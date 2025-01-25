import whisper
import wave
import numpy as np
import os
from datetime import datetime
import traceback
import threading
import re
import sys
from tqdm import tqdm

# プロジェクトのパス設定
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTS_DIR = os.path.join(PROJECT_DIR, 'transcripts')
DATASET_DIR = os.path.join(PROJECT_DIR, 'dataset')

# Whisperモデルの設定
MODEL_NAME = "base"  # 処理速度と精度のバランスを考慮

# ディレクトリの作成
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)

def check_audio_file(audio_file):
    """音声ファイルの存在と形式を確認"""
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_file}")
    
    if not audio_file.lower().endswith(('.wav', '.mp3', '.m4a')):
        raise ValueError(f"未対応の音声形式です: {os.path.splitext(audio_file)[1]}")

def update_progress(callback, progress, status):
    """進捗状況の更新"""
    if callback:
        callback(progress, status)

class ProgressCallback:
    def __init__(self, callback):
        self.callback = callback
        self.current_progress = 0
        self.total_segments = 0
        self.processed_segments = 0

    def update(self, desc=None):
        if desc:
            # Whisperの進捗メッセージから情報を抽出
            if 'frames/s]' in desc:
                match = re.search(r'(\d+)%.*?(\d+\.\d+)frames/s', desc)
                if match:
                    percent = int(match.group(1))
                    fps = float(match.group(2))
                    # 15-80%の範囲で進捗を表示（音声認識フェーズ）
                    adjusted_progress = 15 + (percent * 0.65)
                    self.callback(adjusted_progress, f"音声認識を実行中... {percent}% ({fps:.1f} frames/s)")
            else:
                self.callback(self.current_progress, desc)
        else:
            self.callback(self.current_progress, "処理中...")

def transcribe_audio(audio_file, progress_callback=None):
    """音声認識を実行し、結果を保存する"""
    try:
        # 音声ファイルの確認
        check_audio_file(audio_file)
        update_progress(progress_callback, 0, f"音声ファイルを読み込み中: {audio_file}")
        
        # Whisperモデルの読み込みと設定
        try:
            update_progress(progress_callback, 5, "Whisperモデルを読み込んでいます...")
            start_time = datetime.now()
            model = whisper.load_model(MODEL_NAME, device="cpu")
            load_time = (datetime.now() - start_time).total_seconds()
            update_progress(progress_callback, 10, f"モデルの読み込みが完了しました（所要時間: {load_time:.2f}秒）")
        except Exception as e:
            raise RuntimeError(f"Whisperモデルの読み込みに失敗しました: {str(e)}")
        
        # 日本語に特化した設定でWhisperを実行
        try:
            update_progress(progress_callback, 15, "音声認識を実行中...")
            start_time = datetime.now()
            
            # 進捗状況をキャプチャするためのカスタムコールバック
            progress_handler = ProgressCallback(progress_callback)
            
            # tqdmの出力をキャプチャ
            class TqdmToCallback:
                def write(self, s):
                    if s.strip():  # 空行を無視
                        progress_handler.update(s.strip())
                def flush(self):
                    pass
            
            # 標準出力を一時的にリダイレクト
            old_stdout = sys.stdout
            sys.stdout = TqdmToCallback()
            
            try:
                result = model.transcribe(
                    audio_file,
                    language="ja",  # 日本語を指定
                    task="transcribe",
                    fp16=False,  # 精度優先
                    verbose=True  # 詳細なログを有効化
                )
            finally:
                # 標準出力を元に戻す
                sys.stdout = old_stdout
            
            process_time = (datetime.now() - start_time).total_seconds()
            update_progress(progress_callback, 80, f"音声認識が完了しました（所要時間: {process_time:.2f}秒）")
        except Exception as e:
            raise RuntimeError(f"音声認識の実行に失敗しました: {str(e)}")
        
        # 結果の取得
        text = result["text"]
        segments = result["segments"]  # タイムスタンプ付きセグメント
        
        # タイムスタンプ付きの結果を保存
        try:
            update_progress(progress_callback, 85, "認識結果を保存中...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            transcript_file = os.path.join(TRANSCRIPTS_DIR, f'transcript_{timestamp}.txt')
            
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(f"処理時間: {process_time:.2f}秒\n\n")
                f.write(f"Full Transcript:\n{text}\n\nDetailed Segments:\n")
                for segment in segments:
                    start = segment["start"]
                    end = segment["end"]
                    segment_text = segment["text"]
                    f.write(f"[{start:.2f}s -> {end:.2f}s] {segment_text}\n")
            
            update_progress(progress_callback, 90, f"詳細な転記を保存しました: {transcript_file}")
        except Exception as e:
            raise IOError(f"転記ファイルの保存に失敗しました: {str(e)}")
        
        # データセットとして保存（音声ファイルと転記のペア）
        try:
            update_progress(progress_callback, 95, "データセットを保存中...")
            dataset_subdir = os.path.join(DATASET_DIR, timestamp)
            os.makedirs(dataset_subdir, exist_ok=True)
            
            # 音声ファイルをデータセットにコピー
            import shutil
            audio_extension = os.path.splitext(audio_file)[1]
            dataset_audio = os.path.join(dataset_subdir, f'audio{audio_extension}')
            shutil.copy2(audio_file, dataset_audio)
            
            # 転記テキストをデータセットに保存
            dataset_text = os.path.join(dataset_subdir, 'transcript.txt')
            with open(dataset_text, 'w', encoding='utf-8') as f:
                f.write(text)
            
            update_progress(progress_callback, 100, f"データセットを保存しました: {dataset_subdir}")
        except Exception as e:
            raise IOError(f"データセットの保存に失敗しました: {str(e)}")
        
        print(f"\n認識結果: {text}")
        return text, transcript_file, dataset_subdir
        
    except Exception as e:
        print(f"\n音声認識エラー: {str(e)}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    try:
        # コマンドライン引数から音声ファイルを取得
        import sys
        if len(sys.argv) > 1:
            audio_file = sys.argv[1]
        else:
            audio_file = os.path.join(PROJECT_DIR, 'Test_audio.wav')
        
        transcribe_audio(audio_file)
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        traceback.print_exc()
    finally:
        input("\nPress Enter to close...")
