import whisper
import wave
import numpy as np
import os
import json
from datetime import datetime
import traceback
import threading
import re
import sys
from tqdm import tqdm
import torch
from torch.utils.data import Dataset, DataLoader

# プロジェクトのパス設定
PROJECT_DIR = os.path.abspath(os.path.join(os.getenv('LOCALAPPDATA'), 'WhisperSR'))
TRANSCRIPTS_DIR = os.path.join(PROJECT_DIR, 'transcripts')
DATASET_DIR = os.path.join(PROJECT_DIR, 'dataset')
ANNOTATIONS_DIR = os.path.join(PROJECT_DIR, 'annotations')
FINETUNED_DIR = os.path.join(PROJECT_DIR, 'finetuned_models')
MODELS_DIR = os.path.join(PROJECT_DIR, 'models')
TEMP_DIR = os.path.join(PROJECT_DIR, 'temp')
ASSETS_DIR = os.path.join(PROJECT_DIR, 'assets')

# 環境変数の設定
os.environ["TEMP"] = TEMP_DIR
os.environ["TMP"] = TEMP_DIR
os.environ["XDG_CACHE_HOME"] = PROJECT_DIR
os.environ["WHISPER_HOME"] = PROJECT_DIR

# ディレクトリの作成
for dir_path in [TRANSCRIPTS_DIR, DATASET_DIR, ANNOTATIONS_DIR, FINETUNED_DIR, 
                MODELS_DIR, TEMP_DIR, ASSETS_DIR]:
    os.makedirs(dir_path, exist_ok=True)
    print(f"✓ ディレクトリを確認: {dir_path}")

# Whisperのパスを設定
whisper.audio.ASSETS_PATH = ASSETS_DIR

# mel_filters.npzファイルのダウンロード
mel_filters_path = os.path.join(ASSETS_DIR, "mel_filters.npz")
if not os.path.exists(mel_filters_path):
    print("mel_filters.npzをダウンロード中...")
    try:
        import urllib.request
        mel_filters_url = "https://raw.githubusercontent.com/openai/whisper/main/whisper/assets/mel_filters.npz"
        urllib.request.urlretrieve(mel_filters_url, mel_filters_path)
        print(f"✓ mel_filters.npzをダウンロードしました: {mel_filters_path}")
    except Exception as e:
        raise RuntimeError(f"mel_filters.npzのダウンロードに失敗: {str(e)}")
else:
    print(f"✓ mel_filters.npzが存在します: {mel_filters_path}")

# ファイルサイズの確認
file_size = os.path.getsize(mel_filters_path)
print(f"mel_filters.npzのサイズ: {file_size} bytes")

class AudioTextDataset(Dataset):
    def __init__(self, dataset_dir):
        self.samples = []
        for timestamp_dir in os.listdir(dataset_dir):
            dir_path = os.path.join(dataset_dir, timestamp_dir)
            if os.path.isdir(dir_path):
                audio_files = [f for f in os.listdir(dir_path) if f.startswith('audio')]
                if audio_files and os.path.exists(os.path.join(dir_path, 'transcript.txt')):
                    self.samples.append({
                        'audio': os.path.join(dir_path, audio_files[0]),
                        'transcript': os.path.join(dir_path, 'transcript.txt'),
                        'annotation': os.path.join(dir_path, 'annotation.json')
                    })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        try:
            sample = self.samples[idx]
            audio_path = sample['audio']
            
            # 音声ファイルの存在確認
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
            
            # テキストファイルの読み込み
            transcript = ""
            if os.path.exists(sample['transcript']):
                with open(sample['transcript'], 'r', encoding='utf-8') as f:
                    transcript = f.read().strip()
            else:
                raise FileNotFoundError(f"テキストファイルが見つかりません: {sample['transcript']}")
            
            # アノテーションの読み込み（オプション）
            annotation = {}
            if os.path.exists(sample['annotation']):
                with open(sample['annotation'], 'r', encoding='utf-8') as f:
                    annotation = json.load(f)
            
            return {
                'audio_path': audio_path,
                'transcript': transcript,
                'annotation': annotation
            }
        except Exception as e:
            print(f"データの読み込みエラー (idx={idx}): {str(e)}")
            # エラーが発生した場合は空のデータを返す
            return {
                'audio_path': "",
                'transcript': "",
                'annotation': {}
            }

