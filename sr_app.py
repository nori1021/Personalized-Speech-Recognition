import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
from PersonalizedSR import transcribe_audio, fine_tune_model, DATASET_DIR, FINETUNED_DIR
import os
import sys
import json
import shutil
from datetime import datetime
import pygame

class UserManager:
    def __init__(self):
        self.users_dir = os.path.join(DATASET_DIR, "users")
        os.makedirs(self.users_dir, exist_ok=True)
        self.current_user = None
        self.load_users()

    def load_users(self):
        """ユーザー一覧を読み込む"""
        self.users = []
        if os.path.exists(self.users_dir):
            for user_dir in os.listdir(self.users_dir):
                if os.path.isdir(os.path.join(self.users_dir, user_dir)):
                    self.users.append(user_dir)

    def add_user(self, username):
        """新しいユーザーを追加"""
        user_dir = os.path.join(self.users_dir, username)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
            os.makedirs(os.path.join(user_dir, "audio"))
            os.makedirs(os.path.join(user_dir, "transcripts"))
            os.makedirs(os.path.join(user_dir, "models"))
        self.load_users()

    def get_user_dir(self, username=None):
        """ユーザーのディレクトリを取得"""
        if username is None:
            username = self.current_user
        return os.path.join(self.users_dir, username)

class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("音声認識アプリ")
        self.root.geometry("1000x800")
        
        # 音声再生の初期化
        pygame.mixer.init()
        
        # ユーザー管理
        self.user_manager = UserManager()
        
        # スタイル設定
        style = ttk.Style()
        style.configure('Custom.TButton', padding=5)
        style.configure('Custom.TFrame', padding=10)
        
        # ユーザー選択フレーム
        self.setup_user_frame()
        
        # タブコントロール
        self.tab_control = ttk.Notebook(root)
        
        # 音声認識タブ
        recognition_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(recognition_tab, text='音声認識')
        self.setup_recognition_tab(recognition_tab)
        
        # データセット管理タブ
        dataset_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(dataset_tab, text='データセット管理')
        self.setup_dataset_tab(dataset_tab)
        
        # 学習タブ
        training_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(training_tab, text='モデル学習')
        self.setup_training_tab(training_tab)
        
        self.tab_control.pack(expand=True, fill=tk.BOTH)

    def setup_user_frame(self):
        """ユーザー選択フレームの設定"""
        user_frame = ttk.Frame(self.root)
        user_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(user_frame, text="ユーザー:").pack(side=tk.LEFT)
        
        self.user_var = tk.StringVar()
        self.user_combo = ttk.Combobox(user_frame, textvariable=self.user_var)
        self.user_combo.pack(side=tk.LEFT, padx=5)
        self.refresh_user_list()
        
        ttk.Button(user_frame, text="新規ユーザー", 
                  command=self.create_new_user).pack(side=tk.LEFT, padx=5)
        
        self.user_combo.bind('<<ComboboxSelected>>', self.on_user_selected)

    def refresh_user_list(self):
        """ユーザー一覧を更新"""
        self.user_manager.load_users()
        self.user_combo['values'] = self.user_manager.users
        if self.user_manager.users:
            self.user_combo.set(self.user_manager.users[0])
            self.user_manager.current_user = self.user_manager.users[0]

    def create_new_user(self):
        """新規ユーザーの作成"""
        def create():
            username = username_var.get().strip()
            if username:
                self.user_manager.add_user(username)
                self.refresh_user_list()
                self.user_var.set(username)
                self.user_manager.current_user = username
                dialog.destroy()
        
        dialog = tk.Toplevel(self.root)
        dialog.title("新規ユーザー作成")
        dialog.geometry("300x100")
        
        username_var = tk.StringVar()
        ttk.Label(dialog, text="ユーザー名:").pack(pady=5)
        ttk.Entry(dialog, textvariable=username_var).pack(pady=5)
        ttk.Button(dialog, text="作成", command=create).pack(pady=5)

    def on_user_selected(self, event):
        """ユーザーが選択されたときの処理"""
        self.user_manager.current_user = self.user_var.get()
        self.refresh_dataset_list()
        self.refresh_training_list()

    def setup_recognition_tab(self, parent):
        """音声認識タブの設定"""
        main_frame = ttk.Frame(parent, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ファイル選択部分
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_path = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="参照", 
                              command=self.browse_file, style='Custom.TButton')
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 実行ボタン
        self.process_btn = ttk.Button(main_frame, text="文字起こし開始", 
                                    command=self.start_processing, style='Custom.TButton')
        self.process_btn.pack(pady=(0, 10))
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                      maximum=100, length=300)
        self.progress.pack(pady=(0, 5))
        
        self.status_var = tk.StringVar()
        self.status_var.set("ファイルを選択してください")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))
        
        # 結果表示エリア
        result_frame = ttk.Frame(main_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        result_label = ttk.Label(result_frame, text="認識結果:")
        result_label.pack(anchor=tk.W)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, 
                                                   height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 保存ボタン
        self.save_btn = ttk.Button(main_frame, text="結果を保存", 
                                 command=self.save_result, style='Custom.TButton')
        self.save_btn.pack(pady=10)
        self.save_btn.config(state=tk.DISABLED)

    def setup_dataset_tab(self, parent):
        """データセット管理タブの設定"""
        main_frame = ttk.Frame(parent, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # データセット一覧
        list_frame = ttk.LabelFrame(main_frame, text="音声データ一覧", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.dataset_tree = ttk.Treeview(list_frame, columns=('date', 'file', 'status'),
                                       show='headings')
        self.dataset_tree.heading('date', text='日時')
        self.dataset_tree.heading('file', text='ファイル')
        self.dataset_tree.heading('status', text='状態')
        self.dataset_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                command=self.dataset_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dataset_tree.config(yscrollcommand=scrollbar.set)
        
        # プレビューエリア
        preview_frame = ttk.LabelFrame(main_frame, text="プレビュー", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 音声コントロール
        audio_frame = ttk.Frame(preview_frame)
        audio_frame.pack(fill=tk.X)
        
        self.play_btn = ttk.Button(audio_frame, text="▶ 再生", 
                                 command=self.play_audio)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # テキストエリア
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, 
                                                    height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 編集ボタン
        button_frame = ttk.Frame(preview_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="テキストを保存", 
                  command=self.save_edited_text).pack(side=tk.LEFT, padx=5)
        
        self.dataset_tree.bind('<<TreeviewSelect>>', self.on_dataset_selected)

    def play_audio(self):
        """選択された音声ファイルを再生"""
        selection = self.dataset_tree.selection()
        if not selection:
            return
        
        item = self.dataset_tree.item(selection[0])
        audio_path = os.path.join(
            self.user_manager.get_user_dir(),
            "audio",
            item['values'][1]
        )
        
        if os.path.exists(audio_path):
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                self.play_btn['text'] = "▶ 再生"
            else:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                self.play_btn['text'] = "■ 停止"

    def save_edited_text(self):
        """編集されたテキストを保存"""
        selection = self.dataset_tree.selection()
        if not selection:
            return
        
        item = self.dataset_tree.item(selection[0])
        transcript_path = os.path.join(
            self.user_manager.get_user_dir(),
            "transcripts",
            os.path.splitext(item['values'][1])[0] + ".txt"
        )
        
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(self.preview_text.get(1.0, tk.END))
        
        messagebox.showinfo("保存完了", "テキストを保存しました")

    def on_dataset_selected(self, event):
        """データセットが選択されたときの処理"""
        selection = self.dataset_tree.selection()
        if not selection:
            return
        
        item = self.dataset_tree.item(selection[0])
        transcript_path = os.path.join(
            self.user_manager.get_user_dir(),
            "transcripts",
            os.path.splitext(item['values'][1])[0] + ".txt"
        )
        
        self.preview_text.delete(1.0, tk.END)
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r', encoding='utf-8') as f:
                self.preview_text.insert(tk.END, f.read())

    def refresh_dataset_list(self):
        """データセットリストを更新"""
        self.dataset_tree.delete(*self.dataset_tree.get_children())
        
        if not self.user_manager.current_user:
            return
        
        user_dir = self.user_manager.get_user_dir()
        audio_dir = os.path.join(user_dir, "audio")
        transcripts_dir = os.path.join(user_dir, "transcripts")
        
        if not os.path.exists(audio_dir):
            return
        
        for audio_file in os.listdir(audio_dir):
            if audio_file.endswith(('.wav', '.mp3', '.m4a')):
                timestamp = os.path.splitext(audio_file)[0]
                transcript_file = os.path.splitext(audio_file)[0] + ".txt"
                status = "完了" if os.path.exists(
                    os.path.join(transcripts_dir, transcript_file)
                ) else "未編集"
                
                self.dataset_tree.insert('', 'end', values=(
                    timestamp,
                    audio_file,
                    status
                ))

    def refresh_training_list(self):
        """学習データリストを更新"""
        self.train_tree.delete(*self.train_tree.get_children())
        
        if not self.user_manager.current_user:
            return
        
        user_dir = self.user_manager.get_user_dir()
        audio_dir = os.path.join(user_dir, "audio")
        transcripts_dir = os.path.join(user_dir, "transcripts")
        
        if not os.path.exists(audio_dir):
            return
        
        for audio_file in os.listdir(audio_dir):
            if audio_file.endswith(('.wav', '.mp3', '.m4a')):
                timestamp = os.path.splitext(audio_file)[0]
                transcript_file = os.path.splitext(audio_file)[0] + ".txt"
                status = "完了" if os.path.exists(
                    os.path.join(transcripts_dir, transcript_file)
                ) else "未編集"
                
                self.train_tree.insert('', 'end', values=(
                    timestamp,
                    audio_file,
                    status
                ))

    def setup_training_tab(self, parent):
        """学習タブの設定"""
        main_frame = ttk.Frame(parent, style='Custom.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # データセット選択
        dataset_frame = ttk.LabelFrame(main_frame, text="学習データ選択", padding=10)
        dataset_frame.pack(fill=tk.BOTH, expand=True)
        
        self.train_tree = ttk.Treeview(dataset_frame, 
                                     columns=('date', 'file', 'status'),
                                     show='headings')
        self.train_tree.heading('date', text='日時')
        self.train_tree.heading('file', text='ファイル')
        self.train_tree.heading('status', text='状態')
        self.train_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(dataset_frame, orient=tk.VERTICAL, 
                                command=self.train_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.train_tree.config(yscrollcommand=scrollbar.set)
        
        # 学習設定
        settings_frame = ttk.LabelFrame(main_frame, text="学習設定", padding=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # エポック数
        epoch_frame = ttk.Frame(settings_frame)
        epoch_frame.pack(fill=tk.X)
        ttk.Label(epoch_frame, text="エポック数:").pack(side=tk.LEFT)
        self.epoch_var = tk.StringVar(value="3")
        epoch_entry = ttk.Entry(epoch_frame, textvariable=self.epoch_var, width=10)
        epoch_entry.pack(side=tk.LEFT, padx=5)
        
        # バッチサイズ
        batch_frame = ttk.Frame(settings_frame)
        batch_frame.pack(fill=tk.X)
        ttk.Label(batch_frame, text="バッチサイズ:").pack(side=tk.LEFT)
        self.batch_var = tk.StringVar(value="4")
        batch_entry = ttk.Entry(batch_frame, textvariable=self.batch_var, width=10)
        batch_entry.pack(side=tk.LEFT, padx=5)
        
        # 学習率
        lr_frame = ttk.Frame(settings_frame)
        lr_frame.pack(fill=tk.X)
        ttk.Label(lr_frame, text="学習率:").pack(side=tk.LEFT)
        self.lr_var = tk.StringVar(value="1e-5")
        lr_entry = ttk.Entry(lr_frame, textvariable=self.lr_var, width=10)
        lr_entry.pack(side=tk.LEFT, padx=5)
        
        # 学習ボタン
        self.train_btn = ttk.Button(main_frame, text="学習開始", 
                                  command=self.start_training, style='Custom.TButton')
        self.train_btn.pack(pady=10)
        
        # 進捗表示
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                      maximum=100, length=300)
        self.progress.pack(pady=(0, 5))
        
        self.status_var = tk.StringVar()
        self.status_var.set("学習データを選択してください")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=(0, 10))

    def start_training(self):
        """モデルの学習を開始"""
        selected = self.train_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "学習に使用するデータを選択してください")
            return
        
        try:
            epochs = int(self.epoch_var.get())
            batch_size = int(self.batch_var.get())
            learning_rate = float(self.lr_var.get())
        except ValueError:
            messagebox.showerror("エラー", "学習パラメータの値が不正です")
            return
        
        # 選択されたデータの音声ファイルとテキストファイルを取得
        user_dir = self.user_manager.get_user_dir()
        training_data = []
        
        for item_id in selected:
            item = self.train_tree.item(item_id)
            audio_file = item['values'][1]
            audio_path = os.path.join(user_dir, "audio", audio_file)
            transcript_path = os.path.join(
                user_dir, "transcripts",
                os.path.splitext(audio_file)[0] + ".txt"
            )
            
            if os.path.exists(audio_path) and os.path.exists(transcript_path):
                training_data.append({
                    'audio': audio_path,
                    'transcript': transcript_path
                })
        
        if not training_data:
            messagebox.showerror("エラー", "有効な学習データがありません")
            return
        
        self.train_btn.config(state=tk.DISABLED)
        self.status_var.set("学習を準備中...")
        self.progress_var.set(0)
        
        def train():
            try:
                # 学習用の一時データセットを作成
                temp_dataset_dir = os.path.join(user_dir, "temp_dataset")
                os.makedirs(temp_dataset_dir, exist_ok=True)
                
                # データをコピー
                for i, data in enumerate(training_data):
                    data_dir = os.path.join(temp_dataset_dir, f"data_{i}")
                    os.makedirs(data_dir, exist_ok=True)
                    
                    # 音声ファイルをコピー
                    shutil.copy2(data['audio'], 
                               os.path.join(data_dir, "audio" + os.path.splitext(data['audio'])[1]))
                    
                    # テキストファイルをコピー
                    shutil.copy2(data['transcript'], 
                               os.path.join(data_dir, "transcript.txt"))
                
                # モデルの学習
                model_path = fine_tune_model(
                    "base",
                    temp_dataset_dir,
                    epochs=epochs,
                    batch_size=batch_size,
                    learning_rate=learning_rate
                )
                
                # 学習済みモデルをユーザーディレクトリに移動
                user_model_dir = os.path.join(user_dir, "models")
                os.makedirs(user_model_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                final_model_path = os.path.join(user_model_dir, f"model_{timestamp}")
                shutil.move(model_path, final_model_path)
                
                # 一時データセットを削除
                shutil.rmtree(temp_dataset_dir)
                
                self.root.after(0, lambda: self.status_var.set(
                    f"学習が完了しました: {final_model_path}"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "エラー", f"学習中にエラーが発生しました: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.train_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.progress_var.set(100))
        
        thread = threading.Thread(target=train)
        thread.start()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("音声ファイル", "*.wav;*.mp3;*.m4a"),
                ("すべてのファイル", "*.*")
            ]
        )
        if file_path:
            self.file_path.set(file_path)
            self.status_var.set("ファイルが選択されました")

    def update_progress(self, progress, status):
        self.progress_var.set(progress)
        self.status_var.set(status)
        self.root.update_idletasks()

    def start_processing(self):
        if not self.file_path.get():
            self.status_var.set("ファイルを選択してください")
            return
        
        if not self.user_manager.current_user:
            messagebox.showerror("エラー", "ユーザーを選択してください")
            return
        
        self.process_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        
        def process():
            try:
                # 音声ファイルを処理
                result, transcript_file, dataset_dir = transcribe_audio(
                    self.file_path.get(), 
                    progress_callback=self.update_progress
                )
                
                # 結果をユーザーディレクトリに保存
                user_dir = self.user_manager.get_user_dir()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # 音声ファイルをコピー
                audio_dir = os.path.join(user_dir, "audio")
                os.makedirs(audio_dir, exist_ok=True)
                audio_ext = os.path.splitext(self.file_path.get())[1]
                audio_file = os.path.join(audio_dir, f"{timestamp}{audio_ext}")
                shutil.copy2(self.file_path.get(), audio_file)
                
                # テキストファイルを保存
                transcripts_dir = os.path.join(user_dir, "transcripts")
                os.makedirs(transcripts_dir, exist_ok=True)
                transcript_file = os.path.join(transcripts_dir, f"{timestamp}.txt")
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                self.root.after(0, lambda: self.result_text.insert(tk.END, result))
                self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("処理が完了しました"))
                self.root.after(0, self.refresh_dataset_list)
                
            except Exception as e:
                error_message = f"エラーが発生しました: {str(e)}"
                self.root.after(0, lambda: self.status_var.set(error_message))
            finally:
                self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
        
        thread = threading.Thread(target=process)
        thread.start()

    def save_result(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("テキストファイル", "*.txt")],
            initialfile="認識結果.txt"
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.result_text.get(1.0, tk.END))
            self.status_var.set(f"結果を保存しました: {file_path}")

def initialize_whisper():
    """Whisperの初期化とアセットの設定"""
    import os
    import whisper
    import whisper.audio
    import urllib.request
    import tempfile
    import shutil
    import numpy as np
    
    # アプリケーション固有のキャッシュディレクトリを作成
    app_cache_dir = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), 'WhisperSR'))
    models_dir = os.path.join(app_cache_dir, 'models')
    assets_dir = os.path.join(app_cache_dir, 'assets')
    temp_dir = os.path.join(app_cache_dir, 'temp')
    
    # 必要なディレクトリを作成
    for dir_path in [app_cache_dir, models_dir, assets_dir, temp_dir]:
        os.makedirs(dir_path, exist_ok=True)
        print(f"ディレクトリを確認: {dir_path}")
    
    # 環境変数の設定（重要: これを最初に行う）
    os.environ["TEMP"] = temp_dir
    os.environ["TMP"] = temp_dir
    os.environ["XDG_CACHE_HOME"] = app_cache_dir
    os.environ["WHISPER_HOME"] = app_cache_dir
    
    # Whisperのパスを設定
    whisper.audio.ASSETS_PATH = assets_dir
    print(f"Whisperアセットパス: {whisper.audio.ASSETS_PATH}")
    print(f"一時ディレクトリ: {temp_dir}")
    
    # mel_filters.npzファイルの生成
    mel_filters_path = os.path.join(assets_dir, "mel_filters.npz")
    if not os.path.exists(mel_filters_path):
        print("mel_filters.npzを生成中...")
        try:
            # Whisperのデフォルト設定に基づくメルフィルタバンクの生成
            n_mels = 80
            n_fft = 400
            sampling_rate = 16000
            min_f = 0
            max_f = 8000
            
            def hz_to_mel(f):
                return 2595 * np.log10(1 + f / 700)
            
            def mel_to_hz(m):
                return 700 * (10**(m / 2595) - 1)
            
            # メルスケールの周波数ポイントを生成
            mel_min = hz_to_mel(min_f)
            mel_max = hz_to_mel(max_f)
            mel_points = np.linspace(mel_min, mel_max, n_mels + 2)
            hz_points = mel_to_hz(mel_points)
            
            # FFTビン周波数
            fft_freqs = np.linspace(0, sampling_rate/2, n_fft//2 + 1)
            
            # メルフィルタバンクの生成
            mel_filters = np.zeros((n_mels, n_fft//2 + 1))
            for i in range(n_mels):
                lower = hz_points[i]
                center = hz_points[i+1]
                upper = hz_points[i+2]
                
                # 三角フィルタの左側
                left_slope = (fft_freqs - lower) / (center - lower)
                right_slope = (upper - fft_freqs) / (upper - center)
                mel_filters[i] = np.maximum(0, np.minimum(left_slope, right_slope))
            
            # 正規化
            enorm = 2.0 / (hz_points[2:] - hz_points[:-2])
            mel_filters *= enorm[:, np.newaxis]
            
            # float32に変換して保存
            mel_filters = mel_filters.astype(np.float32)
            np.savez_compressed(mel_filters_path, mel_80=mel_filters)
            print(f"✓ mel_filters.npzを生成しました: {mel_filters_path}")
        except Exception as e:
            raise RuntimeError(f"mel_filters.npzの生成に失敗: {str(e)}")
    else:
        print(f"✓ mel_filters.npzが存在します: {mel_filters_path}")
    
    # モデルを事前にダウンロード
    try:
        print("Whisperモデルをダウンロード中...")
        model = whisper.load_model("base", download_root=models_dir)
        print("✓ モデルのダウンロードが完了しました")
        
        # テスト用の音声データでモデルの動作確認
        print("モデルの動作確認中...")
        test_audio = np.zeros(16000, dtype=np.float32)
        mel = whisper.audio.log_mel_spectrogram(test_audio)
        print("✓ メルスペクトログラム変換のテストに成功")
        
    except Exception as e:
        raise RuntimeError(f"Whisperの初期化に失敗: {str(e)}")

def main():
    try:
        # Whisperの初期化
        print("アプリケーションを初期化中...")
        initialize_whisper()
        
        # GUIの起動
        root = tk.Tk()
        app = SpeechRecognitionApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        error_message = f"アプリケーションの起動中にエラーが発生しました:\n{str(e)}\n\n"
        error_message += traceback.format_exc()
        
        # エラーウィンドウを作成
        error_root = tk.Tk()
        error_root.title("エラー")
        error_root.geometry("600x400")
        
        # エラーメッセージを表示
        error_text = scrolledtext.ScrolledText(error_root, wrap=tk.WORD, width=70, height=20)
        error_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        error_text.insert(tk.END, error_message)
        error_text.config(state=tk.DISABLED)
        
        # 閉じるボタン
        close_btn = ttk.Button(error_root, text="閉じる", command=error_root.destroy)
        close_btn.pack(pady=10)
        
        error_root.mainloop()
        sys.exit(1)

if __name__ == "__main__":
    main()
