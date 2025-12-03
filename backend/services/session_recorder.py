from __future__ import annotations

import json
import wave
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np


class SessionRecorder:

    def __init__(
        self,
        session_id: str,
        base_dir: Path,
        *,
        sample_rate: int = 16_000,
        video_fps: int = 15,
    ) -> None:
        self.session_id = session_id
        self.sample_rate = sample_rate
        self.video_fps = video_fps

        self.session_dir = base_dir / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.audio_path = self.session_dir / "audio.wav"
        self.video_path = self.session_dir / "video.mp4"
        self.metadata_path = self.session_dir / "session.json"

        self._audio_writer: Optional[wave.Wave_write] = None
        self._video_writer: Optional[cv2.VideoWriter] = None
        self._video_size: Optional[tuple[int, int]] = None  # (width, height)

        self._audio_bytes_written = 0
        self._frame_count = 0
        self._closed = False
        self._metadata: Dict[str, Any] = {
            "session_id": session_id,
            "started_at": datetime.utcnow().isoformat(),
            "session_dir": str(self.session_dir),
        }

    # ------------------------------------------------------------------
    # Audio helpers
    # ------------------------------------------------------------------
    def write_audio_chunk(self, pcm_bytes: bytes) -> None:
        """Append raw PCM bytes (16-bit mono) into the WAV container."""
        if not pcm_bytes or self._closed:
            return

        if self._audio_writer is None:
            self._audio_writer = wave.open(str(self.audio_path), "wb")
            self._audio_writer.setnchannels(1)
            self._audio_writer.setsampwidth(2)  # 16-bit PCM
            self._audio_writer.setframerate(self.sample_rate)

        self._audio_writer.writeframes(pcm_bytes)
        self._audio_bytes_written += len(pcm_bytes)

    # ------------------------------------------------------------------
    # Video helpers
    # ------------------------------------------------------------------
    def write_video_frame(self, frame_bgr: np.ndarray) -> None:
        """Append a decoded BGR frame into the MP4 container."""
        if frame_bgr is None or frame_bgr.size == 0 or self._closed:
            return

        height, width = frame_bgr.shape[:2]
        frame_size = (width, height)

        if self._video_writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self._video_size = frame_size
            self._video_writer = cv2.VideoWriter(
                str(self.video_path), fourcc, float(self.video_fps), frame_size
            )

        # リサイズしてフレームサイズを揃える
        if self._video_size and frame_size != self._video_size:
            frame_bgr = cv2.resize(frame_bgr, self._video_size)

        if self._video_writer is not None:
            self._video_writer.write(frame_bgr)
            self._frame_count += 1

    # ------------------------------------------------------------------
    # Finalization
    # ------------------------------------------------------------------
    def finalize(self) -> Dict[str, Any]:
        """Close file handles and persist metadata to disk."""
        if self._closed:
            return self._metadata

        self._closed = True

        if self._audio_writer is not None:
            self._audio_writer.close()
            self._audio_writer = None

        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None

        audio_duration = 0.0
        if self._audio_bytes_written:
            audio_duration = self._audio_bytes_written / (self.sample_rate * 2)

        self._metadata.update(
            {
                "ended_at": datetime.utcnow().isoformat(),
                "audio_path": str(self.audio_path) if self._audio_bytes_written else None,
                "video_path": str(self.video_path) if self._frame_count else None,
                "audio_duration_seconds": audio_duration,
                "audio_bytes": self._audio_bytes_written,
                "video_frame_count": self._frame_count,
                "video_fps": self.video_fps,
            }
        )

        with open(self.metadata_path, "w", encoding="utf-8") as fp:
            json.dump(self._metadata, fp, ensure_ascii=False, indent=2)

        return self._metadata

    def snapshot(self) -> Dict[str, Any]:
        """Return current recording state without closing writers."""
        return {
            "session_dir": str(self.session_dir),
            "audio_path": str(self.audio_path) if self._audio_bytes_written else None,
            "video_path": str(self.video_path) if self._frame_count else None,
            "audio_bytes": self._audio_bytes_written,
            "video_frame_count": self._frame_count,
        }
