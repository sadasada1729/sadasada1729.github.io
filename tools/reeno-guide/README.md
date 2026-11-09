# Reeno 利用ガイドのスクリーンショット

`capture.py` は `call-ai` の現在の SwiftUI 画面を、オフラインのサンプルデータでビルドして撮影します。Firebase の初期化・実通話・実ユーザーデータは使いません。

## 撮影

Apple Silicon Mac、Xcode、iOS 26 以降の Simulator、Python 3 が必要です。画像の操作位置は iPhone 17 Pro Max（1320 × 2868、iOS 26.5）に合わせています。

アプリ側のビルド・編集を止めてから実行してください。撮影用のエントリーポイント、日時、サンプル状態を一時的に `call-ai` に差し込み、ビルド成功・失敗のどちらでも `finally` で元のバイト列へ戻します。強制終了（SIGKILL）をしないでください。通常のアプリとは別の bundle ID を使います。

```sh
xcrun simctl list devices available
python3 tools/reeno-guide/capture.py \
  --repo /path/to/call-ai \
  --device <iPhone-17-Pro-Max-UDID> \
  --product /path/to/DerivedData/reeno-.../Build/Products/Debug-iphonesimulator/Develop.app \
  --output /tmp/reeno-guide-light \
  --appearance light
```

同じビルドで端末のダーク設定も確認できます。

```sh
python3 tools/reeno-guide/capture.py \
  --repo /path/to/call-ai \
  --device <iPhone-17-Pro-Max-UDID> \
  --product /path/to/DerivedData/reeno-.../Build/Products/Debug-iphonesimulator/Develop.app \
  --output /tmp/reeno-guide-dark \
  --appearance dark --skip-build
```

`--only home profile note-draft` のように対象を絞ることもできます。`--skip-build` は同じソース・撮影用コードで作ったビルドに限って使ってください。撮影前の Simulator の外観設定を復元し、このツールが起動した端末は終了します。ステータスバーの撮影用設定は終了時に解除します。

## 配色の扱い

- アプリの Info.plist の `UIUserInterfaceStyle = Dark` を維持し、撮影前に検証します。Simulator がライトでもアプリのウィンドウはダークです。
- 撮影ルートに `preferredColorScheme` を付けません。
- 初回設定の外枠は `OnboardingScreen` の `Image.backgroundLight` と同じ構成です。呼び名など、その画面で指定されている子 View だけに `.environment(\.colorScheme, .light)` を適用します。紹介・AI同意には強制ライトを付けません。
- ホーム・履歴・通話設定は実装内の配色をそのまま使います。時間帯依存の背景のみ、サンプル日時とステータスバーを21:30に揃えます。
- ノート追加の Form は本来の背景を使います。撮影専用の夜空へ差し替えません。
- `AppScreens.swift` の外枠・タブと `HistoryFixtures.swift` のサンプルは撮影専用です。機能の改修時は実装との差分を確認してください。

## 掲載前の確認

1. 両方の外観設定で画像を開き、アプリの明暗・文字・背景が一致することを確認します（キャラクターのアニメーションによる位置差はあり得ます）。iOS標準のマイク許可ダイアログは端末設定に従うため、明暗が変わるのが正常です。掲載画像はライト設定の例です。
2. 掲載する PNG と `capture.json` を `Reeno/app/jp/images/guide/screenshots/` へコピーします。
3. `guide.html` の説明・代替テキスト・赤茶色の操作枠を新しい画像に合わせます。
4. ローカル画像リンク、縦横サイズ、操作番号と説明の対応、モバイル幅での表示を確認します。

`capture.json` にはアプリのソースコミット、撮影環境、端末の外観設定、画像のSHA-256を記録します。着信画面の2枚は別途用意された実機の表示例で、このツールの撮影対象には含みません。

## ウィジェットの表示例

`widget-notes.png` は、アプリの `NoteWidgetView` をオフラインのサンプルで描画した画像です。ホーム画面全体のスクリーンショットではなく、ガイドでも「描画したサンプル」と明記しています。既存のSimulator上の `ImageRenderer` 出力を使用し、元のコミット・ソースと描画コードのハッシュ・サイズ・画像ハッシュを同じ画像ディレクトリの `widget-capture.json` に記録しています。

Widget用の `containerBackground` は同じ背景Viewの通常の背景に置き換えて描画しています。WidgetKitによる色合いの変換や、ホーム画面上のボタン動作を検証した画像ではありません。前後の矢印はアプリ側の `plan/308-widget-previous-phrase` の実装に対応しています。公開時にはアプリの提供版と説明・画像が一致していることを確認してください。この画像は `capture.py` の生成対象には含みません。
