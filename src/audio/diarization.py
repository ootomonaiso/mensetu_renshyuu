"""
pyannote.audio を使用した話者分離
"""
import torch
import os
from typing import List, Dict
from dotenv import load_dotenv
import librosa
import soundfile as sf
import tempfile

# torchaudio 2.0+ 互換性対応: set_audio_backend が廃止されたため、ダミー関数を追加
import torchaudio
if not hasattr(torchaudio, 'set_audio_backend'):
    torchaudio.set_audio_backend = lambda x: None

# huggingface_hub 互換性対応: use_auth_token を token にマッピング
import huggingface_hub
original_hf_hub_download = huggingface_hub.hf_hub_download

def patched_hf_hub_download(*args, use_auth_token=None, token=None, **kwargs):
    """use_auth_token を token に変換するパッチ"""
    if use_auth_token is not None and token is None:
        token = use_auth_token
    return original_hf_hub_download(*args, token=token, **kwargs)

huggingface_hub.hf_hub_download = patched_hf_hub_download

from pyannote.audio import Pipeline

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
        # 環境変数でトークンを設定(huggingface_hub 新バージョン対応)
        os.environ["HF_TOKEN"] = self.hf_token
        
        # 新しいAPIではtokenパラメータを使用
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            token=self.hf_token  # use_auth_token から token に変更
        )
        
        # GPU使用可能ならGPUを使用
        if torch.cuda.is_available():
            self.pipeline.to(torch.device("cuda"))
            print("Using GPU for diarization")
        else:
            print("Using CPU for diarization")
    
    def diarize(self, audio_path: str, num_speakers: int = None, min_speakers: int = 1, max_speakers: int = 3) -> List[Dict]:
        """
        音声ファイルの話者分離を実行
        
        Args:
            audio_path: 音声ファイルパス
            num_speakers: 話者数（Noneの場合は自動検出）
            min_speakers: 最小話者数（自動検出時）
            max_speakers: 最大話者数（自動検出時）
        
        Returns:
            話者分離結果のリスト
        """
        print(f"Diarizing: {audio_path} (speakers: {num_speakers or 'auto'})")
        
        # 音声ファイルをlibrosaで読み込んで一時ファイルに保存
        # これによりフォーマットの問題を回避
        try:
            y, sr = librosa.load(audio_path, sr=16000)
            
            # 一時ファイルに保存
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                sf.write(tmp.name, y, sr)
                tmp_path = tmp.name
            
            # 話者分離実行
            if num_speakers is not None:
                # 話者数が指定されている場合
                diarization = self.pipeline(
                    tmp_path,
                    num_speakers=num_speakers
                )
            else:
                # 話者数を自動検出
                diarization = self.pipeline(
                    tmp_path,
                    min_speakers=min_speakers,
                    max_speakers=max_speakers
                )
            
            # 一時ファイル削除
            os.unlink(tmp_path)
            
        except Exception as e:
            print(f"Error in diarization: {e}")
            return []
        
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
    
    def map_speakers_to_roles(self, segments: List[Dict], teacher_first: bool = True) -> List[Dict]:
        """
        話者ラベル（SPEAKER_00, SPEAKER_01）を役割（教師、生徒）にマッピング
        
        Args:
            segments: 話者ラベル付きセグメント
            teacher_first: Trueの場合、最初に発話した人を教師とする（デフォルト）
        
        Returns:
            役割マッピング済みセグメント
        """
        if not segments:
            return segments
        
        # 話者ごとの統計情報を収集
        speaker_stats = {}
        for seg in segments:
            speaker = seg["speaker"]
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    "count": 0,
                    "total_duration": 0,
                    "first_appearance": seg["start"],
                    "texts": []
                }
            speaker_stats[speaker]["count"] += 1
            speaker_stats[speaker]["total_duration"] += seg["end"] - seg["start"]
            speaker_stats[speaker]["texts"].append(seg["text"])
        
        # マッピング戦略を選択
        speaker_map = {}
        sorted_speakers = sorted(speaker_stats.items(), key=lambda x: x[1]["first_appearance"])
        
        if len(sorted_speakers) >= 2:
            if teacher_first:
                # 最初に発話した人を教師とする（面接開始時の挨拶など）
                speaker_map[sorted_speakers[0][0]] = "教師"
                speaker_map[sorted_speakers[1][0]] = "生徒"
            else:
                # 発話回数が多い方を教師とする
                sorted_by_count = sorted(speaker_stats.items(), key=lambda x: x[1]["count"], reverse=True)
                speaker_map[sorted_by_count[0][0]] = "教師"
                speaker_map[sorted_by_count[1][0]] = "生徒"
        elif len(sorted_speakers) == 1:
            speaker_map[sorted_speakers[0][0]] = "教師"
        
        # その他の話者がいる場合
        for speaker in speaker_stats.keys():
            if speaker not in speaker_map:
                speaker_map[speaker] = f"話者{len(speaker_map) + 1}"
        
        # マッピング適用
        for seg in segments:
            seg["speaker"] = speaker_map.get(seg["speaker"], "不明")
        
        # 統計情報を出力
        print("\n=== 話者分離統計 ===")
        for orig_speaker, role in speaker_map.items():
            stats = speaker_stats[orig_speaker]
            print(f"{role}: 発話回数={stats['count']}, 総発話時間={stats['total_duration']:.1f}秒")
        
        return segments


if __name__ == "__main__":
    # テスト用
    try:
        diarizer = Diarizer()
        print("Diarizer initialized successfully")
    except Exception as e:
        print(f"Error: {e}")
