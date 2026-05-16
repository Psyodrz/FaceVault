"""
FaceVault Liveness Engine - Anti-spoofing with blink & head movement detection.
Uses OpenCV for facial landmark detection (compatible with all systems).
Falls back gracefully when MediaPipe is unavailable.
"""

import cv2
import numpy as np
import time
import random
import os
from typing import Dict, Optional, Tuple
from enum import Enum


class Challenge(str, Enum):
    BLINK = "blink"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"


# Eye landmark indices for 68-point dlib/OpenCV face landmark model
# Left eye: points 36-41, Right eye: points 42-47
LEFT_EYE_68 = [36, 37, 38, 39, 40, 41]
RIGHT_EYE_68 = [42, 43, 44, 45, 46, 47]
NOSE_TIP_68 = 30


class LivenessEngine:
    """Anti-spoofing liveness detection using facial landmark analysis."""

    def __init__(self):
        self.available = False
        self.face_cascade = None
        self.landmark_predictor = None
        self.use_opencv_lbf = False

        # Strategy 1: Try OpenCV's built-in LBF facemark model
        try:
            lbf_model_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "models",
                "lbfmodel.yaml"
            )
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            if os.path.exists(lbf_model_path):
                self.landmark_predictor = cv2.face.createFacemarkLBF()
                self.landmark_predictor.loadModel(lbf_model_path)
                self.use_opencv_lbf = True
                self.available = True
                print("[Liveness] Engine initialized (OpenCV LBF landmarks)")
            else:
                # Strategy 2: Use basic EAR approximation with Haar cascade only
                # We'll compute EAR from the eye region ROI intensity analysis
                self.available = True
                self.use_opencv_lbf = False
                print("[Liveness] Engine initialized (Haar cascade + intensity-based EAR)")
        except Exception as e:
            print(f"[Liveness] OpenCV landmark init failed: {e}")
            # Strategy 3: Minimal mode - just use cascade for face presence
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                self.available = True
                print("[Liveness] Engine initialized (minimal mode - face presence only)")
            except Exception as e2:
                print(f"[Liveness] All init methods failed: {e2}")

        # Challenge state
        self.active_sessions: Dict[str, dict] = {}

    def create_challenge(self, session_id: str) -> Dict:
        """Create a new liveness challenge for a session."""
        challenges = [Challenge.BLINK, Challenge.TURN_LEFT, Challenge.TURN_RIGHT]
        selected = random.choice(challenges)

        messages = {
            Challenge.BLINK: "Please blink your eyes 2 times",
            Challenge.TURN_LEFT: "Please turn your head to the LEFT",
            Challenge.TURN_RIGHT: "Please turn your head to the RIGHT",
        }

        self.active_sessions[session_id] = {
            "challenge": selected,
            "started_at": time.time(),
            "blink_count": 0,
            "last_ear": None,
            "was_closed": False,
            "head_positions": [],
            "completed": False,
            "timeout": 15.0,
        }

        return {
            "challenge": selected.value,
            "message": messages[selected],
            "timeout": 15
        }

    def process_frame(self, session_id: str, frame: np.ndarray) -> Dict:
        """Process a video frame for the active liveness challenge."""
        if not self.available:
            return {"error": "Liveness engine not available", "passed": False}

        if session_id not in self.active_sessions:
            return {"error": "No active challenge", "passed": False}

        session = self.active_sessions[session_id]

        # Check timeout
        elapsed = time.time() - session["started_at"]
        if elapsed > session["timeout"]:
            self.active_sessions.pop(session_id, None)
            return {"status": "failed", "reason": "timeout", "passed": False}

        if session["completed"]:
            return {"status": "completed", "passed": True}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h, w = frame.shape[:2]

        challenge = session["challenge"]

        if challenge == Challenge.BLINK:
            return self._check_blink(session, gray, frame, h, w, elapsed)
        elif challenge in (Challenge.TURN_LEFT, Challenge.TURN_RIGHT):
            return self._check_head_turn(session, gray, frame, h, w, challenge, elapsed)
        else:
            return {"status": "unknown_challenge", "passed": False}

    def _detect_face_rect(self, gray):
        """Detect the largest face rectangle."""
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            return None
        # Return the largest face
        return max(faces, key=lambda f: f[2] * f[3])

    def _get_eye_ear_from_roi(self, gray, face_rect):
        """
        Compute an approximate Eye Aspect Ratio using intensity analysis
        of the eye region. When eyes are closed, the eye ROI has more
        uniform (higher average) intensity since the eyelid covers the iris.
        """
        x, y, w, h = face_rect

        # Eye region: upper 40% of face, split into left/right
        eye_y_start = y + int(h * 0.2)
        eye_y_end = y + int(h * 0.45)
        
        left_eye_roi = gray[eye_y_start:eye_y_end, x + int(w * 0.1):x + int(w * 0.4)]
        right_eye_roi = gray[eye_y_start:eye_y_end, x + int(w * 0.6):x + int(w * 0.9)]

        if left_eye_roi.size == 0 or right_eye_roi.size == 0:
            return 0.3  # Default open

        # Compute the standard deviation of pixel intensities
        # Open eyes have high variance (pupil + sclera), closed eyes have low variance
        left_std = np.std(left_eye_roi)
        right_std = np.std(right_eye_roi)
        avg_std = (left_std + right_std) / 2.0

        # Normalize to EAR-like range (0.0 - 0.5)
        # High std = open eyes ~ high EAR, low std = closed eyes ~ low EAR
        ear = min(0.5, avg_std / 60.0)  # Empirical scaling
        return ear

    def _get_landmarks_ear(self, gray, face_rect):
        """Get EAR using LBF landmark model if available."""
        x, y, w, h = face_rect
        faces_arr = np.array([[x, y, w, h]])
        
        try:
            ok, landmarks = self.landmark_predictor.fit(gray, faces_arr)
            if not ok or len(landmarks) == 0:
                return None
            
            pts = landmarks[0][0]  # 68 landmarks
            
            left_ear = self._eye_aspect_ratio_68(pts, LEFT_EYE_68)
            right_ear = self._eye_aspect_ratio_68(pts, RIGHT_EYE_68)
            avg_ear = (left_ear + right_ear) / 2.0
            
            return avg_ear
        except Exception:
            return None

    def _eye_aspect_ratio_68(self, landmarks, eye_indices):
        """Calculate Eye Aspect Ratio from 68-point landmarks."""
        pts = [landmarks[i] for i in eye_indices]

        # Vertical distances
        v1 = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
        v2 = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
        # Horizontal distance
        h_dist = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))

        if h_dist == 0:
            return 0.3
        return (v1 + v2) / (2.0 * h_dist)

    def _check_blink(self, session, gray, frame, h, w, elapsed) -> Dict:
        """Check for blink detection."""
        face_rect = self._detect_face_rect(gray)
        if face_rect is None:
            return {
                "status": "no_face",
                "message": "No face detected — look at the camera",
                "passed": False,
                "progress": 0
            }

        # Get EAR
        avg_ear = None
        if self.use_opencv_lbf and self.landmark_predictor is not None:
            avg_ear = self._get_landmarks_ear(gray, face_rect)
        
        if avg_ear is None:
            avg_ear = self._get_eye_ear_from_roi(gray, face_rect)

        EAR_THRESHOLD = 0.21 if self.use_opencv_lbf else 0.15

        if avg_ear < EAR_THRESHOLD:
            if not session["was_closed"]:
                session["was_closed"] = True
        else:
            if session["was_closed"]:
                session["blink_count"] += 1
                session["was_closed"] = False

        session["last_ear"] = avg_ear

        if session["blink_count"] >= 2:
            session["completed"] = True
            return {"status": "completed", "passed": True, "blinks": session["blink_count"], "progress": 100}

        return {
            "status": "in_progress",
            "message": f"Blinks detected: {session['blink_count']}/2",
            "progress": session["blink_count"] * 50,
            "ear": round(avg_ear, 3),
            "passed": False
        }

    def _check_head_turn(self, session, gray, frame, h, w, challenge, elapsed) -> Dict:
        """Check for head turn left/right using face position."""
        face_rect = self._detect_face_rect(gray)
        if face_rect is None:
            return {
                "status": "no_face",
                "message": "No face detected — look at the camera",
                "passed": False,
                "progress": 0
            }

        fx, fy, fw, fh = face_rect
        # Nose position approximation: center of face
        nose_x = (fx + fw / 2.0) / w  # Normalized 0-1

        session["head_positions"].append(nose_x)

        if len(session["head_positions"]) < 5:
            return {
                "status": "in_progress",
                "message": "Hold still, then turn your head...",
                "progress": 10,
                "passed": False
            }

        initial_x = np.mean(session["head_positions"][:5])
        current_x = nose_x
        delta = current_x - initial_x

        TURN_THRESHOLD = 0.06

        # Note: in image coordinates, turning LEFT moves face RIGHT (higher x)
        if challenge == Challenge.TURN_LEFT and delta > TURN_THRESHOLD:
            session["completed"] = True
            return {"status": "completed", "passed": True, "progress": 100}
        elif challenge == Challenge.TURN_RIGHT and delta < -TURN_THRESHOLD:
            session["completed"] = True
            return {"status": "completed", "passed": True, "progress": 100}

        progress = min(90, int(abs(delta) / TURN_THRESHOLD * 90))
        direction = "left" if challenge == Challenge.TURN_LEFT else "right"

        return {
            "status": "in_progress",
            "message": f"Turn your head {direction}...",
            "progress": progress,
            "passed": False
        }

    def cleanup_session(self, session_id: str):
        """Remove a completed/expired session."""
        self.active_sessions.pop(session_id, None)
