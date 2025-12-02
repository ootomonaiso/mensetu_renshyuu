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
import cv2
import tempfile
import os

from backend.services.voice_emotion import analyze_voice_emotion
from backend.services.session_recorder import SessionRecorder

try:
    from backend.services.video_processors import PoseAnalyzer, EyeContactAnalyzer
    VIDEO_ANALYSIS_AVAILABLE = True
except ImportError:
    VIDEO_ANALYSIS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("video_processors が見つかりません。動画分析は無効化されます")

logger = logging.getLogger(__name__)


class RealtimeAnalyzer:
    """リアルタイム分析を管理するクラス"""
    
    def __init__(self, session_id: str, recorder: Optional[SessionRecorder] = None):
        self.session_id = session_id
        self.transcription_buffer: List[str] = []
        self.emotion_history: List[Dict[str, Any]] = []
        self.keywords_detected: set = set()
        self.audio_chunks: List[bytes] = []
        self.start_time = datetime.now()
        self.total_audio_duration = 0.0
        
        # 動画分析プロセッサ（利用可能な場合のみ）
        self.enable_realtime_video_analysis = False  # 映像解析はレポート出力時に実施

        if VIDEO_ANALYSIS_AVAILABLE and self.enable_realtime_video_analysis:
            self.pose_analyzer = PoseAnalyzer()
            self.eye_contact_analyzer = EyeContactAnalyzer()
        else:
            self.pose_analyzer = None
            self.eye_contact_analyzer = None

        self.session_recorder = recorder
        self.recording_info: Dict[str, Any] = {}
        self._recording_finalized = False
        
    async def analyze_audio_chunk(self, audio_data: bytes) -> Dict[str, Any]:
        """
        音声チャンクをリアルタイム分析
        
        Args:
            audio_data: 音声バイナリデータ
            
        Returns:
            分析結果（文字起こし、感情スコア、キーワード）
        """
        try:
            # 音声チャンクを保存（ログ + レポート用）
            self.audio_chunks.append(audio_data)
            if self.session_recorder:
                self.session_recorder.write_audio_chunk(audio_data)
            
            # 音声レベル計算
            audio_level = self._calculate_audio_level(audio_data)
            
            # 音声感情分析を実行（音声レベルが一定以上の場合のみ）
            emotion_result = {}
            if len(audio_data) > 1000 and audio_level > 5:  # 音声レベルが5以上の時のみ
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
                            "stability": int(emotion_analysis.get("voice_stability", 50)),
                            "volume": int(emotion_analysis.get("volume_score", 50)),
                            "speaking_rate": int(emotion_analysis.get("speaking_rate_score", 50)),
                            "pitch": int(emotion_analysis.get("pitch_score", 50)),
                        }
                        
                        # 感情履歴に追加
                        self.emotion_history.append({
                            "timestamp": datetime.now().isoformat(),
                            **emotion_result
                        })
                except Exception as e:
                    logger.warning(f"音声感情分析スキップ: {e}")
                    emotion_result = {
                        "confidence": 0,
                        "calmness": 0,
                        "stability": 0,
                        "volume": 0,
                        "speaking_rate": 0,
                        "pitch": 0,
                    }
            else:
                # データが少ない、または無音の場合は0
                emotion_result = {
                    "confidence": 0,
                    "calmness": 0,
                    "stability": 0,
                    "volume": 0,
                    "speaking_rate": 0,
                    "pitch": 0,
                }
            
            result = {
                "type": "audio_analysis",
                "timestamp": asyncio.get_event_loop().time(),
                "audio_level": audio_level,
                "emotion": emotion_result,
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
        映像フレームをリアルタイム分析（MediaPipe）
        
        Args:
            frame_data: 映像フレームのバイナリデータ
            
        Returns:
            分析結果（姿勢、視線）
        """
        try:
            # MediaPipe が利用可能な場合は実際に分析
            if self.session_recorder:
                try:
                    # 録画用に生フレームを保存
                    frame_array = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
                except Exception:
                    frame_array = None
                if frame_array is not None:
                    self.session_recorder.write_video_frame(frame_array)

            if self.enable_realtime_video_analysis and VIDEO_ANALYSIS_AVAILABLE and self.pose_analyzer and self.eye_contact_analyzer:
                # 並列処理で姿勢と視線を分析
                posture_task = asyncio.create_task(
                    self.pose_analyzer.analyze(frame_data)
                )
                eye_contact_task = asyncio.create_task(
                    self.eye_contact_analyzer.analyze(frame_data)
                )
                
                # 両方の完了を待つ
                posture_result, eye_contact_result = await asyncio.gather(
                    posture_task,
                    eye_contact_task,
                    return_exceptions=True
                )
                
                # エラーハンドリング
                if isinstance(posture_result, Exception):
                    logger.error(f"姿勢分析エラー: {posture_result}")
                    posture_result = {"score": 75, "feedback": "分析中..."}
                
                if isinstance(eye_contact_result, Exception):
                    logger.error(f"視線分析エラー: {eye_contact_result}")
                    eye_contact_result = {"score": 70, "feedback": "分析中..."}
                
                result = {
                    "type": "video_analysis",
                    "timestamp": asyncio.get_event_loop().time(),
                    "posture": posture_result,
                    "eye_contact": eye_contact_result,
                }
            else:
                # リアルタイム解析は行わず、録画状況のみ返す
                result = {
                    "type": "video_recording",
                    "timestamp": asyncio.get_event_loop().time(),
                    "frame_captured": frame_array is not None,
                }
            
            return result
            
        except Exception as e:
            logger.error(f"映像分析エラー: {e}", exc_info=True)
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
            統計情報（平均感情スコア、録画情報など）
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # 平均スコア計算
        avg_confidence = 0
        avg_calmness = 0
        if self.emotion_history:
            avg_confidence = np.mean([e.get("confidence", 0) for e in self.emotion_history])
            avg_calmness = np.mean([e.get("calmness", 0) for e in self.emotion_history])
        
        summary = {
            "type": "summary",
            "session_id": self.session_id,
            "duration_seconds": duration,
            "average_confidence": float(avg_confidence),
            "average_calmness": float(avg_calmness),
            "emotion_sample_count": len(self.emotion_history),
            "audio_chunks_count": len(self.audio_chunks),
        }

        if self.recording_info:
            summary["recordings"] = self.recording_info

        return summary
    
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
            "recordings": self.recording_info,
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

    async def finalize_session(self) -> Dict[str, Any]:
        """Close recorders safely (idempotent)."""
        if self._recording_finalized:
            return self.recording_info

        if self.session_recorder:
            self.recording_info = await asyncio.to_thread(self.session_recorder.finalize)

        self._recording_finalized = True
        return self.recording_info
