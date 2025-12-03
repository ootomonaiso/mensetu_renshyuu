"""
ビデオ分析サービス (表情・視線・姿勢)
Phase 4 実装完了: MediaPipe による高度な分析
"""
import cv2
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe が未インストールです。pip install mediapipe でインストールしてください")


def analyze_video(video_path: str) -> Dict[str, Any]:
    """
    ビデオから表情・視線・姿勢を分析 (Phase 4 完全実装)
    
    Args:
        video_path: ビデオファイルパス
    
    Returns:
        {
            "facial_expression": {...},  # 表情分析
            "eye_contact": {...},         # 視線追跡
            "posture": {...},             # 姿勢分析
            "gestures": {...}             # ジェスチャー検出
        }
    """
    if not MEDIAPIPE_AVAILABLE:
        logger.warning("MediaPipe が利用できないため、スタブデータを返します")
        return {
            "facial_expression": _analyze_facial_expression_stub(),
            "eye_contact": _analyze_eye_contact_stub(),
            "posture": _analyze_posture_stub(),
            "gestures": _analyze_gestures_stub(),
            "status": "MediaPipe 未インストール"
        }
    
    if not Path(video_path).exists():
        logger.error(f"ビデオファイルが見つかりません: {video_path}")
        return {
            "facial_expression": _analyze_facial_expression_stub(),
            "eye_contact": _analyze_eye_contact_stub(),
            "posture": _analyze_posture_stub(),
            "gestures": _analyze_gestures_stub(),
            "status": "ビデオファイルなし"
        }
    
    try:
        facial_expression = analyze_facial_expression_mediapipe(video_path)
        eye_contact = analyze_eye_contact_mediapipe(video_path)
        posture = analyze_posture_mediapipe(video_path)
        gestures = analyze_gestures_mediapipe(video_path)
        
        return {
            "facial_expression": facial_expression,
            "eye_contact": eye_contact,
            "posture": posture,
            "gestures": gestures,
            "status": "分析完了"
        }
    except Exception as e:
        logger.error(f"ビデオ分析エラー: {e}", exc_info=True)
        return {
            "facial_expression": _analyze_facial_expression_stub(),
            "eye_contact": _analyze_eye_contact_stub(),
            "posture": _analyze_posture_stub(),
            "gestures": _analyze_gestures_stub(),
            "status": f"エラー: {str(e)}"
        }


def _analyze_facial_expression_stub() -> Dict[str, Any]:
    """
    表情分析 (スタブ)
    
    実装予定:
    - MediaPipe Face Mesh で顔のランドマーク検出
    - 笑顔・緊張・困惑などの感情分類
    - 表情の変化を時系列で記録
    """
    return {
        "smile_frequency": 0,  # 笑顔の頻度 (回/分)
        "smile_duration": 0,   # 笑顔の持続時間 (秒)
        "tension_level": 0,    # 緊張レベル (0-100)
        "dominant_emotion": "neutral",  # 主な表情
        "emotion_timeline": []  # タイムスタンプ付き表情変化
    }


def _analyze_eye_contact_stub() -> Dict[str, Any]:
    """
    視線追跡 (スタブ)
    
    実装予定:
    - MediaPipe Face Detection で視線方向を推定
    - カメラ (面接官) を見ている時間を計測
    - 視線の逸らし方のパターン分析
    """
    return {
        "eye_contact_ratio": 0,      # アイコンタクト比率 (%)
        "eye_contact_frequency": 0,   # 視線を合わせる頻度 (回/分)
        "average_duration": 0,        # 平均持続時間 (秒)
        "looking_away_patterns": [],  # 視線を逸らすパターン
        "feedback": "カメラを見る時間を増やしましょう"
    }


def _analyze_posture_stub() -> Dict[str, Any]:
    """
    姿勢分析 (スタブ)
    
    実装予定:
    - MediaPipe Pose で身体のランドマーク検出
    - 猫背・前傾姿勢を検出
    - 姿勢の変化を時系列で記録
    """
    return {
        "posture_score": 0,          # 姿勢スコア (0-100)
        "slouching_detected": False,  # 猫背検出
        "leaning_forward": False,     # 前傾姿勢
        "body_stability": 0,          # 身体の安定性
        "posture_changes": [],        # 姿勢変化の記録
        "feedback": "背筋を伸ばして座りましょう"
    }


def _analyze_gestures_stub() -> Dict[str, Any]:
    """
    ジェスチャー検出 (スタブ)
    
    実装予定:
    - MediaPipe Hands で手の動きを追跡
    - 手を組む・髪を触るなどの癖を検出
    - ジェスチャーの種類と頻度を記録
    """
    return {
        "hand_gestures": [],           # 検出されたジェスチャー
        "fidgeting_count": 0,          # そわそわした動き (回)
        "hair_touching": 0,            # 髪を触る回数
        "hand_clasping": 0,            # 手を組む回数
        "inappropriate_gestures": [],  # 不適切なジェスチャー
        "feedback": "手の動きは自然です"
    }


