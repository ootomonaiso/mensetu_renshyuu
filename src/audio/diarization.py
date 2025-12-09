"""
pyannote.audio を使用した話者分離
"""
# torchaudio 2.9+ との互換性のためのパッチ
import torchaudio
if not hasattr(torchaudio, 'set_audio_backend'):
    # set_audio_backend は torchaudio 2.9 で削除されたので、ダミー関数を追加
    torchaudio.set_audio_backend = lambda x: None

from pyannote.audio import Pipeline
import torch
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()


class Diarizer:
    def __init__(self, hf_token: str = None):
        """
        Args:
            hf_token: HuggingFace トークン
        """
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN")
        if not self.hf_token:
            raise ValueError("HuggingFace token is required. Set HUGGINGFACE_TOKEN in .env")
        
        print("Loading pyannote.audio pipeline...")
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.hf_token
        )
        
        # GPU使用可能ならGPUを使用
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
            print("Using GPU for diarization")
        else:
            print("Using CPU for diarization")
    
    def diarize(self, audio_path: str, num_speakers: int = 2) -> List[Dict]:
        """
        音声ファイルの話者分離を実行
        
        Args:
            audio_path: 音声ファイルパス
            num_speakers: 話者数
        
        Returns:
            話者分離結果のリスト
        """
        print(f"Diarizing: {audio_path}")
        
        # 話者分離実行
        diarization = self.pipeline(
            audio_path,
            num_speakers=num_speakers
        )
        
        # 結果を整形
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        
        return segments
    
    def assign_speakers_to_segments(
        self, 
        transcription_segments: List[Dict], 
        diarization_segments: List[Dict]
    ) -> List[Dict]:
        """
        文字起こしセグメントに話者ラベルを割り当て
        
        Args:
            transcription_segments: Whisperの文字起こしセグメント
            diarization_segments: 話者分離セグメント
        
        Returns:
            話者ラベル付きセグメント
        """
        result_segments = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_mid = (trans_start + trans_end) / 2
            
            # 重複度が最も高い話者を選択
            best_speaker = "不明"
            max_overlap = 0
            
            for diar_seg in diarization_segments:
                diar_start = diar_seg["start"]
                diar_end = diar_seg["end"]
                
                # 重複時間を計算
                overlap_start = max(trans_start, diar_start)
                overlap_end = min(trans_end, diar_end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = diar_seg["speaker"]
            
            result_segments.append({
                "start": trans_start,
                "end": trans_end,
                "text": trans_seg["text"],
                "speaker": best_speaker
            })
        
        return result_segments
    
    def map_speakers_to_roles(self, segments: List[Dict]) -> List[Dict]:
        """
        話者ラベル（SPEAKER_00, SPEAKER_01）を役割（教師、生徒）にマッピング
        
        Args:
            segments: 話者ラベル付きセグメント
        
        Returns:
            役割マッピング済みセグメント
        """
        # 話者ごとの発話回数をカウント
        speaker_counts = {}
        for seg in segments:
            speaker = seg["speaker"]
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        # 最も発話が多い話者を教師と仮定（通常、教師の方が質問が多い）
        sorted_speakers = sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True)
        
        speaker_map = {}
        if len(sorted_speakers) >= 2:
            speaker_map[sorted_speakers[0][0]] = "教師"
            speaker_map[sorted_speakers[1][0]] = "生徒"
        elif len(sorted_speakers) == 1:
            speaker_map[sorted_speakers[0][0]] = "教師"
        
        # マッピング適用
        for seg in segments:
            seg["speaker"] = speaker_map.get(seg["speaker"], "不明")
        
        return segments


if __name__ == "__main__":
    # テスト用
    try:
        diarizer = Diarizer()
        print("Diarizer initialized successfully")
    except Exception as e:
        print(f"Error: {e}")