def fine_tune_model(base_model, dataset_dir, epochs=3, batch_size=4, learning_rate=1e-5, progress_callback=None):
    """Whisperモデルのファインチューニングを実行"""
    dataset = AudioTextDataset(dataset_dir)
    if len(dataset) == 0:
        raise ValueError("データセットが空です")

    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    # デバイスの設定
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # ベースモデルのロード
    try:
        if os.path.isdir(base_model):
            # カスタムモデルを使用
            checkpoint = torch.load(os.path.join(base_model, 'model.pt'), map_location=device)
            base_model = whisper.load_model(MODEL_NAME, device=device, download_root=MODELS_DIR)
            base_model.load_state_dict(checkpoint['model_state_dict'])
            model = base_model
        else:
            # 標準モデルを使用
            model = whisper.load_model(base_model, download_root=MODELS_DIR, device=device)
        
        print(f"Model loaded successfully:")
        print(f"- Device: {device}")
        print(f"- Model type: {'Custom' if os.path.isdir(base_model) else base_model}")
        print(f"- Dimensions: {model.dims}")
    except Exception as e:
        raise RuntimeError(f"モデルのロードに失敗: {str(e)}")
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_save_path = os.path.join(FINETUNED_DIR, f'model_{timestamp}')
    
    total_steps = epochs * len(dataloader)
    current_step = 0
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in tqdm(dataloader, desc=f'Epoch {epoch+1}/{epochs}'):
            optimizer.zero_grad()
            batch_loss = 0
            
            # バッチ内の各サンプルに対して処理
            for i in range(len(batch['audio_path'])):
                audio_path = batch['audio_path'][i]
                transcript = batch['transcript'][i]
                
                try:
                    # 音声をWhisper形式に変換
                    audio = whisper.load_audio(audio_path)
                    audio = whisper.pad_or_trim(audio)
                    mel = whisper.log_mel_spectrogram(audio).to(model.device)
                    
                    # エンコーダーの出力を取得
                    encoder_output = model.encoder(mel.unsqueeze(0))
                    
                    # テキストのトークン化
                    tokens = torch.tensor([model.tokenizer.encode(transcript)]).to(model.device)
                    
                    # デコーダーの入力準備
                    decoder_input = tokens[:, :-1]  # 最後のトークンを除外
                    target = tokens[:, 1:]  # 最初のトークンを除外
                    
                    # デコーダーの出力を取得
                    decoder_output = model.decoder(decoder_input, encoder_output)
                    
                    # 損失計算
                    loss = torch.nn.functional.cross_entropy(
                        decoder_output.view(-1, decoder_output.size(-1)),
                        target.view(-1),
                        ignore_index=-100
                    )
                    loss.backward()
                    batch_loss += loss.item()
                except Exception as e:
                    print(f"サンプル処理中にエラー: {str(e)}")
                    continue
            
            optimizer.step()
            total_loss += batch_loss / len(batch)
            
            # 進捗更新
            current_step += 1
            if progress_callback:
                progress = (current_step / total_steps) * 100
                avg_loss = total_loss / (len(dataloader) * (epoch + 1))
                progress_callback(progress, 
                                f'Epoch {epoch+1}/{epochs} Loss: {avg_loss:.4f}')
    
    try:
        # モデルの保存
        os.makedirs(model_save_path, exist_ok=True)
        torch.save({
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'dims': model.dims,
            'device': device
        }, os.path.join(model_save_path, 'model.pt'))
        print(f"モデルを保存しました: {model_save_path}")
    except Exception as e:
        raise RuntimeError(f"モデルの保存に失敗: {str(e)}")
    
    # 学習情報の保存
    info = {
        'timestamp': timestamp,
        'base_model': base_model,
        'epochs': epochs,
        'batch_size': batch_size,
        'learning_rate': learning_rate,
        'final_loss': total_loss / len(dataloader),
        'dataset_size': len(dataset),
        'training_completed': True
    }
    
    with open(os.path.join(model_save_path, 'training_info.json'), 'w', 
              encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    
    return model_save_path

def add_annotation(dataset_dir, timestamp, annotation_data):
    """データセットにアノテーションを追加"""
    dataset_subdir = os.path.join(dataset_dir, timestamp)
    if not os.path.exists(dataset_subdir):
        raise ValueError(f"指定されたタイムスタンプのデータセットが見つかりません: {timestamp}")
    
    annotation_file = os.path.join(dataset_subdir, 'annotation.json')
    with open(annotation_file, 'w', encoding='utf-8') as f:
        json.dump(annotation_data, f, ensure_ascii=False, indent=2)
    
    return annotation_file

# Whisperモデルの設定
MODEL_NAME = "base"  # 処理速度と精度のバランスを考慮

def check_audio_file(audio_file):
    """音声ファイルの存在と形式を確認"""
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_file}")
    
    try:
        import soundfile as sf
        info = sf.info(audio_file)
        print(f"音声ファイル情報:")
        print(f"- サンプリングレート: {info.samplerate} Hz")
        print(f"- チャンネル数: {info.channels}")
        print(f"- 長さ: {info.duration:.2f} 秒")
        print(f"- フォーマット: {info.format}")
        return True
    except Exception as e:
        raise ValueError(f"音声ファイルの読み込みに失敗しました: {str(e)}")

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
        if self.callback is None:
            return
            
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

