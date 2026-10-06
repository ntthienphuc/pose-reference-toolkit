"""Optional MediaPipe Holistic adapter; no face or linguistic assessment."""
from pathlib import Path
import numpy as np
from .pose import PoseSequence

BODY = [("pose_nose", 0), ("pose_left_shoulder", 11), ("pose_right_shoulder", 12),
        ("pose_left_elbow", 13), ("pose_right_elbow", 14), ("pose_left_wrist", 15), ("pose_right_wrist", 16)]
HAND = ["wrist", "thumb_cmc", "thumb_mcp", "thumb_ip", "thumb_tip", "index_mcp", "index_pip", "index_dip", "index_tip",
        "middle_mcp", "middle_pip", "middle_dip", "middle_tip", "ring_mcp", "ring_pip", "ring_dip", "ring_tip",
        "pinky_mcp", "pinky_pip", "pinky_dip", "pinky_tip"]
NAMES = tuple([name for name, _ in BODY] + ["left_hand_" + n for n in HAND] + ["right_hand_" + n for n in HAND])
GROUPS = {"body": list(range(7)), "left_hand": list(range(7, 28)), "right_hand": list(range(28, 49))}


def extract_video(path, frame_stride=2, start_ms=0, end_ms=None):
    import cv2
    import mediapipe as mp
    if type(frame_stride) is not int or not 1 <= frame_stride <= 30 or not np.isfinite(start_ms) or start_ms < 0 or (end_ms is not None and (not np.isfinite(end_ms) or end_ms <= start_ms)):
        raise ValueError("Invalid frame sampling/clip interval")
    cap = cv2.VideoCapture(str(Path(path)))
    if not cap.isOpened():
        cap.release()
        raise ValueError("Video cannot be decoded")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        cap.release()
        raise ValueError("Video lacks a usable source FPS")
    try:
        holistic = mp.solutions.holistic.Holistic(model_complexity=1, smooth_landmarks=True,
                   min_detection_confidence=0.5, min_tracking_confidence=0.5)
    except Exception:
        cap.release()
        raise
    xy, confidence, times = [], [], []
    try:
        source_index = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # Frame-index/FPS timing is explicit. VFR exact timing is unsupported.
            stamp = source_index * 1000 / fps
            selected = source_index % frame_stride == 0 and stamp >= start_ms
            source_index += 1
            if end_ms is not None and stamp >= end_ms:
                break
            if not selected:
                continue
            if len(xy) >= 2000:
                raise ValueError("Video exceeds 2000 sampled frames; provide an explicit clip")
            results = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            points, conf = np.full((49, 2), np.nan), np.zeros(49)
            height, width = frame.shape[:2]
            if results.pose_landmarks is not None:
                for i, (_, landmark_index) in enumerate(BODY):
                    landmark = results.pose_landmarks.landmark[landmark_index]
                    points[i] = (landmark.x * width, landmark.y * height)
                    conf[i] = float(landmark.visibility)
            for landmarks, offset in ((results.left_hand_landmarks, 7), (results.right_hand_landmarks, 28)):
                if landmarks is not None:
                    for i, landmark in enumerate(landmarks.landmark):
                        points[offset + i] = (landmark.x * width, landmark.y * height)
                        conf[offset + i] = 1  # Presence indicator, not per-joint calibrated confidence.
            xy.append(points)
            confidence.append(conf)
            times.append(stamp)
    finally:
        holistic.close()
        cap.release()
    if not xy:
        raise ValueError("No frames were decoded in the requested interval")
    return PoseSequence(xy, confidence, times, NAMES, GROUPS)
