#!/usr/bin/env python3
"""Capture the native Reeno connecting ripples without modifying the iOS checkout."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import signal
import subprocess
import tempfile
import time
from zoneinfo import ZoneInfo

BUNDLE = 'com.koki.osada.reeno.promorings'
HERE = Path(__file__).resolve().parent
SCREEN = 'AppFeature/Presentations/Call/InProgress/CallInProgressScreen.swift'
RINGTONE = '/System/Library/PrivateFrameworks/ToneLibrary.framework/Versions/A/Resources/Ringtones/Reflection.m4r'


def run(*args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, **kwargs)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(repo, work):
    sources = repo / 'src/Sources/Sources'
    ui = sources / 'UIComponent'
    app = work / 'Promo.app'
    app.mkdir()
    # Compile the real asset catalog and native UI sources into an offline app.
    run('xcrun', 'actool', ui/'Resources/Media.xcassets', '--compile', app,
        '--platform', 'iphonesimulator', '--minimum-deployment-target', '26.0',
        '--target-device', 'iphone', '--generate-swift-asset-symbols', work/'Assets.swift',
        '--generate-swift-asset-symbol-extensions', 'NO', '--bundle-identifier', BUNDLE)
    run('xcrun', 'actool', ui/'Resources/Media.xcassets', '--compile', app,
        '--platform', 'iphonesimulator', '--minimum-deployment-target', '26.0',
        '--target-device', 'iphone')
    for font in (ui/'Resources/Font').glob('*.ttf'):
        shutil.copy2(font, app/font.name)
    inputs = [sources/SCREEN]
    for relative in ['View/ReenoCharacterView.swift', 'Font/Font+.swift',
                     'Extensions/Image+.swift', 'Extensions/Color+.swift',
                     'Background/AppBackgroundImagePalette.swift',
                     'Background/AppBackgroundTimeSlot.swift']:
        original = ui / relative
        inputs.append(original)
        # Previews are Xcode-only; the runtime view implementation is unchanged.
        (work/original.name).write_text(original.read_text().split('#Preview(')[0])
    screen = (sources/SCREEN).read_text()
    character = screen[screen.index('private struct CallCharacterView:'):screen.index('// MARK: - Preview')]
    # Match the established promotional layout's size, retaining native ripple code.
    character = character.replace('.frame(maxWidth: 260)', '.frame(maxWidth: 330)')
    character = character.replace('.padding(.horizontal, 48)', '.padding(.horizontal, 24)')
    layout = (HERE/'CallContent.swift').read_text()
    (work/'Promo.swift').write_text('''import SwiftUI
extension Bundle { static let module = Bundle.main }
enum CallPresentationPhase { case connecting, inConversation, finishing }
@main struct PromoApp: App {
  init() { Fonts.register() }
  var body: some Scene {
    WindowGroup { PromoScreen().preferredColorScheme(.dark) }
  }
}
struct PromoScreen: View {
  var body: some View {
    content()
      .frame(maxWidth: .infinity, maxHeight: .infinity)
      .background {
        AppBackgroundImagePalette.background(
          for: ProcessInfo.processInfo.environment["REENO_PROMO_SKY"] == "daytime" ? .daytime : .night,
          overlayOpacity: 0.08
        ).overlay {
          LinearGradient(colors: [.black.opacity(0.24), .clear, .black.opacity(0.12)],
                         startPoint: .top, endPoint: .bottom)
        }.ignoresSafeArea()
      }
  }
''' + layout + '\n}\n' + character)
    sdk = subprocess.check_output(['xcrun', '--sdk', 'iphonesimulator', '--show-sdk-path'], text=True).strip()
    run('xcrun', 'swiftc', '-sdk', sdk, '-target', 'arm64-apple-ios26.0-simulator',
        '-module-cache-path', work/'module-cache', '-parse-as-library',
        *sorted(work.glob('*.swift')), '-o', app/'Promo')
    (app/'Info.plist').write_bytes(plistlib.dumps({
        'CFBundleIdentifier': BUNDLE, 'CFBundleExecutable': 'Promo',
        'CFBundleName': 'Reeno Promo', 'CFBundlePackageType': 'APPL',
        'CFBundleVersion': '1', 'CFBundleShortVersionString': '1.0',
        'MinimumOSVersion': '26.0', 'UIDeviceFamily': [1],
        'UILaunchScreen': {}, 'UISupportedInterfaceOrientations': ['UIInterfaceOrientationPortrait'],
    }))
    run('codesign', '--force', '--sign', '-', app)
    return app, {str(p.relative_to(repo)): sha(p) for p in inputs}


def capture(args):
    args.output.mkdir(parents=True, exist_ok=True)
    devices = json.loads(subprocess.check_output(['xcrun', 'simctl', 'list', 'devices', '-j']))
    runtime, device = next((r, d) for r, ds in devices['devices'].items() for d in ds if d['udid'] == args.device)
    booted = device['state'] == 'Booted'
    files = []
    with tempfile.TemporaryDirectory(prefix='reeno-promo-') as tmp:
        work = Path(tmp)
        app, hashes = build(args.repo, work)
        try:
            if not booted:
                run('xcrun', 'simctl', 'boot', args.device)
            run('xcrun', 'simctl', 'bootstatus', args.device, '-b')
            run('xcrun', 'simctl', 'install', args.device, app)
            for sky, clock in [('night', '21:40'), ('daytime', '12:40')]:
                run('xcrun', 'simctl', 'status_bar', args.device, 'override', '--time', clock,
                    '--dataNetwork', 'wifi', '--wifiMode', 'active', '--wifiBars', '3',
                    '--operatorName', '', '--batteryState', 'charged', '--batteryLevel', '100')
                env = os.environ | {'SIMCTL_CHILD_REENO_PROMO_SKY': sky, 'SIMCTL_CHILD_REENO_PROMO_ANIMATES': '1'}
                run('xcrun', 'simctl', 'launch', args.device, BUNDLE,
                    '-AppleLanguages', '(ja)', '-AppleLocale', 'ja_JP', env=env)
                time.sleep(4)
                raw = work/f'{sky}.mp4'
                log = work/f'{sky}.log'
                with log.open('w') as output:
                    recording = subprocess.Popen(['xcrun', 'simctl', 'io', args.device, 'recordVideo',
                        '--codec=h264', '--mask=ignored', str(raw)], stdout=output, stderr=output)
                    try:
                        deadline = time.monotonic() + 30
                        while 'Recording started' not in log.read_text():
                            if recording.poll() is not None or time.monotonic() > deadline:
                                raise RuntimeError(log.read_text())
                            time.sleep(0.2)
                        time.sleep(10)
                    finally:
                        if recording.poll() is None:
                            recording.send_signal(signal.SIGINT)
                        try:
                            recording.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            recording.kill()
                            recording.wait()
                            raise
                    if recording.returncode:
                        raise RuntimeError(log.read_text())
                run('xcrun', 'simctl', 'terminate', args.device, BUNDLE)
                probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(raw)]))
                video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
                duration = float(probe['format']['duration'])
                target = args.output/f'reeno-incoming-promo-{sky}.mp4'
                # Finite repeats cover recording startup jitter without FFmpeg's infinite-loop EOF hang.
                run('ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', raw, '-stream_loop', '2', '-i', args.ringtone,
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-af', f'afade=t=out:st={duration - 0.2}:d=0.2', '-t', duration,
                    '-movflags', '+faststart', target)
                files.append({'file': target.name, 'sha256': sha(target), 'duration_seconds': duration,
                    'resolution': [video['width'], video['height']], 'video_codec': video['codec_name'],
                    'audio_codec': 'aac', 'clock': clock, 'bytes': target.stat().st_size})
        finally:
            subprocess.run(['xcrun', 'simctl', 'uninstall', args.device, BUNDLE])
            subprocess.run(['xcrun', 'simctl', 'status_bar', args.device, 'clear'])
            if not booted:
                subprocess.run(['xcrun', 'simctl', 'shutdown', args.device])
    record = {
        'captured_on': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
        'app_source_commit': subprocess.check_output(['git', '-C', str(args.repo), 'rev-parse', 'HEAD'], text=True).strip(),
        'native_source_sha256': hashes, 'layout_sha256': sha(HERE/'CallContent.swift'),
        'device': device['name'], 'runtime': runtime, 'locale': 'ja_JP',
        'method': 'Native SwiftUI CallCharacterView in connecting phase and unmodified ConnectingRippleView, compiled with native character/background/font/color sources and assets in an isolated offline capture app. Direct simctl recording; H.264 video stream copied unchanged when adding Reflection AAC audio.',
        'ringtone_sha256': sha(args.ringtone),
        'app_checkout_modified': False,
        'intended_use': 'Promotional illustration; not the actual incoming-call screen.',
        'files': files,
    }
    (args.output/'video-capture.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--device', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ringtone', type=Path, default=Path(RINGTONE))
    capture(parser.parse_args())
