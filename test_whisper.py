import os
import whisper
import numpy as np
import urllib.request

def download_file(url, path):
    """ファイルをダウンロードし、進捗状況を表示"""
    try:
        print(f"ダウンロード中: {url}")
        urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        print(f"ダウンロードエラー: {str(e)}")
        return False

def test_whisper_setup():
    print("=== Whisper設定テスト ===")
    
    try:
        # プロジェクトディレクトリの設定
        project_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(project_dir, "models")
        os.makedirs(models_dir, exist_ok=True)
        
        print(f"\nディレクトリ情報:")
        print(f"プロジェクトディレクトリ: {project_dir}")
        print(f"モデルディレクトリ: {models_dir}")
    
        # mel_filters.npzファイルの確認とダウンロード
        mel_filters_path = os.path.join(models_dir, "mel_filters.npz")
        print(f"\nmel_filters.npzの確認:")
        if not os.path.exists(mel_filters_path):
            print("ファイルが見つかりません。ダウンロードを開始します...")
            mel_filters_url = "https://raw.githubusercontent.com/openai/whisper/main/whisper/assets/mel_filters.npz"
            if not download_file(mel_filters_url, mel_filters_path):
                return False
        else:
            print(f"✓ mel_filters.npzが存在します: {mel_filters_path}")
            
        # ファイルサイズの確認
        file_size = os.path.getsize(mel_filters_path)
        print(f"ファイルサイズ: {file_size} bytes")
    
        # 環境変数の設定
        os.environ["XDG_CACHE_HOME"] = models_dir
        print(f"\n環境変数:")
        print(f"XDG_CACHE_HOME = {os.environ.get('XDG_CACHE_HOME')}")
        
        # Whisperのパス設定
        import whisper.audio
        whisper.audio.ASSETS_PATH = models_dir
        print(f"ASSETS_PATH = {whisper.audio.ASSETS_PATH}")
        
        # アセットディレクトリの内容を表示
        print("\nアセットディレクトリの内容:")
        for file in os.listdir(models_dir):
            file_path = os.path.join(models_dir, file)
            size = os.path.getsize(file_path)
            print(f"- {file} ({size} bytes)")
    
        # テスト用の音声データ生成とメルスペクトログラム変換
        print("\nメルスペクトログラム変換テスト:")
        try:
            test_audio = np.zeros(16000, dtype=np.float32)  # 明示的にfloat32を指定
            mel = whisper.audio.log_mel_spectrogram(test_audio)
            print("✓ メルスペクトログラム変換に成功")
            print(f"メルスペクトログラムの形状: {mel.shape}")
        except Exception as e:
            print(f"✗ メルスペクトログラム変換に失敗: {str(e)}")
            print(f"エラーの詳細:")
            traceback.print_exc()
            return False
    
        # モデルのロード
        print("\nWhisperモデルのロード:")
        try:
            model = whisper.load_model("base", download_root=models_dir)
            print("✓ モデルのロードに成功")
            print(f"モデル情報:")
            print(f"- デバイス: {model.device}")
            print(f"- 次元数: {model.dims}")
        except Exception as e:
            print(f"✗ モデルのロードに失敗: {str(e)}")
            print(f"エラーの詳細:")
            traceback.print_exc()
            return False
        
        print("\n=== テスト完了 ===")
        print("すべてのテストに成功しました！")
        return True
        
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {str(e)}")
        print("エラーの詳細:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import traceback
    
    try:
        success = test_whisper_setup()
        if not success:
            print("\nテストに失敗しました。")
            print("エラーログを確認してください。")
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        print("エラーの詳細:")
        traceback.print_exc()
    finally:
        print("\nログの出力が完了しました。")
        input("Enterキーを押して終了...")
