import sounddevice as sd
import numpy as np
import wave
import os
from datetime import datetime

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1):
        """
        音声録音クラスの初期化
        Args:
            sample_rate (int): サンプリングレート（デフォルト: 16000 Hz）
            channels (int): チャンネル数（デフォルト: 1 - モノラル）
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = None
        self.is_recording = False

    def start_recording(self, duration):
        """
        指定された時間の音声を録音
        Args:
            duration (float): 録音時間（秒）
        """
        print("録音を開始します...")
        self.recording = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.int16
        )
        self.is_recording = True
        sd.wait()  # 録音が完了するまで待機
        self.is_recording = False
        print("録音が完了しました")

    def save_recording(self, output_dir="recordings"):
        """
        録音した音声をWAVファイルとして保存
        Args:
            output_dir (str): 保存先ディレクトリ
        Returns:
            str: 保存したファイルのパス
        """
        if self.recording is None:
            raise ValueError("録音データがありません")

        # 保存先ディレクトリの作成
        os.makedirs(output_dir, exist_ok=True)

        # タイムスタンプを含むファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"recording_{timestamp}.wav")

        # WAVファイルとして保存
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(self.recording.tobytes())

        print(f"録音を保存しました: {filename}")
        return filename

def main():
    """
    テスト用のメイン関数
    """
    recorder = AudioRecorder()
    
    try:
        # 5秒間の録音をテスト
        recorder.start_recording(5)
        recorder.save_recording()
    except KeyboardInterrupt:
        print("\n録音を中断しました")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main()
