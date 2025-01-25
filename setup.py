import os

# 必要なディレクトリを作成
os.makedirs('transcriptions', exist_ok=True)

print("""
=== Whisper音声認識システムセットアップ ===

セットアップが完了しました。以下の手順でアプリケーションを使用できます：

1. 必要なパッケージのインストール:
   pip install openai-whisper numpy scipy

2. アプリケーションの起動:
   cd C:\Project
   python sr_app.py

使用可能な音声ファイル形式:
- WAV
- MP3

注意：初回起動時にWhisperモデルのダウンロードが行われます。
""")
