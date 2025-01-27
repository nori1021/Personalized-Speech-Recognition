import os
import sys
import whisper
import numpy as np
import urllib.request
import json

def download_mel_filters():
    """mel_filters.npzファイルをダウンロードして保存"""
    app_dir = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), 'WhisperSR'))
    assets_dir = os.path.join(app_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    mel_filters_path = os.path.join(assets_dir, "mel_filters.npz")
    
    if not os.path.exists(mel_filters_path):
        print("mel_filters.npzファイルをダウンロード中...")
        
        # メルフィルタバンクの生成
        mel_filters = whisper.audio.log_mel_spectrogram(np.zeros(16000))
        
        # NPZファイルとして保存
        np.savez(mel_filters_path, mel_filters)
        print(f"mel_filters.npzを保存しました: {mel_filters_path}")
    else:
        print("mel_filters.npzは既に存在します")

def download_model():
    """Whisperのベースモデルをダウンロード"""
    app_dir = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), 'WhisperSR'))
    models_dir = os.path.join(app_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # 環境変数の設定
    os.environ["XDG_CACHE_HOME"] = app_dir
    os.environ["WHISPER_HOME"] = app_dir
    
    print("Whisperモデルをダウンロード中...")
    try:
        model = whisper.load_model("base", download_root=models_dir)
        print("モデルのダウンロードが完了しました")
    except Exception as e:
        print(f"モデルのダウンロードに失敗しました: {str(e)}")
        raise

def main():
    try:
        print("=== Whisper初期設定 ===")
        download_mel_filters()
        download_model()
        print("\n初期設定が完了しました！")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        input("\nEnterキーを押して終了...")
        sys.exit(1)

if __name__ == "__main__":
    main()