def transcribe_audio(audio_file, model_path=None, progress_callback=None):
    """音声認識を実行し、結果を保存する"""
    try:
        # 音声ファイルの確認
        check_audio_file(audio_file)
        update_progress(progress_callback, 0, f"音声ファイルを読み込み中: {audio_file}")
        
        # Whisperモデルの読み込みと設定
        try:
            update_progress(progress_callback, 5, "Whisperモデルをダウンロード/読み込み中...")
            start_time = datetime.now()
            
            # モデルをロード
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f"Using device: {device}")
                
                if device == "cpu":
                    # CPU使用時はメモリ使用量を抑制
                    torch.set_num_threads(4)  # スレッド数を制限
                    torch.set_num_interop_threads(4)
                
                if model_path and os.path.isdir(model_path):
                    # カスタムモデルを使用
                    checkpoint = torch.load(os.path.join(model_path, 'model.pt'), map_location=device)
                    base_model = whisper.load_model(MODEL_NAME, device=device, download_root=MODELS_DIR)
                    base_model.load_state_dict(checkpoint['model_state_dict'])
                    model = base_model
                else:
                    # デフォルトモデルを使用
                    model = whisper.load_model(MODEL_NAME, device=device, download_root=MODELS_DIR)
                
                if device == "cpu":
                    # CPUモードの場合、メモリ使用量を最適化
                    model.encoder.conv1.padding_mode = 'zeros'
                    model.encoder.conv2.padding_mode = 'zeros'
                    
                # モデル情報の表示
                print(f"Model loaded successfully:")
                print(f"- Device: {device}")
                print(f"- Model type: {'Custom' if model_path else MODEL_NAME}")
                print(f"- Dimensions: {model.dims}")
                print(f"- Language: Japanese")
                
            except Exception as e:
                raise RuntimeError(f"モデルのロードに失敗: {str(e)}\n{traceback.format_exc()}")
            
            # テスト用の音声データでモデルの動作確認
            test_audio = np.zeros(16000, dtype=np.float32)
            mel = whisper.audio.log_mel_spectrogram(test_audio)
            print("✓ メルスペクトログラム変換のテストに成功")
            load_time = (datetime.now() - start_time).total_seconds()
            update_progress(progress_callback, 10, f"モデルの読み込みが完了しました（所要時間: {load_time:.2f}秒）")
        except Exception as e:
            raise RuntimeError(f"Whisperモデルの読み込みに失敗しました: {str(e)}")
        
        # 日本語に特化した設定でWhisperを実行
        try:
            update_progress(progress_callback, 15, "音声認識を実行中...")
            start_time = datetime.now()
            
            # 音声認識の実行
            update_progress(progress_callback, 20, "音声認識を開始...")
            
            # 音声データの読み込みと前処理
            try:
                import soundfile as sf
                audio, sr = sf.read(audio_file)
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)  # ステレオをモノラルに変換
                if sr != whisper.audio.SAMPLE_RATE:
                    # リサンプリングが必要な場合
                    from scipy import signal
                    audio = signal.resample(audio, int(len(audio) * whisper.audio.SAMPLE_RATE / sr))
                audio = whisper.pad_or_trim(audio.astype(np.float32))
                
                # メルスペクトログラムの計算
                mel = whisper.log_mel_spectrogram(audio).to(model.device)
                print(f"✓ 音声データの読み込みに成功 (shape: {audio.shape}, sr: {sr})")
            except Exception as e:
                raise RuntimeError(f"音声データの読み込みに失敗: {str(e)}")
            
            # 進捗表示用の関数
            def update_transcription_progress():
                for i in range(10):
                    progress = 20 + (i * 6)
                    update_progress(progress_callback, progress, 
                                  f"音声認識を実行中... {i * 10}%")
                    import time
                    time.sleep(0.2)
            
            # 進捗表示用のスレッド
            progress_thread = threading.Thread(target=update_transcription_progress)
            progress_thread.daemon = True
            progress_thread.start()
            
            # 音声認識の実行（シンプルな方法で再試行）
            try:
                result = model.transcribe(
                    audio_file,
                    language="ja",
                    task="transcribe",
                    fp16=False,
                    verbose=False,
                    initial_prompt="日本語の音声を認識します。"
                )
            except Exception as e:
                print(f"最初の試行でエラー: {str(e)}")
                print("別の方法で再試行します...")
                
                # 別の方法で再試行
                options = whisper.DecodingOptions(
                    language="ja",
                    task="transcribe",
                    fp16=False,
                    prompt="日本語の音声を認識します。"
                )
                result = model.decode(mel, options)
                result = {
                    "text": result.text,
                    "segments": [{
                        "text": result.text,
                        "start": 0,
                        "end": len(audio) / whisper.audio.SAMPLE_RATE
                    }]
                }
            
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
        
            # データセットとして保存（音声ファイル、転記、JSONメタデータ）
        try:
            update_progress(progress_callback, 95, "データセットを保存中...")
            dataset_subdir = os.path.join(DATASET_DIR, timestamp)
            os.makedirs(dataset_subdir, exist_ok=True)
            
            # 音声ファイルをデータセットにコピー
            import shutil
            audio_extension = os.path.splitext(audio_file)[1]
            dataset_audio = os.path.join(dataset_subdir, f'audio{audio_extension}')
            shutil.copy2(audio_file, dataset_audio)
            
            # 転記テキストをJSONフォーマットで保存
            dataset_json = os.path.join(dataset_subdir, 'transcript.json')
            transcript_data = {
                'text': text,
                'segments': segments,
                'metadata': {
                    'timestamp': timestamp,
                    'model': MODEL_NAME,
                    'process_time': process_time,
                    'audio_file': os.path.basename(audio_file)
                }
            }
            with open(dataset_json, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            # プレーンテキストとしても保存
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
            if sys.argv[1] == "--finetune":
                # ファインチューニングモード
                print("ファインチューニングを開始します...")
                model_path = fine_tune_model(MODEL_NAME, DATASET_DIR)
                print(f"モデルを保存しました: {model_path}")
            else:
                # 通常の音声認識モード
                audio_file = sys.argv[1]
                result, transcript_file, dataset_dir = transcribe_audio(audio_file)
                
                # アノテーション例の追加
                timestamp = os.path.basename(dataset_dir)
                annotation_data = {
                    "speaker": "unknown",
                    "environment": "unknown",
                    "quality_score": 0,
                    "notes": "",
                    "verified": False
                }
                annotation_file = add_annotation(DATASET_DIR, timestamp, annotation_data)
                print(f"\nアノテーションファイルを作成しました: {annotation_file}")
        else:
            audio_file = os.path.join(PROJECT_DIR, 'Test_audio.wav')
            transcribe_audio(audio_file)
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        traceback.print_exc()
    finally:
        input("\nPress Enter to close...")
