"""faster-whisper / librosa / Gemini 統合分析サービス"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from faster_whisper import WhisperModel
import librosa

from app.clients.supabase import get_supabase_client


class AudioAnalysisService:
    """音声分析サービス（文字起こし + 音響特徴抽出）"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        # faster-whisper モデル（small が精度と速度のバランス良好）
        self.whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
    
    def transcribe_audio(self, audio_path: str) -> dict[str, Any]:
        """
        音声文字起こし（faster-whisper）
        
        Returns:
            transcript: 全文
            transcript_with_timestamps: セグメントごとのタイムスタンプ付き
            detected_language: 検出言語
        """
        segments, info = self.whisper_model.transcribe(
            audio_path,
            language="ja",
            beam_size=5,
            vad_filter=True,  # 無音区間をスキップ
        )
        
        full_text = []
        timestamped_segments = []
        
        for segment in segments:
            full_text.append(segment.text)
            timestamped_segments.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            })
        
        return {
            "transcript": " ".join(full_text),
            "transcript_with_timestamps": json.dumps(timestamped_segments, ensure_ascii=False),
            "detected_language": info.language,
        }
    
    def analyze_acoustic_features(self, audio_path: str) -> dict[str, Any]:
        """
        音響特徴抽出（librosa）
        
        Returns:
            avg_speech_rate: 話速（文字数/秒）
            avg_volume_db: 平均音量
            avg_pitch_hz: 平均ピッチ
            pause_count: ポーズ回数（無音区間）
            filler_count: フィラー推定回数（"えー"等）
        """
        # 音声読み込み
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # 音量（RMS）
        rms = librosa.feature.rms(y=y)[0]
        avg_volume_db = float(20 * np.log10(np.mean(rms) + 1e-6))
        
        # ピッチ（f0）推定
        f0, voiced_flag, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr
        )
        avg_pitch_hz = float(np.nanmean(f0)) if not np.isnan(f0).all() else 0.0
        
        # ポーズ検出（無音区間）
        intervals = librosa.effects.split(y, top_db=30)
        pause_count = len(intervals) - 1 if len(intervals) > 1 else 0
        
        # TODO: フィラー検出はWhisperのテキストから「えー」「あのー」等をカウント
        filler_count = 0
        
        # 話速（文字数/秒）は文字起こし結果と組み合わせて計算
        avg_speech_rate = 0.0  # 後でセッションサービスから更新
        
        return {
            "avg_speech_rate": avg_speech_rate,
            "avg_volume_db": round(avg_volume_db, 2),
            "avg_pitch_hz": round(avg_pitch_hz, 2),
            "pause_count": pause_count,
            "filler_count": filler_count,
        }
    
    def save_audio_analysis(
        self, session_id: str, transcript_data: dict, acoustic_data: dict
    ) -> None:
        """
        文字起こしと音響特徴をDBに保存
        
        - interview_sessions に transcript 保存
        - audio_analysis に音響特徴保存
        """
        # トランスクリプト文字数から話速計算
        transcript = transcript_data["transcript"]
        char_count = len(transcript.replace(" ", ""))
        
        # セッションからduration取得
        session_res = (
            self.supabase.table("interview_sessions")
            .select("duration")
            .eq("id", session_id)
            .single()
            .execute()
        )
        duration = session_res.data.get("duration", 60)
        avg_speech_rate = round(char_count / (duration / 60), 2) if duration > 0 else 0.0
        
        # interview_sessions に transcript 保存
        self.supabase.table("interview_sessions").update({
            "transcript": transcript_data["transcript"],
            "status": "completed",
        }).eq("id", session_id).execute()
        
        # audio_analysis に音響特徴保存
        acoustic_data["avg_speech_rate"] = avg_speech_rate
        self.supabase.table("audio_analysis").insert({
            "session_id": session_id,
            **acoustic_data,
        }).execute()
