
# Personalized Speech Recognition with Whisper

日本語音声の文字起こしと翻訳を行うためのカスタマイズ可能な音声認識システム。OpenAIのWhisperモデルを使用して、特定の話者の音声に特化した高精度な文字起こしを実現します。

## 機能

- 音声ファイル（WAV/MP3）からの文字起こし
- タイムスタンプ付きの文字起こし結果
- 文字起こし履歴の保存と管理
- 日本語音声認識に最適化
- GUIインターフェース

## 必要条件

- Python 3.9以上
- pip（Pythonパッケージマネージャー）

## インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/[username]/Personalized-Speech-Recognition-with-Whisper.git
cd Personalized-Speech-Recognition-with-Whisper
```

2. 必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

## 使用方法

### GUIアプリケーションの起動

```bash
python sr_app.py
```

### 音声ファイルの文字起こし

1. 「参照」ボタンをクリックして音声ファイルを選択
2. 「文字起こし開始」ボタンをクリック
3. 結果が表示されたら、必要に応じて「結果を保存」ボタンをクリック

## プロジェクト構成

```
.
├── PersonalizedSR.py      # Whisper音声認識モジュール
├── sr_app.py             # GUIアプリケーション
├── train_whisper.py      # モデル学習用モジュール
├── recordings/           # 録音ファイル保存ディレクトリ
└── transcriptions/       # 文字起こし結果保存ディレクトリ
```

## 開発ロードマップ

1. [x] 基本的な音声ファイル文字起こし機能
2. [x] タイムスタンプ付きセグメント出力
3. [x] GUIアプリケーションインターフェース
4. [ ] 特定の話者の音声データセット作成機能
5. [ ] 学習データの管理システム
6. [ ] モデルの再学習機能
7. [ ] 英語への翻訳機能
8. [ ] リアルタイム字幕生成機能

## 技術仕様

- **音声認識**: OpenAI Whisper
- **GUI**: tkinter
- **対応音声形式**: WAV, MP3
- **出力形式**: テキスト（.txt）, JSON（履歴）

## 注意事項

- 大きな音声ファイルの処理には時間がかかる場合があります
- 文字起こしの精度は音声の品質に依存します
- 初回起動時にWhisperモデルのダウンロードが行われます

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
=======

