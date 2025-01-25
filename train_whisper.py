import os
import json
import shutil
from datetime import datetime

def save_training_data(user, date, audio_file, original_text, corrected_text, dataset_dir):
    """学習データを保存する"""
    try:
        # 学習データ保存用のディレクトリ
        training_dir = os.path.join(dataset_dir, 'training_data')
        os.makedirs(training_dir, exist_ok=True)
        
        # 学習データの情報を保存
        training_info = {
            'user': user,
            'date': date,
            'audio_file': audio_file,
            'original_text': original_text,
            'corrected_text': corrected_text,
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        
        # 情報をJSONファイルとして保存
        info_file = os.path.join(training_dir, 'training_info.json')
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(training_info, f, ensure_ascii=False, indent=2)
        
        # 修正テキストを保存
        corrected_file = os.path.join(training_dir, 'corrected_text.txt')
        with open(corrected_file, 'w', encoding='utf-8') as f:
            f.write(corrected_text)
        
        return training_dir
    except Exception as e:
        raise Exception(f"学習データの保存に失敗しました: {str(e)}")

def train_model(training_dir):
    """モデルの学習を実行する"""
    try:
        # 学習情報の読み込み
        info_file = os.path.join(training_dir, 'training_info.json')
        with open(info_file, 'r', encoding='utf-8') as f:
            training_info = json.load(f)
        
        # 修正テキストの読み込み
        corrected_file = os.path.join(training_dir, 'corrected_text.txt')
        with open(corrected_file, 'r', encoding='utf-8') as f:
            corrected_text = f.read()
        
        # TODO: ここにWhisperモデルの学習処理を実装
        # 現在は学習データの保存のみ実装
        
        return True
    except Exception as e:
        raise Exception(f"モデルの学習に失敗しました: {str(e)}")
