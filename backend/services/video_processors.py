"""
動画処理専用モジュール（並列処理用）

MediaPipe を使った骨格検出・姿勢分析
"""
import asyncio
import logging
import numpy as np
from typing import Dict, Any, Optional
import cv2

logger = logging.getLogger(__name__)

# グローバルモデルキャッシュ
_pose_detector = None
_face_mesh_detector = None


class PoseAnalyzer:
    """姿勢分析プロセッサ（MediaPipe Pose）"""
    
    def __init__(self):
        self.pose = None
        
    async def initialize(self):
        """MediaPipe Pose を初期化"""
        global _pose_detector
        if _pose_detector is None:
            try:
                import mediapipe as mp
                logger.info("MediaPipe Pose をロード中...")
                _pose_detector = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                logger.info("MediaPipe Pose のロード完了")
            except Exception as e:
                logger.warning(f"MediaPipe Pose のロード失敗: {e}")
                _pose_detector = None
        self.pose = _pose_detector
        
    async def analyze(self, frame_data: bytes) -> Dict[str, Any]:
        """
        映像フレームから姿勢を分析
        
        Args:
            frame_data: JPEG画像バイナリ
            
        Returns:
            姿勢スコアとフィードバック
        """
        if self.pose is None:
            await self.initialize()
            if self.pose is None:
                return self._default_posture()
        
        try:
            # JPEG → numpy array
            nparr = np.frombuffer(frame_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return self._default_posture()
            
            # RGB変換
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # MediaPipe で処理
            results = await asyncio.to_thread(self.pose.process, image_rgb)
            
            if not results.pose_landmarks:
                return {
                    "score": 50,
                    "feedback": "姿勢を検出できませんでした",
                    "details": {}
                }
            
            # 骨格から姿勢を評価
            landmarks = results.pose_landmarks.landmark
            
            # 肩の水平度チェック
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            shoulder_angle = abs(left_shoulder.y - right_shoulder.y)
            
            # 背筋の真っすぐさチェック
            nose = landmarks[0]
            left_hip = landmarks[23]
            spine_alignment = abs(nose.x - left_hip.x)
            
            # スコア計算
            score = 100
            feedback_parts = []
            
            if shoulder_angle > 0.05:
                score -= 20
                feedback_parts.append("肩が傾いています")
            
            if spine_alignment > 0.1:
                score -= 15
                feedback_parts.append("背筋を伸ばしましょう")
            
            # 顔の位置チェック（前傾・後傾）
            if nose.z > 0:
                score -= 10
                feedback_parts.append("やや前傾姿勢です")
            
            score = max(0, min(100, score))
            
            if score >= 80:
                feedback = "✨ 姿勢が良好です！"
            elif score >= 60:
                feedback = "👍 まずまずの姿勢です。" + ("、".join(feedback_parts) if feedback_parts else "")
            else:
                feedback = "💡 姿勢を改善しましょう: " + "、".join(feedback_parts)
            
            return {
                "score": int(score),
                "feedback": feedback,
                "details": {
                    "shoulder_level": float(1 - shoulder_angle * 10),
                    "spine_alignment": float(1 - spine_alignment * 5),
                    "forward_lean": float(-nose.z) if nose.z < 0 else 0.0
                }
            }
            
        except Exception as e:
            logger.warning(f"姿勢分析エラー: {e}")
            return self._default_posture()
    
    def _default_posture(self) -> Dict[str, Any]:
        return {
            "score": 75,
            "feedback": "姿勢分析中...",
            "details": {}
        }


class EyeContactAnalyzer:
    """視線分析プロセッサ（MediaPipe Face Mesh）"""
    
    def __init__(self):
        self.face_mesh = None
        
    async def initialize(self):
        """MediaPipe Face Mesh を初期化"""
        global _face_mesh_detector
        if _face_mesh_detector is None:
            try:
                import mediapipe as mp
                logger.info("MediaPipe Face Mesh をロード中...")
                _face_mesh_detector = mp.solutions.face_mesh.FaceMesh(
                    static_image_mode=False,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                logger.info("MediaPipe Face Mesh のロード完了")
            except Exception as e:
                logger.warning(f"MediaPipe Face Mesh のロード失敗: {e}")
                _face_mesh_detector = None
        self.face_mesh = _face_mesh_detector
        
    async def analyze(self, frame_data: bytes) -> Dict[str, Any]:
        """
        映像フレームから視線を分析
        
        Args:
            frame_data: JPEG画像バイナリ
            
        Returns:
            視線スコアとフィードバック
        """
        if self.face_mesh is None:
            await self.initialize()
            if self.face_mesh is None:
                return self._default_eye_contact()
        
        try:
            # JPEG → numpy array
            nparr = np.frombuffer(frame_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return self._default_eye_contact()
            
            # RGB変換
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # MediaPipe で処理
            results = await asyncio.to_thread(self.face_mesh.process, image_rgb)
            
            if not results.multi_face_landmarks:
                return {
                    "score": 50,
                    "feedback": "顔を検出できませんでした",
                    "details": {}
                }
            
            # 虹彩の位置から視線方向を推定
            landmarks = results.multi_face_landmarks[0].landmark
            
            # 左目・右目の虹彩位置
            left_iris = landmarks[468]  # MediaPipe のランドマークインデックス
            right_iris = landmarks[473]
            
            # 目の中心からのズレを計算
            left_eye_center = landmarks[33]
            right_eye_center = landmarks[263]
            
            left_offset = abs(left_iris.x - left_eye_center.x)
            right_offset = abs(right_iris.x - right_eye_center.x)
            
            avg_offset = (left_offset + right_offset) / 2
            
            # スコア計算（カメラを見ているほど高い）
            score = max(0, min(100, int((1 - avg_offset * 5) * 100)))
            
            if score >= 80:
                feedback = "👁️ カメラをしっかり見ています"
            elif score >= 60:
                feedback = "👀 ほぼカメラを見ています"
            else:
                feedback = "💡 カメラを見るよう意識しましょう"
            
            return {
                "score": score,
                "feedback": feedback,
                "details": {
                    "gaze_offset": float(avg_offset),
                    "looking_away": avg_offset > 0.2
                }
            }
            
        except Exception as e:
            logger.warning(f"視線分析エラー: {e}")
            return self._default_eye_contact()
    
    def _default_eye_contact(self) -> Dict[str, Any]:
        return {
            "score": 70,
            "feedback": "視線分析中...",
            "details": {}
        }
