"""
FaceVault Analysis Engine - Emotion, age, gender detection.
Uses DeepFace when available, falls back to basic analysis.
"""

import cv2
import numpy as np
import base64

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

class AnalysisEngine:
    def __init__(self):
        self.available = DEEPFACE_AVAILABLE
        if self.available:
            print("[Analysis] DeepFace available")
        else:
            print("[Analysis] DeepFace not installed — emotion/age/gender disabled")

    def analyze_frame(self, frame):
        if not self.available:
            return []
        try:
            results = DeepFace.analyze(frame, actions=['emotion','age','gender'], enforce_detection=False, silent=True)
            if not isinstance(results, list):
                results = [results]
            output = []
            for r in results:
                output.append({
                    "emotion": r.get("dominant_emotion", "unknown"),
                    "emotions": r.get("emotion", {}),
                    "age": r.get("age", 0),
                    "gender": r.get("dominant_gender", "unknown"),
                    "region": r.get("region", {})
                })
            return output
        except Exception:
            return []

    def compare_faces(self, img1, img2):
        if not self.available:
            return {"similarity": 0, "verified": False, "error": "DeepFace not installed"}
        try:
            result = DeepFace.verify(img1, img2, enforce_detection=False)
            return {
                "similarity": round((1 - result.get("distance", 1)) * 100, 1),
                "verified": result.get("verified", False),
                "threshold": result.get("threshold", 0),
                "model": result.get("model", "VGG-Face"),
                "distance": result.get("distance", 0)
            }
        except Exception as e:
            return {"similarity": 0, "verified": False, "error": str(e)}
