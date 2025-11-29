"""
リアルタイム音声処理サービス
WebSocket経由で音声チャンクを受信 → 文字起こし → 分析
"""
import io
import logging
import asyncio
from typing import AsyncGenerator, Dict, Any
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa

from .transcription import get_whisper_model
from .ai_analysis import analyze_with_gemini
from .audio_analysis import analyze_audio_features
from .voice_emotion import analyze_voice_emotion

logger = logging.getLogger(__name__)


class RealtimeTranscriber:
    """リアルタイム文字起こし処理"""
    
    def __init__(self):
        self.model = get_whisper_model()
        self.buffer = bytearray()
        self.buffer_duration = 3.0  # 3秒ごとに処理
        self.sample_rate = 16000
        self.channels = 1
        self.accumulated_text = ""
        
    def add_audio_chunk(self, audio_data: bytes):
        """音声チャンクをバッファに追加"""
        self.buffer.extend(audio_data)
        
    def get_buffer_duration(self) -> float:
        """現在のバッファの長さ（秒）を取得"""
        # 16bit PCM想定
        num_samples = len(self.buffer) // 2
        return num_samples / self.sample_rate
    
    async def process_buffer(self) -> Dict[str, Any]:
        """
        バッファの音声を文字起こし + リアルタイム音響・感情分析
        
        Returns:
            {
                "text": "文字起こし結果",
                "duration": 3.2,
                "is_final": False,
                "audio_features": {...},  # 音響分析
                "voice_emotion": {...}    # 感情分析
            }
        """
        if len(self.buffer) < self.sample_rate * 2:  # 最低1秒必要
            return {
                "text": "", 
                "duration": 0, 
                "is_final": False,
                "audio_features": {},
                "voice_emotion": {}
            }
        
        try:
            # バッファを音声配列に変換
            audio_array = np.frombuffer(self.buffer, dtype=np.int16).astype(np.float32) / 32768.0
            
            # 一時ファイルに保存（faster-whisperの要件）
            temp_path = Path("output/temp_chunk.wav")
            sf.write(str(temp_path), audio_array, self.sample_rate)
            
            # === 並列処理: 文字起こし + 音響分析 + 感情分析 ===
            transcription_task = asyncio.to_thread(self._transcribe, str(temp_path))
            audio_analysis_task = asyncio.to_thread(analyze_audio_features, str(temp_path))
            emotion_analysis_task = asyncio.to_thread(analyze_voice_emotion, str(temp_path))
            
            text, audio_features, voice_emotion = await asyncio.gather(
                transcription_task,
                audio_analysis_task,
                emotion_analysis_task
            )
            
            # 累積テキストに追加
            if text.strip():
                self.accumulated_text += text + " "
            
            # バッファをクリア
            buffer_duration = self.get_buffer_duration()
            self.buffer.clear()
            
            logger.info(f"リアルタイム分析完了: text={text[:30]}... speech_rate={audio_features.get('speech_rate', 0):.1f} confidence={voice_emotion.get('confidence_score', 0):.1f}")
            
            return {
                "text": text,
                "accumulated_text": self.accumulated_text,
                "duration": buffer_duration,
                "is_final": False,
                "audio_features": audio_features,
                "voice_emotion": voice_emotion
            }
            
        except Exception as e:
            logger.error(f"リアルタイム処理エラー: {e}")
            return {
                "text": "", 
                "duration": 0, 
                "is_final": False, 
                "error": str(e),
                "audio_features": {},
                "voice_emotion": {}
            }
    
    def _transcribe(self, audio_path: str) -> str:
        """文字起こし実行（同期処理）"""
        segments, info = self.model.transcribe(
            audio_path,
            language="ja",
            beam_size=5,
            vad_filter=True
        )
        return " ".join([segment.text for segment in segments])
    
    async def finalize(self) -> Dict[str, Any]:
        """
        残りのバッファを処理して終了
        
        Returns:
            {
                "text": "最終文字起こし結果",
                "accumulated_text": "累積テキスト全文",
                "is_final": True
            }
        """
        # 残りのバッファを処理
        if len(self.buffer) > 0:
            await self.process_buffer()
        
        logger.info(f"文字起こし完了。総文字数: {len(self.accumulated_text)}")
        
        return {
            "text": self.accumulated_text,
            "accumulated_text": self.accumulated_text,
            "is_final": True
        }
    
    async def analyze_accumulated_text(self) -> Dict[str, Any]:
        """累積テキストをGeminiで分析"""
        if not self.accumulated_text.strip():
            return {
                "keywords": [],
                "keigo_feedback": "分析するテキストがありません",
                "confidence_score": 0,
                "nervousness_score": 0,
                "overall_impression": ""
            }
        
        try:
            # Gemini APIで分析（文字起こしテキストのみ使用）
            analysis = await asyncio.to_thread(
                analyze_with_gemini,
                self.accumulated_text,
                None  # audio_features は使用しない
            )
            
            logger.info(f"AI分析完了: {len(analysis.get('keywords', []))} キーワード抽出")
            return analysis
            
        except Exception as e:
            logger.error(f"AI分析エラー: {e}")
            return {
                "keywords": [],
                "keigo_feedback": f"分析エラー: {str(e)}",
                "confidence_score": 0,
                "nervousness_score": 0,
                "overall_impression": "",
                "error": str(e)
            }