# === Phase 4 実装: MediaPipe による分析 ===

def analyze_facial_expression_mediapipe(video_path: str) -> Dict[str, Any]:
    """
    MediaPipe Face Mesh で表情分析
    
    笑顔の頻度・持続時間、緊張レベルを検出
    """
    if not MEDIAPIPE_AVAILABLE:
        return _analyze_facial_expression_stub()
    
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    )
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _analyze_facial_expression_stub()
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    smile_frames = 0
    tension_scores = []
    emotion_timeline = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 5フレームごとに分析 (処理速度向上)
        if frame_count % 5 != 0:
            frame_count += 1
            continue
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # 口角の位置から笑顔判定 (landmark 61, 291: 口角)
            left_mouth = landmarks[61]
            right_mouth = landmarks[291]
            nose_tip = landmarks[1]
            
            # 笑顔スコア計算 (口角が上がっているか)
            mouth_height = (left_mouth.y + right_mouth.y) / 2
            smile_score = nose_tip.y - mouth_height
            
            if smile_score > 0.02:  # 閾値 (調整可能)
                smile_frames += 1
            
            # 緊張レベル (眉間の距離・表情の硬さ)
            eyebrow_left = landmarks[70]
            eyebrow_right = landmarks[300]
            eyebrow_distance = abs(eyebrow_right.x - eyebrow_left.x)
            tension = max(0, 100 - eyebrow_distance * 500)  # 眉が寄ると緊張
            tension_scores.append(tension)
            
            # タイムスタンプ付き記録
            timestamp = frame_count / fps
            if smile_score > 0.02:
                emotion_timeline.append({
                    "time": round(timestamp, 1),
                    "emotion": "smile",
                    "score": round(smile_score * 100, 1)
                })
        
        frame_count += 1
    
    cap.release()
    face_mesh.close()
    
    duration_seconds = total_frames / fps if fps > 0 else 0
    smile_frequency = (smile_frames / (duration_seconds / 60)) if duration_seconds > 60 else smile_frames
    smile_duration = (smile_frames / fps) if fps > 0 else 0
    avg_tension = np.mean(tension_scores) if tension_scores else 0
    
    return {
        "smile_frequency": round(smile_frequency, 1),
        "smile_duration": round(smile_duration, 1),
        "tension_level": round(avg_tension, 1),
        "dominant_emotion": "smile" if smile_frames > total_frames * 0.3 else "neutral",
        "emotion_timeline": emotion_timeline[:10]  # 最初の10イベント
    }


def analyze_eye_contact_mediapipe(video_path: str) -> Dict[str, Any]:
    """
    MediaPipe Face Detection で視線追跡
    
    カメラを見ている時間を計測
    """
    if not MEDIAPIPE_AVAILABLE:
        return _analyze_eye_contact_stub()
    
    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(
        model_selection=1,
        min_detection_confidence=0.5
    )
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _analyze_eye_contact_stub()
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    eye_contact_frames = 0
    looking_away_patterns = []
    frame_count = 0
    consecutive_looking_away = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 3 != 0:  # 3フレームごと
            frame_count += 1
            continue
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb_frame)
        
        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            
            # 顔の中心位置でカメラを見ているか判定
            face_center_x = bbox.xmin + bbox.width / 2
            face_center_y = bbox.ymin + bbox.height / 2
            
            # 画面中央を見ている (±0.2の範囲)
            looking_at_camera = (0.3 < face_center_x < 0.7) and (0.3 < face_center_y < 0.7)
            
            if looking_at_camera:
                eye_contact_frames += 1
                consecutive_looking_away = 0
            else:
                consecutive_looking_away += 1
                if consecutive_looking_away == 1:  # 視線を逸らし始めた
                    timestamp = frame_count / fps
                    looking_away_patterns.append({
                        "time": round(timestamp, 1),
                        "direction": "left" if face_center_x < 0.3 else "right"
                    })
        
        frame_count += 1
    
    cap.release()
    face_detection.close()
    
    duration_seconds = total_frames / fps if fps > 0 else 0
    eye_contact_ratio = (eye_contact_frames / total_frames * 100) if total_frames > 0 else 0
    eye_contact_frequency = len(looking_away_patterns) / (duration_seconds / 60) if duration_seconds > 60 else len(looking_away_patterns)
    avg_duration = (eye_contact_frames / fps / len(looking_away_patterns)) if looking_away_patterns else (eye_contact_frames / fps if fps > 0 else 0)
    
    feedback = "アイコンタクトは良好です" if eye_contact_ratio > 60 else "カメラを見る時間を増やしましょう"
    
    return {
        "eye_contact_ratio": round(eye_contact_ratio, 1),
        "eye_contact_frequency": round(eye_contact_frequency, 1),
        "average_duration": round(avg_duration, 1),
        "looking_away_patterns": looking_away_patterns[:5],
        "feedback": feedback
    }


