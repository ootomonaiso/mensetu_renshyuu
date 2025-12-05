"""
音声処理サービス
faster-whisper + librosa + pyannote.audio で文字起こし・音響分析・話者分離
"""
import logging
import numpy as np
import wave
from pathlib import Path
from typing import Dict, Any, Optional, List
from faster_whisper import WhisperModel
import librosa
import torch
from pyannote.audio import Pipeline

logger = logging.getLogger(__name__)
class AudioProcessor:
    """音声処理クラス"""
    
    def __init__(self, model_size: str = "base", enable_diarization: bool = True):
        """
        Args:
            model_size: Whisperモデルサイズ (tiny, base, small, medium, large)
            enable_diarization: 話者分離を有効にするか
        """
        logger.info(f"Whisperモデルをロード中: {model_size}")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        logger.info("Whisperモデルロード完了")
        
        # 話者分離パイプライン (遅延ロード)
        self.diarization_pipeline = None
        self.enable_diarization = enable_diarization
        if enable_diarization:
            try:
                logger.info("話者分離モデルをロード中...")
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=None  # 公開モデル使用
                )
                logger.info("話者分離モデルロード完了")
            except Exception as e:
                logger.warning(f"話者分離モデルのロードに失敗: {e}")
                logger.warning("話者分離なしで続行します")
                self.enable_diarization = False
    
    def diarize_speakers(self, audio_path: Path) -> List[Dict[str, Any]]:
        """
        話者分離を実行
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            [{
                "start": 開始時刻(秒),
                "end": 終了時刻(秒),
                "speaker": "SPEAKER_00" or "SPEAKER_01"
            }, ...]
        """
        if not self.enable_diarization or self.diarization_pipeline is None:
            logger.warning("話者分離が無効です")
            return []
        
        logger.info(f"話者分離開始: {audio_path}")
        
        try:
            diarization = self.diarization_pipeline(str(audio_path))
            
            speaker_segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                speaker_segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })
            
            logger.info(f"話者分離完了: {len(speaker_segments)}セグメント, {len(set(s['speaker'] for s in speaker_segments))}話者")
            return speaker_segments
            
        except Exception as e:
            logger.error(f"話者分離エラー: {e}", exc_info=True)
            return []
    
    def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        """
        音声ファイルを文字起こし (話者分離付き)
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            {
                "text": "文字起こしテキスト",
                "segments": [...],
                "language": "ja",
                "speakers": [...]  # 話者分離結果
            }
        """
        logger.info(f"文字起こし開始: {audio_path}")
        
        # Whisper 文字起こし
        segments, info = self.model.transcribe(
            str(audio_path),
            language="ja",
            beam_size=5,
            vad_filter=True
        )
        
        full_text = ""
        segment_list = []
        
        for segment in segments:
            full_text += segment.text + " "
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "speaker": None  # 後で割り当て
            })
        
        logger.info(f"文字起こし完了: {len(segment_list)}セグメント")
        
        # 話者分離
        speaker_segments = self.diarize_speakers(audio_path)
        
        # セグメントに話者を割り当て
        if speaker_segments:
            segment_list = self._assign_speakers(segment_list, speaker_segments)
        
        return {
            "text": full_text.strip(),
            "segments": segment_list,
            "language": info.language,
            "duration": info.duration,
            "speakers": speaker_segments
        }
    
    def _assign_speakers(self, 
                        transcript_segments: List[Dict],
                        speaker_segments: List[Dict]) -> List[Dict]:
        """
        文字起こしセグメントに話者を割り当て
        
        Args:
            transcript_segments: Whisperの文字起こしセグメント
            speaker_segments: pyannoteの話者分離セグメント
            
        Returns:
            話者が割り当てられたセグメント
        """
        for t_seg in transcript_segments:
            t_start = t_seg["start"]
            t_end = t_seg["end"]
            t_mid = (t_start + t_end) / 2
            
            # 中間時刻が含まれる話者セグメントを探す
            for s_seg in speaker_segments:
                if s_seg["start"] <= t_mid <= s_seg["end"]:
                    t_seg["speaker"] = s_seg["speaker"]
                    break
        
        return transcript_segments
    
    def analyze_audio(self, audio_path: Path) -> Dict[str, Any]:
        """
        音響特徴を分析（VoiceMind風の声域分析含む）
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            {
                "speech_rate": 話速(文字数/分),
                "average_volume": 平均音量(dB),
                "pause_count": ポーズ回数,
                "pitch_mean": 平均ピッチ(Hz),
                "pitch_std": ピッチ標準偏差,
                "jitter": ジッター(声の震え),
                "energy_variance": エネルギー分散,
                "voice_range": 声域分析,
                "timeline": タイムライン（1秒ごとの特徴）
            }
        """
        logger.info(f"音響分析開始: {audio_path}")
        
        # 音声読み込み
        y, sr = librosa.load(str(audio_path), sr=16000)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # 音量分析
        rms = librosa.feature.rms(y=y)[0]
        avg_volume = 20 * np.log10(np.mean(rms) + 1e-6)
        
        # ピッチ分析
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        pitch_mean = np.mean(pitch_values) if pitch_values else 0
        pitch_std = np.std(pitch_values) if pitch_values else 0
        
        # ジッター計算 (ピッチ変動)
        jitter = (pitch_std / pitch_mean * 100) if pitch_mean > 0 else 0
        
        # エネルギー分散
        energy = np.sum(y ** 2)
        energy_variance = np.var(rms)
        
        # ポーズ検出 (音量が閾値以下の区間)
        threshold = np.mean(rms) * 0.3
        is_silence = rms < threshold
        pause_count = np.sum(np.diff(is_silence.astype(int)) == 1)
        
        # 声域分析（VoiceMind風）
        voice_range = self._analyze_voice_range(pitch_values)
        
        result = {
            "duration": float(duration),
            "average_volume": float(avg_volume),
            "pause_count": int(pause_count),
            "pitch_mean": float(pitch_mean),
            "pitch_std": float(pitch_std),
            "jitter": float(jitter),
            "energy_variance": float(energy_variance),
            "voice_range": voice_range
        }
        
        logger.info(f"音響分析完了: 音量={avg_volume:.1f}dB, ポーズ={pause_count}回, 声域={voice_range['dominant']}")
        
        return result
    
    def _analyze_voice_range(self, pitch_values: List[float]) -> Dict[str, Any]:
        """
        声域を分析（低音域・中音域・高音域の割合）
        
        Args:
            pitch_values: ピッチ値のリスト
            
        Returns:
            {
                "low": 低音域の割合 (%),
                "mid": 中音域の割合 (%),
                "high": 高音域の割合 (%),
                "dominant": 支配的な声域
            }
        """
        if not pitch_values:
            return {"low": 0, "mid": 0, "high": 0, "dominant": "不明"}
        
        pitch_array = np.array(pitch_values)
        
        # 声域の閾値（一般的な日本語話者の範囲）
        # 男性: 80-200Hz, 女性: 150-350Hz を基準に設定
        low_threshold = 150  # Hz
        high_threshold = 250  # Hz
        
        low_count = np.sum(pitch_array < low_threshold)
        high_count = np.sum(pitch_array > high_threshold)
        mid_count = len(pitch_array) - low_count - high_count
        
        total = len(pitch_array)
        low_pct = (low_count / total * 100) if total > 0 else 0
        mid_pct = (mid_count / total * 100) if total > 0 else 0
        high_pct = (high_count / total * 100) if total > 0 else 0
        
        # 支配的な声域を判定
        dominant = "中音域"
        if low_pct > mid_pct and low_pct > high_pct:
            dominant = "低音域"
        elif high_pct > mid_pct and high_pct > low_pct:
            dominant = "高音域"
        
        return {
            "low": round(low_pct, 1),
            "mid": round(mid_pct, 1),
            "high": round(high_pct, 1),
            "dominant": dominant
        }
    
    def analyze_voice_quality(self, audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        声質の多次元分析（VoiceMind風12軸分析）
        
        Args:
            audio_features: analyze_audio() の結果
            
        Returns:
            {
                "dimensions": 12次元の分析結果,
                "summary": 総合評価
            }
        """
        jitter = audio_features["jitter"]
        pitch_mean = audio_features["pitch_mean"]
        pitch_std = audio_features["pitch_std"]
        energy_var = audio_features["energy_variance"]
        pause_count = audio_features["pause_count"]
        duration = audio_features["duration"]
        voice_range = audio_features.get("voice_range", {})
        
        # VoiceMind風の12軸分析
        dimensions = {}
        
        # 1. 社会性: 声の明瞭さと安定性
        social = 70 - int(jitter * 5) + min(20, int(pause_count / max(duration, 1) * 15))
        dimensions["social"] = max(0, min(100, social))
        
        # 2. 行動性: エネルギーの高さ
        action = min(100, int(energy_var * 300 + 40))
        dimensions["action"] = max(0, min(100, action))
        
        # 3. 感情: ピッチ変動の豊かさ
        emotion = min(100, int(pitch_std / 10 * 50 + 30))
        dimensions["emotion"] = max(0, min(100, emotion))
        
        # 4. 本能: 低音域の使用率
        instinct = int(voice_range.get("low", 30) * 1.5)
        dimensions["instinct"] = max(0, min(100, instinct))
        
        # 5. 存在感: ピッチの高さと安定性
        presence = min(100, int((pitch_mean / 250) * 60 + (100 - jitter * 5)))
        dimensions["presence"] = max(0, min(100, presence))
        
        # 6. 自己表現: 中音域の使用率
        self_expr = int(voice_range.get("mid", 40) * 1.3)
        dimensions["self_expression"] = max(0, min(100, self_expr))
        
        # 7. 同調性: 声の柔らかさ（低ジッター）
        harmony = 100 - min(100, int(jitter * 8))
        dimensions["harmony"] = max(0, min(100, harmony))
        
        # 8. 調和: エネルギーの安定性
        balance = 100 - min(100, int(energy_var * 800))
        dimensions["balance"] = max(0, min(100, balance))
        
        # 9. 順応性: ポーズの適切さ
        adapt = min(100, 50 + int(pause_count / max(duration, 1) * 30))
        dimensions["adaptation"] = max(0, min(100, adapt))
        
        # 10. 思考性: 高音域の使用率
        thinking = int(voice_range.get("high", 20) * 1.8)
        dimensions["thinking"] = max(0, min(100, thinking))
        
        # 11. 分析性: ピッチの精密さ（低変動）
        analysis = 100 - min(100, int(pitch_std / 5))
        dimensions["analysis"] = max(0, min(100, analysis))
        
        # 12. 感覚性: 全体的な声質の豊かさ
        sensation = int((dimensions["emotion"] + dimensions["presence"]) / 2)
        dimensions["sensation"] = max(0, min(100, sensation))
        
        # 総合評価
        avg_score = sum(dimensions.values()) / len(dimensions)
        dominant = max(dimensions.items(), key=lambda x: x[1])
        
        summary = {
            "average": round(avg_score, 1),
            "dominant_trait": dominant[0],
            "dominant_score": dominant[1],
            "personality_type": self._determine_personality_type(dimensions)
        }
        
        return {
            "dimensions": dimensions,
            "summary": summary
        }
    
    def _determine_personality_type(self, dimensions: Dict[str, int]) -> str:
        """
        声質から性格タイプを推定
        """
        social = dimensions.get("social", 0)
        emotion = dimensions.get("emotion", 0)
        thinking = dimensions.get("thinking", 0)
        harmony = dimensions.get("harmony", 0)
        
        if social > 70 and emotion > 60:
            return "外向的・感情豊か"
        elif thinking > 70 and harmony > 60:
            return "論理的・調和型"
        elif emotion > 70 and harmony < 50:
            return "情熱的・直感型"
        elif social < 50 and thinking > 60:
            return "内向的・分析型"
        else:
            return "バランス型"
