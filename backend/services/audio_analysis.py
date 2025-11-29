"""
音響分析サービス (librosa)
"""
import librosa
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def analyze_audio_features(audio_path: str) -> Dict[str, Any]:
    """
    音響特徴を分析
    
    Args:
        audio_path: 音声ファイルパス
    
    Returns:
        {
            "speech_rate": 話速 (文字/分),
            "average_volume": 平均音量 (dB),
            "volume_variance": 音量のばらつき,
            "pause_count": ポーズ回数,
            "pause_total_duration": 総ポーズ時間 (秒),
            "pitch_mean": 平均ピッチ (Hz),
            "pitch_variance": ピッチのばらつき,
            "duration": 音声の長さ (秒)
        }
    """
    try:
        # 音声ロード
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        logger.info(f"音声ロード完了: {duration:.2f}秒")
        
        # === 音量分析 ===
        rms = librosa.feature.rms(y=y)[0]
        rms_db = librosa.amplitude_to_db(rms)
        
        average_volume = float(np.mean(rms_db))
        volume_variance = float(np.std(rms_db))
        
        # === ポーズ検出 ===
        # 無音区間を検出 (閾値: -40dB)
        intervals = librosa.effects.split(y, top_db=40)
        
        # ポーズ = 無音区間
        pauses = []
        for i in range(len(intervals) - 1):
            pause_start = intervals[i][1] / sr
            pause_end = intervals[i + 1][0] / sr
            pause_duration = pause_end - pause_start
            
            # 0.5秒以上のポーズのみカウント
            if pause_duration >= 0.5:
                pauses.append(pause_duration)
        
        pause_count = len(pauses)
        pause_total = sum(pauses) if pauses else 0.0
        
        # === ピッチ分析 ===
        # f0 (基本周波数) を推定
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        # 各フレームの最大ピッチを取得
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:  # 有効なピッチのみ
                pitch_values.append(pitch)
        
        if pitch_values:
            pitch_mean = float(np.mean(pitch_values))
            pitch_variance = float(np.std(pitch_values))
        else:
            pitch_mean = 0.0
            pitch_variance = 0.0
        
        # === 話速推定 (仮) ===
        # 実際の話速は文字起こし結果と組み合わせて計算
        # ここでは音声の有効時間から推定
        speech_duration = duration - pause_total
        # 日本語の平均話速: 約300文字/分
        estimated_speech_rate = 300.0  # デフォルト値
        
        logger.info(f"音響分析完了: 音量={average_volume:.1f}dB, ポーズ={pause_count}回")
        
        return {
            "speech_rate": round(estimated_speech_rate, 1),
            "average_volume": round(average_volume, 1),
            "volume_variance": round(volume_variance, 1),
            "pause_count": pause_count,
            "pause_total_duration": round(pause_total, 2),
            "pitch_mean": round(pitch_mean, 1),
            "pitch_variance": round(pitch_variance, 1),
            "duration": round(duration, 2),
            "speech_duration": round(speech_duration, 2)
        }
        
    except Exception as e:
        logger.error(f"音響分析エラー: {str(e)}", exc_info=True)
        return {
            "speech_rate": 0.0,
            "average_volume": 0.0,
            "volume_variance": 0.0,
            "pause_count": 0,
            "pause_total_duration": 0.0,
            "pitch_mean": 0.0,
            "pitch_variance": 0.0,
            "duration": 0.0,
            "speech_duration": 0.0,
            "error": str(e)
        }


def calculate_actual_speech_rate(text: str, duration: float) -> float:
    """
    実際の話速を計算
    
    Args:
        text: 文字起こしテキスト
        duration: 音声の長さ (秒)
    
    Returns:
        話速 (文字/分)
    """
    if duration <= 0:
        return 0.0
    
    char_count = len(text)
    minutes = duration / 60.0
    
    return round(char_count / minutes, 1)
