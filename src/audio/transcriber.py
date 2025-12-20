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
            model_name: Whisperモデル名 (tiny, base, small, medium, large, large-v2, large-v3)
                       精度優先: medium以上を推奨
        """
        self.model_name = model_name or os.getenv("WHISPER_MODEL", "medium")
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
            verbose=False,
            # 精度向上のためのパラメータ
            beam_size=5,              # ビームサーチのビーム幅（デフォルト5、大きいほど精度UP）
            best_of=5,                # ベスト候補数（デフォルト5）
            temperature=0.0,          # 温度パラメータ（0で最も確実な予測）
            compression_ratio_threshold=2.4,  # 圧縮率の閾値
            logprob_threshold=-1.0,   # 対数確率の閾値
            no_speech_threshold=0.6,  # 無音判定の閾値
            condition_on_previous_text=True,  # 前のテキストを条件付け（文脈考慮）
            initial_prompt="これは日本語の面接の音声です。敬語や丁寧語が使われています。",  # 初期プロンプトで文脈を提供
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
