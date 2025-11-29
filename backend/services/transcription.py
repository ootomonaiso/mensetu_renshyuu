"""
音声文字起こしサービス (faster-whisper)
"""
from faster_whisper import WhisperModel
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Whisper モデル (グローバルで1回だけロード)
_model = None


def get_whisper_model() -> WhisperModel:
    """
    Whisper モデルを取得 (シングルトン)
    """
    global _model
    if _model is None:
        logger.info("Whisper モデルをロード中...")
        # base モデル (精度と速度のバランス)
        # 選択肢: tiny, base, small, medium, large-v2
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.info("Whisper モデルロード完了")
    return _model


def transcribe_audio(audio_path: str) -> Dict[str, Any]:
    """
    音声ファイルを文字起こし
    
    Args:
        audio_path: 音声ファイルパス
    
    Returns:
        {
            "text": 全文,
            "segments": [{"start": 0.0, "end": 5.2, "text": "こんにちは"}],
            "language": "ja",
            "duration": 120.5
        }
    """
    try:
        model = get_whisper_model()
        
        # 文字起こし実行
        segments, info = model.transcribe(
            audio_path,
            language="ja",  # 日本語指定
            beam_size=5,     # ビーム幅 (精度向上)
            vad_filter=True, # 無音区間除去
        )
        
        # セグメント収集
        segment_list = []
        full_text_parts = []
        
        for segment in segments:
            segment_data = {
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            }
            segment_list.append(segment_data)
            full_text_parts.append(segment.text.strip())
        
        full_text = " ".join(full_text_parts)
        
        logger.info(f"文字起こし完了: {len(full_text)} 文字, {len(segment_list)} セグメント")
        
        return {
            "text": full_text,
            "segments": segment_list,
            "language": info.language,
            "duration": info.duration if hasattr(info, 'duration') else None,
            "segment_count": len(segment_list)
        }
        
    except Exception as e:
        logger.error(f"文字起こしエラー: {str(e)}", exc_info=True)
        return {
            "text": "",
            "segments": [],
            "language": "ja",
            "duration": None,
            "segment_count": 0,
            "error": str(e)
        }
