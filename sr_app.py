import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from datetime import datetime
import whisper
import shutil
from PersonalizedSR import transcribe_audio
from train_whisper import save_training_data, train_model
import traceback
import subprocess
import threading
import re

class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("音声認識アプリケーション")
        self.root.geometry("800x600")
        
        # ユーザーデータの保存先
        self.app_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_data')
        self.users_file = os.path.join(self.app_data_dir, 'users.json')
        os.makedirs(self.app_data_dir, exist_ok=True)
        
        # 選択された履歴エントリ
        self.selected_entry = None
        
        # ユーザーデータの読み込み
        self.users = self.load_users()
        
        # UIの作成
        self.create_ui()
        
        try:
            # Whisperモデルの読み込み
            print("Whisperモデルを読み込んでいます...")
            self.model = whisper.load_model("base", device="cpu")
            print("モデルの読み込みが完了しました")
        except Exception as e:
            print(f"モデルの読み込み中にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", f"モデルの読み込み中にエラーが発生しました:\n{str(e)}")

    def load_users(self):
        """ユーザーデータの読み込み"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, dict) or "users" not in data:
                        data = {"users": {}}
                    return data
        except Exception as e:
            print(f"ユーザーデータの読み込み中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", "ユーザーデータの読み込みに失敗しました")
        return {"users": {}}

    def save_users(self):
        """ユーザーデータの保存"""
        try:
            if not isinstance(self.users, dict) or "users" not in self.users:
                self.users = {"users": {}}
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ユーザーデータの保存中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", "ユーザーデータの保存に失敗しました")

    def create_ui(self):
        """UIの作成"""
        try:
            # メインフレーム
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # ユーザー選択部分
            user_frame = ttk.Frame(main_frame)
            user_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E))
            
            ttk.Label(user_frame, text="ユーザー:").grid(row=0, column=0, sticky=tk.W)
            self.user_var = tk.StringVar()
            self.user_combo = ttk.Combobox(user_frame, textvariable=self.user_var)
            self.user_combo['values'] = list(self.users["users"].keys())
            self.user_combo.grid(row=0, column=1, sticky=(tk.W, tk.E))
            
            # 新規ユーザー追加ボタン
            ttk.Button(user_frame, text="新規ユーザー", command=self.add_new_user).grid(row=0, column=2, padx=5)
            
            # 音声ファイル選択ボタン
            ttk.Button(main_frame, text="音声ファイルを選択", command=self.select_file).grid(row=1, column=0, columnspan=3, pady=10)
            
            # 進捗状況表示
            progress_frame = ttk.LabelFrame(main_frame, text="処理状況", padding="5")
            progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
            
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, length=400)
            self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
            
            self.progress_percent = tk.StringVar(value="0%")
            ttk.Label(progress_frame, textvariable=self.progress_percent).grid(row=0, column=2, padx=5)
            
            self.status_var = tk.StringVar(value="待機中")
            self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, wraplength=600)
            self.status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5)
            
            # 履歴表示
            history_frame = ttk.LabelFrame(main_frame, text="処理履歴", padding="5")
            history_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
            
            # 履歴リストボックス
            self.history_listbox = tk.Listbox(history_frame, height=15)
            self.history_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # スクロールバー
            scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            self.history_listbox.configure(yscrollcommand=scrollbar.set)
            
            # ファイルを開くボタン
            button_frame = ttk.Frame(history_frame)
            button_frame.grid(row=1, column=0, columnspan=2, pady=5)
            
            ttk.Button(button_frame, text="音声ファイルを再生", command=self.play_audio).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="テキストファイルを開く", command=self.open_text).grid(row=0, column=1, padx=5)
            ttk.Button(button_frame, text="修正テキストを学習", command=self.learn_corrected_text).grid(row=0, column=2, padx=5)
            
            # ユーザー選択時の処理
            self.user_combo.bind('<<ComboboxSelected>>', self.update_history)
            # 履歴選択時の処理
            self.history_listbox.bind('<<ListboxSelect>>', self.on_select_history)

            # ウィンドウのリサイズ設定
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(1, weight=1)
            main_frame.rowconfigure(3, weight=1)
            history_frame.columnconfigure(0, weight=1)
            history_frame.rowconfigure(0, weight=1)
            user_frame.columnconfigure(1, weight=1)
            progress_frame.columnconfigure(0, weight=1)

        except Exception as e:
            print(f"UIの作成中にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", "UIの作成中にエラーが発生しました")

    def update_progress(self, progress, status):
        """進捗状況の更新"""
        self.progress_var.set(progress)
        self.progress_percent.set(f"{int(progress)}%")
        self.status_var.set(status)
        
        # プログレスバーの色を更新
        if progress == 100:
            self.progress_bar["style"] = "green.Horizontal.TProgressbar"
        elif progress == 0:
            self.progress_bar["style"] = "Horizontal.TProgressbar"
        
        # Whisperの進捗表示を解析
        if "frames/s]" in status:
            match = re.search(r'(\d+)%.*?(\d+\.\d+)frames/s', status)
            if match:
                percent = int(match.group(1))
                fps = float(match.group(2))
                self.progress_var.set(percent)
                self.progress_percent.set(f"{percent}%")
                self.status_var.set(f"音声認識を実行中... ({fps:.1f} frames/s)")
        
        self.root.update_idletasks()

    def process_callback(self, progress, status):
        """処理状況のコールバック"""
        self.root.after(0, lambda: self.update_progress(progress, status))

    def play_audio(self):
        """選択された履歴の音声ファイルを再生"""
        try:
            if not self.selected_entry:
                messagebox.showwarning("警告", "再生する履歴を選択してください")
                return
            
            dataset_dir = self.selected_entry["dataset_dir"]
            audio_files = [f for f in os.listdir(dataset_dir) if f.startswith('audio')]
            if audio_files:
                audio_path = os.path.join(dataset_dir, audio_files[0])
                if os.path.exists(audio_path):
                    os.startfile(audio_path)
                else:
                    messagebox.showerror("エラー", "音声ファイルが見つかりません")
                
        except Exception as e:
            print(f"音声ファイルの再生中にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", "音声ファイルの再生に失敗しました")

    def open_text(self):
        """選択された履歴のテキストファイルを開く"""
        try:
            if not self.selected_entry:
                messagebox.showwarning("警告", "開くテキストファイルを選択してください")
                return
            
            transcript_file = self.selected_entry["transcript_file"]
            if os.path.exists(transcript_file):
                os.startfile(transcript_file)
            else:
                messagebox.showerror("エラー", "テキストファイルが見つかりません")
                
        except Exception as e:
            print(f"テキストファイルを開く際にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", "テキストファイルを開けませんでした")

    def learn_corrected_text(self):
        """修正テキストを学習データとして使用"""
        try:
            if not self.selected_entry:
                messagebox.showwarning("警告", "学習する履歴を選択してください")
                return
            
            # 修正テキストファイルの選択
            corrected_file = filedialog.askopenfilename(
                title="修正したテキストファイルを選択",
                filetypes=[("テキストファイル", "*.txt")]
            )
            
            if corrected_file:
                try:
                    # 修正テキストの読み込み
                    with open(corrected_file, 'r', encoding='utf-8') as f:
                        corrected_text = f.read()
                    
                    # 学習データの保存
                    user = self.user_var.get()
                    date = self.selected_entry["date"]
                    audio_file = self.selected_entry["input_file"]
                    original_text = self.selected_entry["output_text"]
                    dataset_dir = self.selected_entry["dataset_dir"]
                    
                    training_dir = save_training_data(
                        user, date, audio_file, original_text, 
                        corrected_text, dataset_dir
                    )
                    
                    # モデルの学習
                    if train_model(training_dir):
                        messagebox.showinfo("完了", "修正テキストを学習データとして保存しました")
                    else:
                        messagebox.showwarning("警告", "学習データの保存は完了しましたが、モデルの学習は実装されていません")
                    
                except Exception as e:
                    error_msg = f"学習データの処理中にエラーが発生しました:\n{str(e)}"
                    print(error_msg)
                    traceback.print_exc()
                    messagebox.showerror("エラー", error_msg)
                    
        except Exception as e:
            print(f"修正テキストの学習中にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", "修正テキストの学習に失敗しました")

    def on_select_history(self, event):
        """履歴が選択されたときの処理"""
        try:
            selection = self.history_listbox.curselection()
            if selection:
                date = self.history_listbox.get(selection[0])
                user = self.user_var.get()
                
                if user and user in self.users["users"]:
                    for entry in self.users["users"][user]["history"]:
                        if entry["date"] == date:
                            self.selected_entry = entry
                            self.status_var.set(f"選択: {entry['input_file']} ({entry['date']})")
                            break
                            
        except Exception as e:
            print(f"履歴選択時にエラーが発生しました: {str(e)}")
            traceback.print_exc()

    def add_new_user(self):
        """新規ユーザーの追加"""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("新規ユーザー追加")
            dialog.geometry("300x100")
            
            ttk.Label(dialog, text="ユーザー名:").grid(row=0, column=0, padx=5, pady=5)
            name_var = tk.StringVar()
            name_entry = ttk.Entry(dialog, textvariable=name_var)
            name_entry.grid(row=0, column=1, padx=5, pady=5)
            
            def save_user():
                try:
                    name = name_var.get().strip()
                    if name:
                        if name not in self.users["users"]:
                            if not isinstance(self.users, dict):
                                self.users = {"users": {}}
                            if "users" not in self.users:
                                self.users["users"] = {}
                            
                            self.users["users"][name] = {"history": []}
                            self.save_users()
                            self.user_combo['values'] = list(self.users["users"].keys())
                            self.user_combo.set(name)
                            self.update_history(None)
                            dialog.destroy()
                        else:
                            messagebox.showerror("エラー", "このユーザー名は既に存在します")
                    else:
                        messagebox.showerror("エラー", "ユーザー名を入力してください")
                except Exception as e:
                    print(f"ユーザー保存中にエラーが発生しました: {str(e)}")
                    messagebox.showerror("エラー", "ユーザーの保存に失敗しました")
            
            ttk.Button(dialog, text="保存", command=save_user).grid(row=1, column=0, columnspan=2, pady=10)
            
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.focus_set()
            
        except Exception as e:
            print(f"ユーザー追加ダイアログの作成中にエラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", "ユーザー追加ダイアログの作成に失敗しました")

    def select_file(self):
        """音声ファイルの選択と処理"""
        try:
            user = self.user_var.get()
            if not user:
                messagebox.showerror("エラー", "ユーザーを選択してください")
                return
            
            if not isinstance(self.users, dict):
                self.users = {"users": {}}
            if "users" not in self.users:
                self.users["users"] = {}
            if user not in self.users["users"]:
                self.users["users"][user] = {"history": []}
            elif "history" not in self.users["users"][user]:
                self.users["users"][user]["history"] = []
                
            file_path = filedialog.askopenfilename(
                title="音声ファイルを選択",
                filetypes=[
                    ("音声ファイル", "*.wav;*.mp3;*.m4a"),
                    ("WAVファイル", "*.wav"),
                    ("MP3ファイル", "*.mp3"),
                    ("M4Aファイル", "*.m4a"),
                    ("すべてのファイル", "*.*")
                ]
            )
            
            if file_path:
                def process_audio():
                    try:
                        self.update_progress(0, "音声認識を開始します...")
                        print(f"音声ファイルを処理中: {file_path}")
                        
                        # 音声認識の実行
                        result = transcribe_audio(file_path, progress_callback=self.process_callback)
                        
                        # 結果の保存
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        history_entry = {
                            "date": timestamp,
                            "input_file": os.path.basename(file_path),
                            "output_text": result[0],  # 認識されたテキスト
                            "transcript_file": result[1],  # 転記ファイルのパス
                            "dataset_dir": result[2]  # データセットディレクトリのパス
                        }
                        
                        self.users["users"][user]["history"].append(history_entry)
                        self.save_users()
                        
                        # UI更新
                        self.root.after(0, lambda: self.update_progress(100, "処理が完了しました"))
                        self.root.after(0, lambda: self.update_history(None))
                        self.root.after(0, lambda: messagebox.showinfo("完了", "音声認識が完了しました"))
                        
                    except Exception as e:
                        error_msg = f"処理中にエラーが発生しました:\n{str(e)}"
                        print(error_msg)
                        traceback.print_exc()
                        self.root.after(0, lambda: self.update_progress(0, "エラーが発生しました"))
                        self.root.after(0, lambda: messagebox.showerror("エラー", error_msg))
                
                # 処理を別スレッドで実行
                thread = threading.Thread(target=process_audio)
                thread.daemon = True
                thread.start()
                    
        except Exception as e:
            print(f"ファイル選択中にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", "ファイル選択中にエラーが発生しました")

    def update_history(self, event):
        """履歴の更新"""
        try:
            user = self.user_var.get()
            
            # リストボックスをクリア
            self.history_listbox.delete(0, tk.END)
            
            if user and user in self.users["users"]:
                if "history" in self.users["users"][user]:
                    # 履歴を新しい順に表示（日付のみ）
                    for entry in reversed(self.users["users"][user]["history"]):
                        self.history_listbox.insert(tk.END, entry["date"])
                    
        except Exception as e:
            print(f"履歴の更新中にエラーが発生しました: {str(e)}")
            traceback.print_exc()
            messagebox.showerror("エラー", "履歴の更新中にエラーが発生しました")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        # プログレスバーのスタイル設定
        style = ttk.Style()
        style.configure("Horizontal.TProgressbar", background='blue')
        style.configure("green.Horizontal.TProgressbar", background='green')
        
        app = SpeechRecognitionApp(root)
        root.mainloop()
    except Exception as e:
        print(f"アプリケーションの起動中にエラーが発生しました: {str(e)}")
        traceback.print_exc()