def analyze_posture_mediapipe(video_path: str) -> Dict[str, Any]:
    """
    MediaPipe Pose で姿勢分析
    
    猫背・前傾姿勢を検出
    """
    if not MEDIAPIPE_AVAILABLE:
        return _analyze_posture_stub()
    
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5
    )
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _analyze_posture_stub()
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    posture_scores = []
    slouching_count = 0
    leaning_count = 0
    posture_changes = []
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 5 != 0:
            frame_count += 1
            continue
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)
        
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            
            # 肩と耳の位置で猫背判定
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR]
            right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR]
            
            # 耳が肩より前に出ていると猫背
            ear_shoulder_diff = ((left_ear.z + right_ear.z) / 2) - ((left_shoulder.z + right_shoulder.z) / 2)
            slouching = ear_shoulder_diff < -0.05
            
            # 前傾姿勢判定 (鼻と肩の位置)
            nose = landmarks[mp_pose.PoseLandmark.NOSE]
            leaning = nose.z < (left_shoulder.z + right_shoulder.z) / 2 - 0.1
            
            if slouching:
                slouching_count += 1
            if leaning:
                leaning_count += 1
            
            # 姿勢スコア (0-100)
            score = 100
            if slouching:
                score -= 30
            if leaning:
                score -= 20
            posture_scores.append(max(0, score))
            
            # 姿勢変化記録
            timestamp = frame_count / fps
            if slouching or leaning:
                posture_changes.append({
                    "time": round(timestamp, 1),
                    "issue": "slouching" if slouching else "leaning"
                })
        
        frame_count += 1
    
    cap.release()
    pose.close()
    
    avg_score = np.mean(posture_scores) if posture_scores else 0
    slouching_detected = slouching_count > total_frames * 0.2
    leaning_detected = leaning_count > total_frames * 0.2
    
    feedback = "姿勢は良好です"
    if slouching_detected:
        feedback = "背筋を伸ばして座りましょう"
    elif leaning_detected:
        feedback = "前のめりにならないよう注意しましょう"
    
    return {
        "posture_score": round(avg_score, 1),
        "slouching_detected": slouching_detected,
        "leaning_forward": leaning_detected,
        "body_stability": round(100 - (len(posture_changes) / (total_frames / fps) * 10), 1) if total_frames > 0 else 0,
        "posture_changes": posture_changes[:5],
        "feedback": feedback
    }


def analyze_gestures_mediapipe(video_path: str) -> Dict[str, Any]:
    """
    MediaPipe Hands でジェスチャー検出
    
    手の動き・癖を検出
    """
    if not MEDIAPIPE_AVAILABLE:
        return _analyze_gestures_stub()
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5
    )
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return _analyze_gestures_stub()
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    hand_gestures = []
    fidgeting_count = 0
    hair_touching_count = 0
    hand_clasping_count = 0
    frame_count = 0
    prev_hand_position = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 5 != 0:
            frame_count += 1
            continue
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 手の中心位置
                hand_center_x = np.mean([lm.x for lm in hand_landmarks.landmark])
                hand_center_y = np.mean([lm.y for lm in hand_landmarks.landmark])
                
                # そわそわした動き検出 (手の位置が頻繁に変わる)
                if prev_hand_position:
                    distance = np.sqrt((hand_center_x - prev_hand_position[0])**2 + 
                                     (hand_center_y - prev_hand_position[1])**2)
                    if distance > 0.1:
                        fidgeting_count += 1
                
                # 髪を触る (手が顔の上部にある)
                if hand_center_y < 0.3:
                    hair_touching_count += 1
                
                # 手を組む (2本の手が近い)
                if len(results.multi_hand_landmarks) == 2:
                    hand2_center_x = np.mean([lm.x for lm in results.multi_hand_landmarks[1].landmark])
                    hand2_center_y = np.mean([lm.y for lm in results.multi_hand_landmarks[1].landmark])
                    distance = np.sqrt((hand_center_x - hand2_center_x)**2 + (hand_center_y - hand2_center_y)**2)
                    if distance < 0.2:
                        hand_clasping_count += 1
                
                prev_hand_position = (hand_center_x, hand_center_y)
        
        frame_count += 1
    
    cap.release()
    hands.close()
    
    duration_seconds = total_frames / fps if fps > 0 else 0
    
    feedback = "手の動きは自然です"
    if fidgeting_count > duration_seconds * 0.5:
        feedback = "手の動きを落ち着かせましょう"
    elif hair_touching_count > duration_seconds * 0.2:
        feedback = "髪を触る癖に注意しましょう"
    
    return {
        "hand_gestures": hand_gestures,
        "fidgeting_count": fidgeting_count,
        "hair_touching": hair_touching_count,
        "hand_clasping": hand_clasping_count,
        "inappropriate_gestures": [],
        "feedback": feedback
    }


# === スタブ関数 (MediaPipe 未インストール時のフォールバック) ===
