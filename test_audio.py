import numpy as np
import soundfile as sf

# テスト用の音声データを生成（1秒のサイン波）
duration = 1.0  # 秒
sample_rate = 16000
t = np.linspace(0, duration, int(sample_rate * duration))
frequency = 440.0  # Hz (A4音)
audio_data = np.sin(2 * np.pi * frequency * t)

# 音声ファイルとして保存
output_file = 'Test_audio.wav'
sf.write(output_file, audio_data, sample_rate)
print(f"テスト用音声ファイルを作成しました: {output_file}")
