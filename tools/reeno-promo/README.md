# Reeno の紹介用動画の再撮影

`capture.py` は `call-ai` の SwiftUI ソースとアセットを読み、専用のオフライン撮影アプリを一時ディレクトリにビルドする。元の iOS リポジトリには書き込まない。実際の通話やバックエンド接続は行わない。

`CallContent.swift` は既存の紹介用レイアウトを基に、`CallCharacterView` の phase を `.connecting` に変更し、固定の装飾円を取り除いたもの。`CallCharacterView` と `ConnectingRippleView` は実行時にアプリの `CallInProgressScreen.swift` から取り込む。キャラクターのサイズと余白だけを既存の紹介用レイアウトに合わせ、波紋の色・線幅・拡大率・フェード・タイミングはアプリの実装をそのまま使う。

Apple Silicon Mac、Xcode（iOS 26 以降）、iOS Simulator、Python 3、ffmpeg / ffprobe が必要。

```sh
xcrun simctl list devices available
python3 tools/reeno-promo/capture.py \
  --repo /path/to/call-ai \
  --device <iPhone-17-Pro-Simulator-UDID> \
  --output /tmp/reeno-promo-output
```

夜空・青空を約10秒ずつ録画し、Reflection の着信音を AAC で付ける。映像は H.264 のままコピーし、再エンコードしない。撮影環境・読み込んだソースのハッシュ・出力の仕様は `video-capture.json` に記録する。

出力を確認したら、2本の MP4 と記録を `Reeno/app/jp/media-kit/09-incoming-promo/` にコピーし、`assets.html` のダウンロード容量表示を更新する。PNG は静止画として別途管理する。
