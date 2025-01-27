import os
import sys
import winshell
from win32com.client import Dispatch

def create_shortcut():
    try:
        # プロジェクトのパスを取得
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # OneDriveデスクトップのパスを取得
        desktop = r"C:\Users\noriy\OneDrive\デスクトップ"
        
        # ショートカットのパス
        shortcut_path = os.path.join(desktop, "音声認識アプリ.lnk")
        
        # バッチファイルのパス
        batch_path = os.path.join(project_dir, "run_app.bat")
        
        # ショートカットを作成
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = batch_path
        shortcut.WorkingDirectory = project_dir
        shortcut.IconLocation = sys.executable  # Pythonのアイコンを使用
        shortcut.save()
        
        print(f"デスクトップにショートカットを作成しました: {shortcut_path}")
        return True
        
    except Exception as e:
        print(f"ショートカットの作成に失敗しました: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        create_shortcut()
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    finally:
        input("Enterキーを押して終了...")
