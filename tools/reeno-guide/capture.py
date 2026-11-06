#!/usr/bin/env python3
"""Capture actual app views with offline sample state; restore all app source changes."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import struct
import time
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = None
WORK = None
SOURCES = None
OUTPUT = None
APPEARANCE = 'light'
APP = 'import SwiftUI\nimport AppFeature\nimport UIComponent\n@main\nstruct MediaKitApp: App {\n  init() {\n    NSTimeZone.default = TimeZone(identifier: "Asia/Tokyo")!\n    Fonts.register()\n  }\n  var body: some Scene { WindowGroup { GuideCaptureScreen() } }\n}\n'
CLOCK = '\n#if DEBUG\npublic enum MediaKitClock {\n  public static var now: Date {\n    var calendar = Calendar(identifier: .gregorian)\n    calendar.timeZone = TimeZone(identifier: "Asia/Tokyo")!\n    let hour = Int(ProcessInfo.processInfo.environment["REENO_CAPTURE_HOUR"] ?? "7") ?? 7\n    return calendar.date(from: DateComponents(year: 2026, month: 11, day: 6, hour: hour, minute: 30))!\n  }\n}\n#endif\n'
BUNDLE = 'com.koki.osada.reeno.guidecapture'
MODES = {'welcome': 180, 'name': 0, 'profile': 0, 'profile-language': 0, 'profile-level': 0, 'ai-consent': 0, 'microphone': 0,
         'first-call': 0,
         'initial-schedule': 0, 'home-first': 0, 'home': 0, 'home-settings': 500,
         'history': 0, 'history-missed': 0, 'history-detail': 0, 'history-phrases': 450,
         'note-draft': 0, 'call-tab': 0, 'call-settings': 0, 'schedule-windows': 700,
         'schedule-editor': 700, 'microphone-dialog': 0}
CAPTURE_HOUR = 21

def run(*args, **kwargs):
    return subprocess.run(args, check=True, cwd=ROOT, **kwargs)

def build(device):
    originals = {}
    def edit(path, old=None, new='', append=False):
        if path not in originals: originals[path] = path.read_bytes()
        text = path.read_text()
        if append: text += new
        else:
            assert old in text, f'Capture hook changed: {path} / {old}'
            text = text.replace(old, new)
        path.write_text(text)
    def file(relative): return SOURCES / relative
    try:
        app = ROOT / 'src/reeno/App/App.swift'
        edit(app, app.read_text(), APP)
        edit(file('AppFeature/Presentations/Tab/TabScreen.swift'), new=(HERE/'AppScreens.swift').read_text(), append=True)
        background = file('UIComponent/Background/BackgroundView.swift')
        edit(background, new=CLOCK, append=True)
        for relative in ['UIComponent/Background/BackgroundView.swift', 'HomeFeature/Presentations/Root/HomeRootScreen.swift',
                         'CallHistoryFeature/Presentations/Root/CallHistoryRootScreen.swift', 'CallHistoryFeature/Presentations/Detail/CallHistoryDetailScreen.swift',
                         'AppFeature/Presentations/Call/CallTabRootScreen.swift']:
            edit(file(relative), 'context.date', 'MediaKitClock.now')
        edit(file('HomeFeature/Presentations/Root/HomeDashboardMainViews.swift'), 'from: Date()', 'from: MediaKitClock.now')
        debug = file('HomeFeature/Presentations/Root/HomeDashboardDebugScenario.swift')
        edit(debug, 'import Foundation', 'import Foundation\nimport UIComponent')
        edit(debug, 'private let now = Date()', 'private let now = MediaKitClock.now')
        edit(debug, '"Sada"', '"Haru"')
        edit(debug, 'nextCallHint: "昨日話したイタリア料理のお店、行ってみた感想を話してみましょう"', 'nextCallHint: scenario == .settingsIncomplete ? "" : "昨日話したイタリア料理のお店、行ってみた感想を話してみましょう"')
        edit(debug, 'totalAnsweredCallCount: 12', 'totalAnsweredCallCount: scenario == .settingsIncomplete ? 0 : 12')
        edit(debug, 'currentStreakDays: 3', 'currentStreakDays: scenario == .settingsIncomplete ? 0 : 3')
        edit(file('AppFeature/Presentations/Onboarding/ProfileSetupScreen.swift'), '"Sada"', '"Haru"')
        edit(file('AppFeature/Presentations/Onboarding/RegisterNameScreenState.swift'), 'var name = ""', 'var name = "Haru"')
        edit(file('AppFeature/Presentations/Call/CallTabRootScreenState.swift'), 'func onAppear() {', 'func onAppear() { isLoading = false; return;')
        history = file('CallHistoryFeature/Presentations/Root/CallHistoryRootScreen.swift')
        edit(history, new=(HERE/'HistoryFixtures.swift').read_text(), append=True)
        edit(file('CallHistoryFeature/Presentations/Root/CallHistoryRootScreenState.swift'), 'func onAppear() async {', '''func onAppear() async {
    isLoading = false
    callSetting = GuideHistoryFixtures.setting
    let missed = ProcessInfo.processInfo.environment["REENO_GUIDE_SCREEN"] == "history-missed"
    calls = missed ? [GuideHistoryFixtures.call(.missed, offset: -300), GuideHistoryFixtures.call(.declined, offset: -86400), GuideHistoryFixtures.call(.completed, offset: -172800)] : [GuideHistoryFixtures.call(), GuideHistoryFixtures.call(.completed, offset: -86400)]
    return
''')
        detail = file('CallHistoryFeature/Presentations/Detail/CallHistoryDetailScreenState.swift')
        edit(detail, 'self.call = call', 'self.call = call\n    self.summary = GuideHistoryFixtures.summary')
        edit(detail, 'func onAppear() {', 'func onAppear() { return;')
        edit(detail, 'func learningContentBottomAppeared() {', 'func learningContentBottomAppeared() { return;')
        setting = file('CallSettingFeature/Presentations/Detail/CallSettingDetailScreenState.swift')
        edit(setting, 'func onAppear() async {', '''func onAppear() async {
    isLoading = false; callNowPhase = .idle
    for day in Weekday.allCases { weeklyWindows[day] = [.init(id: "guide-window", startMinutes: 1140, endMinutes: 1380)] }
    apply(setting: .init(id: "guide-sample", isEnabled: true, language: .englishUS,
      level: .beginner, voice: .neutral, availableWindows: weeklyWindows,
      timeZoneIdentifier: "Asia/Tokyo", desiredCallCountPerDay: 1, updatedAt: MediaKitClock.now))
    if ProcessInfo.processInfo.environment["REENO_GUIDE_SCREEN"] == "schedule-editor" {
      addWindowTapped(weekday: .monday)
      editingStartTime = Self.time(hour: 12); editingEndTime = Self.time(hour: 13)
    }
    return
''')
        edit(setting, 'availableSnoozeFixedHours(now: .now', 'availableSnoozeFixedHours(now: MediaKitClock.now')
        settingView = file('CallSettingFeature/Presentations/Detail/CallSettingDetailScreen.swift')
        edit(settingView, 'await state.voicePreview.observeCallAudio()', '')
        edit(settingView, 'await state.observeCallNowAvailability()', '')
        with (WORK/'build.log').open('w') as log:
            run('xcodebuild','-project','src/reeno.xcodeproj','-scheme','Develop','-configuration','Debug',
                '-destination',f'platform=iOS Simulator,id={device}','-disableAutomaticPackageResolution',
                'CLANG_ENABLE_EXPLICIT_MODULES=NO','SWIFT_ENABLE_EXPLICIT_MODULES=NO','CODE_SIGNING_ALLOWED=NO',
                f'PRODUCT_BUNDLE_IDENTIFIER={BUNDLE}','build',stdout=log,stderr=subprocess.STDOUT)
    finally:
        for path,data in originals.items(): path.write_bytes(data)
        print('Restored all application sources.',flush=True)

def capture(device, product, modes):
    product_info = plistlib.loads((product/'Info.plist').read_bytes())
    if product_info.get('CFBundleIdentifier') != BUNDLE:
        raise ValueError('Use the offline guide-capture build product; refusing to launch a normal app build.')
    app = WORK/'Capture.app'
    if app.exists(): shutil.rmtree(app)
    shutil.copytree(product,app)
    for path in app.glob('*.bundle/Info.plist'):
        info=plistlib.loads(path.read_bytes());info['CFBundleIdentifier']='guide.resources.'+path.parent.stem.replace('_','-')
        path.write_bytes(plistlib.dumps(info))
    info=plistlib.loads((app/'Info.plist').read_bytes());info['CFBundleDisplayName']='Reeno';(app/'Info.plist').write_bytes(plistlib.dumps(info))
    state=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','-j']))
    info=next(d for ds in state['devices'].values() for d in ds if d['udid']==device)
    booted=info['state']=='Booted'
    output=OUTPUT;output.mkdir(parents=True,exist_ok=True)
    previous_appearance = None
    try:
        if not booted: run('xcrun','simctl','boot',device)
        run('xcrun','simctl','bootstatus',device,'-b')
        previous_appearance = subprocess.check_output(['xcrun','simctl','ui',device,'appearance'], text=True).strip().lower()
        run('xcrun','simctl','ui',device,'appearance',APPEARANCE)
        assert info_plist_style(app) == 'Dark', 'Capture must preserve the app UIUserInterfaceStyle=Dark'
        run('xcrun','simctl','install',device,str(app))
        for mode in modes:
            hour = CAPTURE_HOUR
            run('xcrun','simctl','status_bar',device,'override','--time',f'{hour:02}:30','--dataNetwork','wifi','--wifiMode','active','--wifiBars','3','--batteryState','charged','--batteryLevel','100')
            if mode=='microphone-dialog': run('xcrun','simctl','privacy',device,'reset','microphone',BUNDLE)
            env=os.environ.copy();env.update(SIMCTL_CHILD_REENO_GUIDE_SCREEN=mode,SIMCTL_CHILD_REENO_GUIDE_SCROLL=str(MODES[mode]),SIMCTL_CHILD_REENO_CAPTURE_HOUR=str(hour),SIMCTL_CHILD_REENO_CONVERSATION_LEVEL='4',SIMCTL_CHILD_TZ='Asia/Tokyo')
            run('xcrun','simctl','launch',device,BUNDLE,'-AppleLanguages','(ja)','-AppleLocale','ja_JP',env=env)
            time.sleep(8)
            run('xcrun','simctl','io',device,'screenshot','--mask=alpha',str(output/f'{mode}.png'))
            run('xcrun','simctl','terminate',device,BUNDLE)
    finally:
        if previous_appearance in ('light', 'dark'):
            subprocess.run(['xcrun','simctl','ui',device,'appearance',previous_appearance], check=True)
        subprocess.run(['xcrun','simctl','uninstall',device,BUNDLE],stdout=subprocess.DEVNULL)
        subprocess.run(['xcrun','simctl','status_bar',device,'clear'],stdout=subprocess.DEVNULL)
        if not booted: subprocess.run(['xcrun','simctl','shutdown',device],stdout=subprocess.DEVNULL)
    today = datetime.now(ZoneInfo('Asia/Tokyo')).date().isoformat()
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    record_path = output/'capture.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else {
        'captured_on': today, 'device': info['name'], 'runtime': next(k for k, ds in state['devices'].items() if any(d['udid'] == device for d in ds)), 'locale': 'ja_JP',
        'source_commit': commit,
        'method': 'Actual app screens rendered with offline sample fixtures. Native iOS microphone permission dialog. No user data or backend access. Temporary source changes restored.'}
    previous = {entry['file']: entry for entry in record.get('files', [])}
    record['last_capture_on'] = today
    record['harness_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'capture.py', HERE/'AppScreens.swift', HERE/'HistoryFixtures.swift']}
    record['appearance_policy'] = 'Preserve app Info.plist Dark and each production view colorScheme. No global preferredColorScheme or screenshot-only background replacement.'
    record['files'] = []
    for path in sorted(output.glob('*.png')):
        entry = previous.get(path.name, {'file': path.name})
        entry['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.stem in modes:
            hour = CAPTURE_HOUR
            entry.update(captured_on=today, source_commit=commit, display_time=f'{hour:02}:30',
                         background='app-defined (21:30 for time-dependent screens)', simulator_appearance=APPEARANCE, app_interface_style='Dark', resolution=list(struct.unpack('>II',path.read_bytes()[16:24])))
        record['files'].append(entry)
    (output/'capture.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')

def info_plist_style(app):
    return plistlib.loads((app/'Info.plist').read_bytes()).get('UIUserInterfaceStyle')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--appearance', choices=['light','dark'], default='light')
    parser.add_argument('--device',required=True);parser.add_argument('--product',required=True,type=Path)
    parser.add_argument('--skip-build',action='store_true');parser.add_argument('--only',nargs='+',choices=list(MODES))
    args=parser.parse_args()
    ROOT=args.repo.expanduser().resolve(); SOURCES=ROOT/'src/Sources/Sources'
    WORK=ROOT/'.build/guide-capture'; OUTPUT=args.output.expanduser().resolve(); APPEARANCE=args.appearance
    WORK.mkdir(parents=True,exist_ok=True)
    if not args.skip_build: build(args.device)
    capture(args.device,args.product,args.only or list(MODES))
