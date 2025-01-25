# Personalized Speech Recognition with Whisper

日本語音声の文字起こしと翻訳を行うためのカスタマイズ可能な音声認識システム。OpenAIのWhisperモデルを使用して、特定の話者の音声に特化した高精度な文字起こしを実現します。

## 機能

- 音声ファイル（WAV/MP3）からの文字起こし
- タイムスタンプ付きの文字起こし結果
- 文字起こし履歴の保存と管理
- 日本語音声認識に最適化
- GUIインターフェース
- 音声録音機能

## 必要条件

- Python 3.9以上
- pip（Pythonパッケージマネージャー）
- Windows 10/11（デスクトップアプリケーション用）

## インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/nori1021/Personalized-Speech-Recognition.git
cd Personalized-Speech-Recognition
```

2. 必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

3. デスクトップアプリケーションのビルド（オプション）:
```bash
python build_app.py
```

## 使用方法

### GUIアプリケーションの起動

```bash
python sr_app.py
```

### 音声録音と文字起こし

1. 「録音開始」ボタンをクリックして音声を録音
2. 「録音停止」ボタンをクリックして録音を終了
3. 「文字起こし開始」ボタンをクリック
4. 結果が表示されたら、必要に応じて「結果を保存」ボタンをクリック

### 既存の音声ファイルの文字起こし

1. 「参照」ボタンをクリックして音声ファイルを選択
2. 「文字起こし開始」ボタンをクリック
3. 結果が表示されたら、必要に応じて「結果を保存」ボタンをクリック

## プロジェクト構成

```
.
├── PersonalizedSR.py      # Whisper音声認識モジュール
├── sr_app.py             # GUIアプリケーション
├── train_whisper.py      # モデル学習用モジュール
├── record_audio.py       # 音声録音モジュール
├── setup.py             # パッケージセットアップ
├── build_app.py         # デスクトップアプリビルド
├── requirements.txt     # 依存パッケージリスト
├── icon_desktop.png     # アプリケーションアイコン
├── app_data/           # アプリケーションデータ
│   └── users.json      # ユーザー設定
├── dataset/            # 学習用データセット（自動生成）
├── recordings/         # 録音ファイル保存ディレクトリ（自動生成）
└── transcripts/        # 文字起こし結果保存ディレクトリ（自動生成）
```

## 開発ロードマップ

1. [x] 基本的な音声ファイル文字起こし機能
2. [x] タイムスタンプ付きセグメント出力
3. [x] GUIアプリケーションインターフェース
4. [x] 音声録音機能
5. [x] デスクトップアプリケーションビルド
6. [ ] 特定の話者の音声データセット作成機能
7. [ ] 学習データの管理システム
8. [ ] モデルの再学習機能
9. [ ] 英語への翻訳機能
10. [ ] リアルタイム字幕生成機能

## 技術仕様

- **音声認識**: OpenAI Whisper
- **GUI**: tkinter
- **対応音声形式**: WAV, MP3, M4A
- **出力形式**: テキスト（.txt）, JSON（履歴）
- **デスクトップアプリ**: PyInstaller

## 注意事項

- 大きな音声ファイルの処理には時間がかかる場合があります
- 文字起こしの精度は音声の品質に依存します
- 初回起動時にWhisperモデルのダウンロードが行われます（約1GB）
- デスクトップアプリケーションは現在Windowsのみ対応

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 謝辞

- [OpenAI Whisper](https://github.com/openai/whisper)
