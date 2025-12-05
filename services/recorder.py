"""
録音セッション管理
WebSocketから受信した音声データをWAVファイルに保存
"""
import wave
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class SessionRecorder:
    """録音セッション管理クラス"""
    
    def __init__(self, session_id: str, output_dir: Path):
        """
        Args:
            session_id: セッションID
            output_dir: 出力ディレクトリ
        """
        self.session_id = session_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_path = self.output_dir / f"{session_id}.wav"
        self.wav_file: Optional[wave.Wave_write] = None
        
        logger.info(f"セッションレコーダー初期化: {session_id}")
    
    def start(self, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2):
        """録音開始"""
        self.wav_file = wave.open(str(self.audio_path), 'wb')
        self.wav_file.setnchannels(channels)
        self.wav_file.setsampwidth(sample_width)
        self.wav_file.setframerate(sample_rate)
        
        logger.info(f"録音開始: {self.audio_path}")
    
    def write_chunk(self, audio_data: bytes):
        """音声チャンクを書き込み"""
        if self.wav_file:
            self.wav_file.writeframes(audio_data)
    
    def stop(self) -> Path:
        """録音停止してファイルパスを返す"""
        if self.wav_file:
            self.wav_file.close()
            self.wav_file = None
            
        logger.info(f"録音停止: {self.audio_path}")
        return self.audio_path
    
    def get_path(self) -> Path:
        """音声ファイルパスを取得"""
        return self.audio_path
