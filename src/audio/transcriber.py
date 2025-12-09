"""
Whisper を使用した音声文字起こし
"""
import whisper
import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


class Transcriber:
    def __init__(self, model_name: str = None):
        """
        Args:
            model_name: Whisperモデル名 (tiny, base, small, medium, large)
        """
        self.model_name = model_name or os.getenv("WHISPER_MODEL", "base")
        print(f"Loading Whisper model: {self.model_name}")
        self.model = whisper.load_model(self.model_name)
    
    def transcribe(self, audio_path: str, language: str = "ja") -> Dict:
        """
        音声ファイルを文字起こし
        
        Args:
            audio_path: 音声ファイルパス
            language: 言語コード (デフォルト: ja)
        
        Returns:
            文字起こし結果 (text, segments含む)
        """
        print(f"Transcribing: {audio_path}")
        result = self.model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False
        )
        return result
    
    def get_segments_with_timestamps(self, result: Dict) -> List[Dict]:
        """
        タイムスタンプ付きセグメントを取得
        
        Args:
            result: transcribe() の結果
        
        Returns:
            セグメントリスト
        """
        segments = []
        for segment in result.get("segments", []):
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "speaker": None  # 話者分離後に設定
            })
        return segments
    
    def format_transcript(self, segments: List[Dict]) -> str:
        """
        セグメントをフォーマットされたテキストに変換
        
        Args:
            segments: セグメントリスト
        
        Returns:
            フォーマット済みテキスト
        """
        lines = []
        for seg in segments:
            speaker = seg.get("speaker", "不明")
            start_time = self._format_time(seg["start"])
            text = seg["text"]
            lines.append(f"[{start_time}] {speaker}: {text}")
        return "\n".join(lines)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """秒を MM:SS 形式に変換"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # テスト用
    transcriber = Transcriber()
    print("Transcriber initialized successfully")
