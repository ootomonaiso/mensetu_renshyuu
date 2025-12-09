"""
librosa を使用した音声分析
"""
import librosa
import numpy as np
from typing import Dict, List
import soundfile as sf


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
        # 音声ファイル読み込み
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # 全体分析
        overall_analysis = {
            "duration": len(y) / sr,
            "pitch_mean": self._analyze_pitch(y, sr),
            "volume_mean": self._analyze_volume(y),
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
    
    def _analyze_pitch(self, y: np.ndarray, sr: int) -> float:
        """
        ピッチ（音の高さ）分析
        
        Args:
            y: 音声データ
            sr: サンプリングレート
        
        Returns:
            平均ピッチ (Hz)
        """
        try:
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            # 有効なピッチのみ抽出（0でないもの）
            pitch_values = pitches[pitches > 0]
            if len(pitch_values) > 0:
                return float(np.mean(pitch_values))
            return 0.0
        except Exception as e:
            print(f"Pitch analysis error: {e}")
            return 0.0
    
    def _analyze_volume(self, y: np.ndarray) -> float:
        """
        音量分析
        
        Args:
            y: 音声データ
        
        Returns:
            平均音量 (dB)
        """
        try:
            # RMS (Root Mean Square) エネルギー
            rms = librosa.feature.rms(y=y)[0]
            # dBに変換
            db = librosa.amplitude_to_db(rms)
            return float(np.mean(db))
        except Exception as e:
            print(f"Volume analysis error: {e}")
            return 0.0
    
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
        話者別の音声分析
        
        Args:
            audio_path: 音声ファイルパス
            segments: 話者分離済みセグメント
        
        Returns:
            話者別分析結果
        """
        # 音声ファイル読み込み
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # 話者ごとにグループ化
        speaker_data = {}
        for seg in segments:
            speaker = seg.get("speaker", "不明")
            if speaker not in speaker_data:
                speaker_data[speaker] = {
                    "segments": [],
                    "total_duration": 0,
                    "total_text": ""
                }
            
            speaker_data[speaker]["segments"].append(seg)
            speaker_data[speaker]["total_duration"] += (seg["end"] - seg["start"])
            speaker_data[speaker]["total_text"] += seg.get("text", "")
        
        # 各話者の分析
        results = {}
        for speaker, data in speaker_data.items():
            pitches = []
            volumes = []
            
            for seg in data["segments"]:
                start_sample = int(seg["start"] * sr)
                end_sample = int(seg["end"] * sr)
                segment_audio = y[start_sample:end_sample]
                
                if len(segment_audio) > 0:
                    # ピッチ分析
                    pitch = self._analyze_pitch(segment_audio, sr)
                    if pitch > 0:
                        pitches.append(pitch)
                    
                    # 音量分析
                    volume = self._analyze_volume(segment_audio)
                    volumes.append(volume)
            
            # 話速計算
            speaking_rate = self._analyze_speaking_rate(
                data["total_text"], 
                data["total_duration"]
            )
            
            results[speaker] = {
                "pitch_mean": float(np.mean(pitches)) if pitches else 0.0,
                "pitch_std": float(np.std(pitches)) if pitches else 0.0,
                "volume_mean": float(np.mean(volumes)) if volumes else 0.0,
                "volume_std": float(np.std(volumes)) if volumes else 0.0,
                "speaking_rate": speaking_rate,
                "total_duration": data["total_duration"],
                "segment_count": len(data["segments"])
            }
        
        return results
    
    def evaluate_interview_voice(self, analysis: Dict, speaker: str = "生徒") -> Dict:
        """
        面接に適した声かどうかを評価
        
        Args:
            analysis: 分析結果
            speaker: 評価対象話者
        
        Returns:
            評価結果
        """
        if speaker not in analysis.get("by_speaker", {}):
            return {"score": 0, "feedback": "データが不足しています"}
        
        data = analysis["by_speaker"][speaker]
        feedback = []
        score = 100
        
        # ピッチ評価（適度な高さが望ましい: 150-250 Hz）
        pitch = data["pitch_mean"]
        if 150 <= pitch <= 250:
            feedback.append("✓ 声の高さが適切です")
        elif pitch < 150:
            feedback.append("⚠ 声がやや低めです。もう少し明るいトーンを意識しましょう")
            score -= 10
        elif pitch > 250:
            feedback.append("⚠ 声がやや高めです。落ち着いたトーンを意識しましょう")
            score -= 10
        
        # 音量評価（適度な音量: -30 ~ -15 dB）
        volume = data["volume_mean"]
        if -30 <= volume <= -15:
            feedback.append("✓ 音量が適切です")
        elif volume < -30:
            feedback.append("⚠ 声が小さいです。もう少しはっきりと話しましょう")
            score -= 15
        elif volume > -15:
            feedback.append("⚠ 声が大きすぎます。落ち着いて話しましょう")
            score -= 10
        
        # 話速評価（適度な速さ: 250-350 文字/分）
        rate = data["speaking_rate"]
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
