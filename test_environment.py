import os
import sys
import traceback

def check_environment():
    print("=== 環境チェックを開始 ===")
    
    # Pythonバージョンの確認
    print(f"\nPythonバージョン: {sys.version}")
    
    # 作業ディレクトリの確認
    print(f"\n現在の作業ディレクトリ: {os.getcwd()}")
    
    # 必要なライブラリの確認
    print("\n必要なライブラリの確認:")
    required_libs = [
        ('numpy', 'numpy'),
        ('torch', 'torch'),
        ('torchaudio', 'torchaudio'),
        ('tkinter', 'tkinter'),
        ('tqdm', 'tqdm'),
        ('openai-whisper', 'whisper')
    ]
    
    for package_name, import_name in required_libs:
        try:
            if import_name == 'tkinter':
                import tkinter
                print(f"✓ {package_name} - バージョン: {tkinter.TkVersion}")
            elif import_name == 'whisper':
                import whisper
                print(f"✓ {package_name} - インストール済み")
                # Whisperモデルのキャッシュディレクトリをチェック
                try:
                    app_dir = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), 'WhisperSR'))
                    models_dir = os.path.join(app_dir, "models")
                    model = whisper.load_model("base", download_root=models_dir)
                    print(f"  ✓ Whisperモデル(base)のロードに成功")
                except Exception as e:
                    print(f"  ✗ Whisperモデルのロードに失敗: {str(e)}")
            else:
                module = __import__(import_name)
                print(f"✓ {package_name} - バージョン: {getattr(module, '__version__', 'unknown')}")
        except ImportError as e:
            print(f"✗ {package_name} ({import_name}) - エラー: {str(e)}")
    
    # アプリケーションディレクトリの確認
    print("\nアプリケーションディレクトリの確認:")
    app_dir = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), 'WhisperSR'))
    required_dirs = [
        'models',
        'assets',
        'temp',
        'transcripts',
        'dataset',
        'annotations',
        'finetuned_models'
    ]
    
    for dir_name in required_dirs:
        dir_path = os.path.join(app_dir, dir_name)
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ {dir_name} ディレクトリを確認しました: {dir_path}")
        except Exception as e:
            print(f"✗ {dir_name} ディレクトリの作成に失敗: {str(e)}")
    
    # 環境変数の設定
    os.environ["TEMP"] = os.path.join(app_dir, "temp")
    os.environ["TMP"] = os.path.join(app_dir, "temp")
    os.environ["XDG_CACHE_HOME"] = app_dir
    os.environ["WHISPER_HOME"] = app_dir
    
    print(f"\n環境変数の設定:")
    print(f"TEMP = {os.environ.get('TEMP')}")
    print(f"TMP = {os.environ.get('TMP')}")
    print(f"XDG_CACHE_HOME = {os.environ.get('XDG_CACHE_HOME')}")
    print(f"WHISPER_HOME = {os.environ.get('WHISPER_HOME')}")
    
    print("\n=== 環境チェック完了 ===")

if __name__ == "__main__":
    try:
        check_environment()
        input("\nEnterキーを押して終了...")
    except Exception as e:
        print(f"\nエラーが発生しました:")
        traceback.print_exc()
        input("\nEnterキーを押して終了...")
