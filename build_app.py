import os
import sys
import shutil
from pathlib import Path
import subprocess
import traceback

def create_desktop_shortcut(exe_path, shortcut_name):
    """デスクトップにショートカットを作成"""
    try:
        import winshell
        from win32com.client import Dispatch

        desktop = Path(winshell.desktop())
        shortcut_path = desktop / f"{shortcut_name}.lnk"
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(exe_path)
        shortcut.WorkingDirectory = str(exe_path.parent)
        shortcut.save()
        return True
    except Exception as e:
        print(f"ショートカットの作成中にエラーが発生しました: {str(e)}")
        print(traceback.format_exc())
        return False

def copy_project_files(target_dir):
    """プロジェクトファイルをビルドディレクトリにコピー"""
    try:
        src_dir = Path(r"C:\Project\PersonalizedSR\Personalized-Speech-Recognition-with-Wisper")
        build_dir = target_dir / "build_temp"
        
        print(f"ソースディレクトリ: {src_dir}")
        print(f"ビルドディレクトリ: {build_dir}")
        
        # ビルドディレクトリをクリーンアップ
        if build_dir.exists():
            shutil.rmtree(build_dir)
        os.makedirs(build_dir)
        
        # 必要なファイルをコピー
        required_files = ["sr_app.py", "PersonalizedSR.py", "train_whisper.py"]
        for file in required_files:
            src_path = src_dir / file
            if not src_path.exists():
                print(f"エラー: {file} が見つかりません: {src_path}")
                return False
            print(f"コピー中: {file}")
            shutil.copy2(src_path, build_dir)
            print(f"コピー完了: {build_dir / file}")
        return build_dir
    except Exception as e:
        print(f"ファイルのコピー中にエラーが発生しました: {str(e)}")
        print(traceback.format_exc())
        return False

def main():
    print("アプリケーションのビルドを開始します...")
    
    # 作業ディレクトリを設定
    work_dir = Path(r"C:\Project\PersonalizedSR\Personalized-Speech-Recognition-with-Wisper")
    os.chdir(work_dir)
    print(f"作業ディレクトリを変更: {work_dir}")
    
    # ビルドディレクトリを作成
    build_dir = copy_project_files(work_dir)
    if not build_dir:
        print("ファイルのコピーに失敗しました。")
        return

    print("PyInstallerでexeファイルを作成しています...")
    try:
        # 既存のビルドファイルをクリーンアップ
        spec_file = work_dir / "WhisperSR.spec"
        if spec_file.exists():
            os.remove(spec_file)
        
        build_path = work_dir / "build"
        if build_path.exists():
            shutil.rmtree(build_path)
        
        dist_path = work_dir / "dist"
        if dist_path.exists():
            shutil.rmtree(dist_path)

        # PyInstallerコマンドを文字列として構築
        cmd_str = (
            f'pyinstaller --onefile --windowed --name=WhisperSR '
            f'--hidden-import=whisper --hidden-import=numpy --hidden-import=torch '
            f'--hidden-import=tkinter --hidden-import=tkinter.ttk '
            f'--hidden-import=tkinter.filedialog --hidden-import=tkinter.messagebox '
            f'--hidden-import=train_whisper '
            f'--add-data="{build_dir}/PersonalizedSR.py;." '
            f'--add-data="{build_dir}/train_whisper.py;." '
            f'--log-level=DEBUG --clean "{build_dir}/sr_app.py"'
        )
        
        print(f"実行するコマンド: {cmd_str}")
        
        # PyInstallerを実行
        process = subprocess.run(
            cmd_str,
            capture_output=True,
            text=True,
            shell=True
        )
        
        # 出力を表示
        print("\nビルドプロセスの出力:")
        if process.stdout:
            print(process.stdout)
        
        if process.returncode != 0:
            print("\nビルド中にエラーが発生しました:")
            if process.stderr:
                print(process.stderr)
            return
        
        # 生成されたexeファイルのパス
        exe_path = work_dir / "dist" / "WhisperSR.exe"
        
        if exe_path.exists():
            print("\nデスクトップにショートカットを作成しています...")
            if create_desktop_shortcut(exe_path, "WhisperSR"):
                print("\nアプリケーションが正常に作成されました！")
                print(f"実行ファイル: {exe_path}")
                print("デスクトップにショートカットが作成されました。")
                print("\n使用方法:")
                print("1. デスクトップの「WhisperSR」アイコンをダブルクリック")
                print("2. 「参照」ボタンをクリックして音声ファイルを選択")
                print("3. 「文字起こし開始」ボタンをクリック")
        else:
            print("\nエラー: exeファイルが生成されませんでした。")
            print(f"期待されたパス: {exe_path}")
            
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
