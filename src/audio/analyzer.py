"""
librosa を使用した音声分析（感情分析機能付き）
"""
import librosa
import numpy as np
from typing import Dict, List, Tuple
import soundfile as sf
import warnings


class AudioAnalyzer:
    def __init__(self, sample_rate: int = 16000):
        """
        Args:
            sample_rate: サンプリングレート
        """
        self.sample_rate = sample_rate
    
    def analyze(self, audio_path: str, segments: List[Dict] = None) -> Dict:
        """
        音声ファイルの総合分析
        
        Args:
            audio_path: 音声ファイルパス
            segments: 話者分離済みセグメント（あれば）
        
        Returns:
            分析結果辞書
        """
        # 音声ファイル読み込み（soundfileを優先的に使用）
        try:
            y, sr = sf.read(audio_path)
            # ステレオの場合はモノラルに変換
            if len(y.shape) > 1:
                y = y.mean(axis=1)
            # サンプリングレートが異なる場合はリサンプリング
            if sr != self.sample_rate:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate
        except Exception as e:
            # フォールバック: librosaで読み込み（警告を抑制）
            warnings.filterwarnings('ignore', category=FutureWarning)
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # 全体分析
        overall_analysis = {
            "duration": len(y) / sr,
            "speaking_rate": None  # セグメントから計算
        }
        
        # 話者別分析
        speaker_analysis = {}
        if segments:
            speaker_analysis = self._analyze_by_speaker(audio_path, segments)
        
        return {
            "overall": overall_analysis,
            "by_speaker": speaker_analysis
        }
    
    def _analyze_emotion(self, y: np.ndarray, sr: int) -> Dict[str, float]:
        """
        音声から感情を分析
        
        Args:
            y: 音声データ
            sr: サンプリングレート
        
        Returns:
            感情スコア辞書 (confidence, energy, stress)
        """
        try:
            # スペクトル重心（明るさ・自信度の指標）
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            centroid_mean = float(np.mean(spectral_centroid))
            centroid_std = float(np.std(spectral_centroid))
            
            # RMSエネルギー（活力・エネルギーの指標）
            rms = librosa.feature.rms(y=y)[0]
            energy_mean = float(np.mean(rms))
            energy_std = float(np.std(rms))
            
            # ゼロ交差率（緊張・ストレスの指標）
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            zcr_mean = float(np.mean(zcr))
            
            # 正規化してスコア化（0-100）
            confidence = min(100, (centroid_mean / 4000) * 100)  # 高いほど自信がある
            energy = min(100, (energy_mean * 1000) * 100)  # 高いほどエネルギッシュ
            stress = min(100, zcr_mean * 200)  # 高いほど緊張している
            
            return {
                "confidence": float(confidence),  # 自信度
                "energy": float(energy),  # 活力
                "stress": float(stress),  # 緊張度
                "calmness": float(100 - stress)  # 落ち着き度
            }
        except Exception as e:
            print(f"Emotion analysis error: {e}")
            return {
                "confidence": 50.0,
                "energy": 50.0,
                "stress": 50.0,
                "calmness": 50.0
            }
    
    def _analyze_speaking_rate(self, text: str, duration: float) -> float:
        """
        話速分析（文字数/分）
        
        Args:
            text: 発話テキスト
            duration: 発話時間（秒）
        
        Returns:
            話速（文字/分）
        """
        if duration == 0:
            return 0.0
        char_count = len(text.replace(" ", ""))
        return (char_count / duration) * 60
    
    def _analyze_by_speaker(self, audio_path: str, segments: List[Dict]) -> Dict:
        """
        話者別の音声分析（感情分析を含む）
        
        Args:
            audio_path: 音声ファイルパス
            segments: 話者分離済みセグメント
        
        Returns:
            話者別分析結果
        """
        # 音声ファイル読み込み
        try:
            y, sr = sf.read(audio_path)
            if len(y.shape) > 1:
                y = y.mean(axis=1)
            if sr != self.sample_rate:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.sample_rate)
                sr = self.sample_rate
        except:
            warnings.filterwarnings('ignore', category=FutureWarning)
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # 話者ごとにグループ化
        speaker_data = {}
        for seg in segments:
            speaker = seg.get("speaker", "不明")
            if speaker not in speaker_data:
                speaker_data[speaker] = {
                    "segments": [],
                    "total_duration": 0,
                    "total_text": "",
                    "emotion_timeline": []  # 時系列の感情データ
                }
            
            speaker_data[speaker]["segments"].append(seg)
            speaker_data[speaker]["total_duration"] += (seg["end"] - seg["start"])
            speaker_data[speaker]["total_text"] += seg.get("text", "")
        
        # 各話者の分析
        results = {}
        for speaker, data in speaker_data.items():
            emotion_timeline = []
            
            for seg in data["segments"]:
                start_sample = int(seg["start"] * sr)
                end_sample = int(seg["end"] * sr)
                segment_audio = y[start_sample:end_sample]
                
                if len(segment_audio) > 0:
                    # 感情分析
                    emotions = self._analyze_emotion(segment_audio, sr)
                    emotion_timeline.append({
                        "time": seg["start"],
                        "duration": seg["end"] - seg["start"],
                        **emotions
                    })
            
            # 話速計算
            speaking_rate = self._analyze_speaking_rate(
                data["total_text"], 
                data["total_duration"]
            )
            
            # 平均感情スコアを計算
            avg_emotions = {
                "confidence": 0.0,
                "energy": 0.0,
                "stress": 0.0,
                "calmness": 0.0
            }
            
            if emotion_timeline:
                for key in avg_emotions.keys():
                    avg_emotions[key] = float(np.mean([e[key] for e in emotion_timeline]))
            
            results[speaker] = {
                "speaking_rate": speaking_rate,
                "total_duration": data["total_duration"],
                "segment_count": len(data["segments"]),
                "emotion_timeline": emotion_timeline,  # 時系列データ
                "emotion_average": avg_emotions  # 平均値
            }
        
        return results
    
    def evaluate_interview_voice(self, analysis: Dict, speaker: str = "生徒") -> Dict:
        """
        面接に適した感情状態かどうかを評価
        
        Args:
            analysis: 分析結果
            speaker: 評価対象話者
        
        Returns:
            評価結果
        """
        if speaker not in analysis.get("by_speaker", {}):
            return {"score": 0, "feedback": "データが不足しています"}
        
        data = analysis["by_speaker"][speaker]
        emotions = data.get("emotion_average", {})
        feedback = []
        score = 100
        
        # 自信度評価（50-80が適切）
        confidence = emotions.get("confidence", 50)
        if 50 <= confidence <= 80:
            feedback.append("✓ 適度な自信が感じられます")
        elif confidence < 50:
            feedback.append("⚠ 声に自信が感じられません。もう少し明るく話しましょう")
            score -= 15
        else:
            feedback.append("⚠ やや自信過剰に聞こえます。謙虚さを意識しましょう")
            score -= 10
        
        # エネルギー評価（40-70が適切）
        energy = emotions.get("energy", 50)
        if 40 <= energy <= 70:
            feedback.append("✓ 適度な活力が感じられます")
        elif energy < 40:
            feedback.append("⚠ 活気が不足しています。もう少し元気よく話しましょう")
            score -= 15
        else:
            feedback.append("⚠ エネルギーが高すぎます。落ち着いて話しましょう")
            score -= 10
        
        # 緊張度評価（20-50が適切）
        stress = emotions.get("stress", 50)
        if 20 <= stress <= 50:
            feedback.append("✓ 適度な緊張感で話せています")
        elif stress > 50:
            feedback.append("⚠ 緊張が高いです。深呼吸をしてリラックスしましょう")
            score -= 20
        else:
            feedback.append("✓ リラックスして話せています")
        
        # 話速評価（250-350 文字/分）
        rate = data.get("speaking_rate", 0)
        if 250 <= rate <= 350:
            feedback.append("✓ 話す速さが適切です")
        elif rate < 250:
            feedback.append("⚠ 話す速さがゆっくりです。もう少しテンポよく話しましょう")
            score -= 10
        elif rate > 350:
            feedback.append("⚠ 話す速さが速いです。落ち着いてゆっくり話しましょう")
            score -= 15
        
        return {
            "score": max(0, score),
            "feedback": feedback,
            "details": data
        }


if __name__ == "__main__":
    # テスト用
    analyzer = AudioAnalyzer()
    print("AudioAnalyzer initialized successfully")
