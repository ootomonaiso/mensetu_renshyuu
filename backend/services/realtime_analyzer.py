"""
リアルタイム音声・映像分析サービス

音声ストリーム → リアルタイム文字起こし + 感情分析
映像フレーム → 姿勢・表情分析（Phase 4）
"""
import asyncio
import json
import logging
import io
from typing import Optional, Dict, Any, List
from datetime import datetime
import numpy as np

from backend.services.voice_emotion import analyze_voice_emotion

logger = logging.getLogger(__name__)


class RealtimeAnalyzer:
    """リアルタイム分析を管理するクラス"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.transcription_buffer: List[str] = []
        self.emotion_history: List[Dict[str, Any]] = []
        self.keywords_detected: set = set()
        self.audio_chunks: List[bytes] = []
        self.start_time = datetime.now()
        self.total_audio_duration = 0.0
        
    async def analyze_audio_chunk(self, audio_data: bytes) -> Dict[str, Any]:
        """
        音声チャンクをリアルタイム分析
        
        Args:
            audio_data: 音声バイナリデータ
            
        Returns:
            分析結果（文字起こし、感情スコア、キーワード）
        """
        try:
            # 音声チャンクを保存（後でレポート生成時に使用）
            self.audio_chunks.append(audio_data)
            
            # 音声レベル計算
            audio_level = self._calculate_audio_level(audio_data)
            
            # 音声感情分析を実行
            emotion_result = {}
            if len(audio_data) > 1000:  # 最低限のデータサイズチェック
                try:
                    # BytesIO でラップして soundfile で読めるようにする
                    emotion_analysis = await asyncio.to_thread(
                        analyze_voice_emotion, 
                        io.BytesIO(audio_data)
                    )
                    
                    if emotion_analysis:
                        emotion_result = {
                            "confidence": int(emotion_analysis.get("confidence_score", 50)),
                            "calmness": 100 - int(emotion_analysis.get("nervousness_score", 50)),
                            "energy": emotion_analysis.get("energy_mean", 0),
                            "pitch": emotion_analysis.get("pitch_mean", 0),
                        }
                        
                        # 感情履歴に追加
                        self.emotion_history.append({
                            "timestamp": datetime.now().isoformat(),
                            **emotion_result
                        })
                except Exception as e:
                    logger.warning(f"音声感情分析スキップ: {e}")
                    emotion_result = {
                        "confidence": 70,
                        "calmness": 65,
                        "energy": 0,
                        "pitch": 0,
                    }
            else:
                # データが少ない場合はデフォルト値
                emotion_result = {
                    "confidence": 70,
                    "calmness": 65,
                    "energy": 0,
                    "pitch": 0,
                }
            
            result = {
                "type": "audio_analysis",
                "timestamp": asyncio.get_event_loop().time(),
                "audio_level": audio_level,
                "transcription": "",  # TODO: Whisper でリアルタイム文字起こし
                "emotion": emotion_result,
                "keywords": list(self.keywords_detected),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"音声分析エラー: {e}", exc_info=True)
            return {
                "type": "error",
                "message": str(e)
            }
    
    async def analyze_video_frame(self, frame_data: bytes) -> Dict[str, Any]:
        """
        映像フレームをリアルタイム分析（Phase 4）
        
        Args:
            frame_data: 映像フレームのバイナリデータ
            
        Returns:
            分析結果（姿勢、表情、視線）
        """
        try:
            # TODO: MediaPipe で姿勢・表情分析
            # 現在はダミー実装
            
            result = {
                "type": "video_analysis",
                "timestamp": asyncio.get_event_loop().time(),
                "posture": {
                    "score": 80,
                    "feedback": "良好な姿勢です",
                },
                "eye_contact": {
                    "score": 70,
                    "feedback": "適度な視線が保たれています",
                },
                "expression": {
                    "type": "neutral",
                    "confidence": 0.8,
                },
            }
            
            return result
            
        except Exception as e:
            logger.error(f"映像分析エラー: {e}")
            return {
                "type": "error",
                "message": str(e)
            }
    
    def _calculate_audio_level(self, audio_data: bytes) -> float:
        """
        音声レベルを計算（0-100）
        
        Args:
            audio_data: 音声バイナリ
            
        Returns:
            音声レベル（0-100）
        """
        try:
            # Int16 として解釈して RMS 計算
            samples = np.frombuffer(audio_data, dtype=np.int16)
            if len(samples) == 0:
                return 0.0
            
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            # 正規化（0-32768 → 0-100）
            level = min(100, (rms / 32768.0) * 100)
            return float(level)
            
        except Exception as e:
            logger.error(f"音声レベル計算エラー: {e}")
            return 0.0
    
    async def get_summary(self) -> Dict[str, Any]:
        """
        セッション全体のサマリーを取得
        
        Returns:
            統計情報（平均感情スコア、キーワード一覧など）
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # 平均スコア計算
        avg_confidence = 0
        avg_calmness = 0
        if self.emotion_history:
            avg_confidence = np.mean([e.get("confidence", 0) for e in self.emotion_history])
            avg_calmness = np.mean([e.get("calmness", 0) for e in self.emotion_history])
        
        return {
            "type": "summary",
            "session_id": self.session_id,
            "duration_seconds": duration,
            "total_transcription": " ".join(self.transcription_buffer),
            "keywords": list(self.keywords_detected),
            "average_confidence": float(avg_confidence),
            "average_calmness": float(avg_calmness),
            "emotion_sample_count": len(self.emotion_history),
            "audio_chunks_count": len(self.audio_chunks),
        }
    
    async def generate_report(self, output_dir: str) -> Dict[str, str]:
        """
        セッションのMarkdownレポートを生成
        
        Args:
            output_dir: 出力ディレクトリパス
            
        Returns:
            レポートファイルパスとURL
        """
        from pathlib import Path
        from backend.services.report import generate_markdown_report
        
        summary = await self.get_summary()
        
        # レポート用データ構造を作成
        report_data = {
            "student_name": "リアルタイムセッション",
            "session_id": self.session_id,
            "timestamp": self.start_time.isoformat(),
            "duration": summary["duration_seconds"],
            "transcript": summary["total_transcription"] or "（音声データなし）",
            "audio_features": {
                "speech_rate": 0,  # TODO: 実装
                "pause_count": 0,
                "avg_pitch": 0,
            },
            "voice_emotion": {
                "confidence_score": summary["average_confidence"],
                "nervousness_score": 100 - summary["average_calmness"],
                "feedback": f"セッション中の平均自信度: {summary['average_confidence']:.1f}%",
            },
            "ai_analysis": {
                "keywords": summary["keywords"],
                "keigo_score": 0,
                "professionalism_score": summary["average_confidence"],
            },
        }
        
        # Markdownレポート生成
        report_path = Path(output_dir) / f"live_{self.session_id}.md"
        await asyncio.to_thread(
            generate_markdown_report,
            report_data,
            str(report_path)
        )
        
        return {
            "report_path": str(report_path),
            "report_url": f"/reports/live_{self.session_id}.md",
        }
