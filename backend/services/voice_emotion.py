"""
音声感情分析サービス (声の震え・感情検出)
"""
import librosa
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def analyze_voice_emotion(audio_path: str) -> Dict[str, Any]:
    """
    音声から感情状態を分析
    
    Args:
        audio_path: 音声ファイルパス
    
    Returns:
        {
            "confidence_score": 0-100 (自信度),
            "nervousness_score": 0-100 (緊張度),
            "voice_stability": 0-100 (声の安定性),
            "jitter": 声の震え (ms),
            "pitch_variance": ピッチの変動幅 (Hz),
            "energy_variance": エネルギーの変動,
            "speaking_rate_variance": 話速の変動
        }
    """
    try:
        # 音声ロード
        y, sr = librosa.load(audio_path, sr=None)
        
        logger.info("音声感情分析開始...")
        
        # === 1. ピッチ分析 (基本周波数 F0) ===
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if len(pitch_values) > 0:
            pitch_mean = float(np.mean(pitch_values))
            pitch_variance = float(np.std(pitch_values))
        else:
            pitch_mean = 0.0
            pitch_variance = 0.0
        
        # === 2. ジッター分析 (声の震え) ===
        # ピッチの周期的変動を検出
        if len(pitch_values) > 10:
            # 隣接フレーム間のピッチ差分
            pitch_diffs = np.diff(pitch_values)
            jitter = float(np.mean(np.abs(pitch_diffs)))
        else:
            jitter = 0.0
        
        # === 3. エネルギー分析 ===
        rms = librosa.feature.rms(y=y)[0]
        energy_variance = float(np.std(rms))
        
        # === 4. MFCC (メル周波数ケプストラム係数) ===
        # 声質の特徴を抽出
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_variance = float(np.mean(np.std(mfccs, axis=1)))
        
        # === 5. 話速の変動 ===
        # 発話区間を検出
        intervals = librosa.effects.split(y, top_db=40)
        
        if len(intervals) > 2:
            # 各区間の長さを計算
            interval_durations = [(end - start) / sr for start, end in intervals]
            speaking_rate_variance = float(np.std(interval_durations))
        else:
            speaking_rate_variance = 0.0
        
        # === スコア計算 ===
        
        # 自信度: ピッチが安定し、エネルギーが一定
        confidence_score = 50  # ベースライン
        
        if pitch_variance < 30:
            confidence_score += 20
        elif pitch_variance < 50:
            confidence_score += 10
        
        if energy_variance < 0.05:
            confidence_score += 15
        elif energy_variance < 0.1:
            confidence_score += 5
        
        if jitter < 5:
            confidence_score += 15
        
        confidence_score = min(100, max(0, confidence_score))
        
        # 緊張度: ピッチが不安定、声が震える、エネルギーが変動
        nervousness_score = 30  # ベースライン
        
        if pitch_variance > 50:
            nervousness_score += 25
        elif pitch_variance > 30:
            nervousness_score += 15
        
        if jitter > 10:
            nervousness_score += 20
        elif jitter > 5:
            nervousness_score += 10
        
        if energy_variance > 0.1:
            nervousness_score += 15
        
        nervousness_score = min(100, max(0, nervousness_score))
        
        # 声の安定性: 総合的な評価
        voice_stability = 100 - nervousness_score
        
        logger.info(f"音声感情分析完了: 自信度={confidence_score}, 緊張度={nervousness_score}")
        
        return {
            "confidence_score": int(confidence_score),
            "nervousness_score": int(nervousness_score),
            "voice_stability": int(voice_stability),
            "jitter": round(jitter, 2),
            "pitch_mean": round(pitch_mean, 1),
            "pitch_variance": round(pitch_variance, 1),
            "energy_variance": round(energy_variance, 3),
            "mfcc_variance": round(mfcc_variance, 3),
            "speaking_rate_variance": round(speaking_rate_variance, 3)
        }
        
    except Exception as e:
        logger.error(f"音声感情分析エラー: {str(e)}", exc_info=True)
        return {
            "confidence_score": 50,
            "nervousness_score": 50,
            "voice_stability": 50,
            "jitter": 0.0,
            "pitch_mean": 0.0,
            "pitch_variance": 0.0,
            "energy_variance": 0.0,
            "mfcc_variance": 0.0,
            "speaking_rate_variance": 0.0,
            "error": str(e)
        }


def get_emotion_feedback(emotion_data: Dict[str, Any]) -> str:
    """
    感情分析結果からフィードバックメッセージを生成
    
    Args:
        emotion_data: 感情分析結果
    
    Returns:
        フィードバックメッセージ
    """
    feedback = []
    
    confidence = emotion_data.get("confidence_score", 50)
    nervousness = emotion_data.get("nervousness_score", 50)
    jitter = emotion_data.get("jitter", 0)
    
    # 自信度のフィードバック
    if confidence > 70:
        feedback.append("✨ **自信を持って話せています!** 声のトーンが安定しており、説得力があります。")
    elif confidence > 50:
        feedback.append("👍 **適度な自信が感じられます。** もう少し声に力を入れると、さらに印象が良くなります。")
    else:
        feedback.append("💡 **もう少し自信を持ちましょう。** 練習を重ねて、自分の言葉に確信を持つことが大切です。")
    
    # 緊張度のフィードバック
    if nervousness > 70:
        feedback.append("😰 **緊張が高めです。** 深呼吸をして、リラックスしてから話すと良いでしょう。")
    elif nervousness > 50:
        feedback.append("😊 **やや緊張気味です。** 事前準備を十分にして、落ち着いて話しましょう。")
    else:
        feedback.append("😎 **リラックスして話せています!** この調子を維持しましょう。")
    
    # 声の震えのフィードバック
    if jitter > 10:
        feedback.append("🎤 **声が震えています。** ゆっくり深呼吸をして、落ち着いて話すことを意識しましょう。")
    elif jitter > 5:
        feedback.append("🎤 **声が少し不安定です。** リラックスして、安定したトーンで話すよう心がけましょう。")
    
    return "\n\n".join(feedback)
