"""
FaceVault Face Engine - Advanced Deep Learning Pipeline.
Uses OpenCV YuNet (Detection) and SFace (Recognition) with
enhanced multi-metric matching for cross-age and degraded-image support.
"""

import cv2
import numpy as np
import os
import pickle
import base64
import threading
from typing import List, Dict, Optional
from datetime import datetime

class FaceEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(self.base_dir, "models")
        self.labels_file = os.path.join(self.base_dir, "facevault_features.pkl")
        self.dataset_dir = os.path.join(self.base_dir, "facevault_dataset")
        os.makedirs(self.dataset_dir, exist_ok=True)

        # Load Deep Learning Models
        yunet_path = os.path.join(self.models_dir, "yunet.onnx")
        sface_path = os.path.join(self.models_dir, "sface.onnx")

        self.detector = None
        self.recognizer = None
        self.recognition_available = False

        if os.path.exists(yunet_path) and os.path.exists(sface_path):
            try:
                self.detector = cv2.FaceDetectorYN.create(
                    model=yunet_path,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.5,
                    nms_threshold=0.3,
                    top_k=5000
                )
                self.recognizer = cv2.FaceRecognizerSF.create(
                    model=sface_path,
                    config=""
                )
                self.recognition_available = True
                print("[Engine] Deep Learning ML Pipeline initialized (YuNet + SFace)")
            except Exception as e:
                print(f"[Engine] ML Pipeline init failed: {e}")
        else:
            print("[Engine] ONNX models not found in backend/models/")

        self.label_to_name: Dict[int, str] = {}
        self.name_to_label: Dict[str, int] = {}
        self.features: Dict[int, List[np.ndarray]] = {}
        self.next_label = 0
        self.is_trained = False

        self._load_model()
        print(f"[Engine] Ready - people={len(self.label_to_name)}")

    def _load_model(self):
        if os.path.exists(self.labels_file):
            try:
                with open(self.labels_file, 'rb') as f:
                    data = pickle.load(f)
                    self.label_to_name = data.get('label_to_name', {})
                    self.name_to_label = data.get('name_to_label', {})
                    self.features = data.get('features', {})
                    self.next_label = data.get('next_label', 0)
                if self.features:
                    self.is_trained = True
                print(f"[Engine] Loaded {len(self.label_to_name)} enrolled profiles")
            except Exception as e:
                print(f"[Engine] Error loading features: {e}")

    def _save_model(self):
        try:
            data = {
                'label_to_name': self.label_to_name,
                'name_to_label': self.name_to_label,
                'features': self.features,
                'next_label': self.next_label
            }
            with open(self.labels_file, 'wb') as f:
                pickle.dump(data, f)
            self.is_trained = len(self.features) > 0
        except Exception as e:
            print(f"[Engine] Error saving features: {e}")

    def _detect_yunet(self, frame: np.ndarray):
        if self.detector is None:
            return []
        h, w = frame.shape[:2]
        # YuNet requires dynamic input size based on the frame
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(frame)
        return faces if faces is not None else []

    def _pad_box(self, x, y, w, h, frame_h, frame_w, pad_ratio=0.30):
        """
        Expand a tight YuNet bounding box so it covers the full face
        including forehead, chin, and ears.
        """
        pad_w = int(w * pad_ratio)
        pad_h_top = int(h * pad_ratio * 1.5)   # Extra padding on top for forehead/hair
        pad_h_bot = int(h * pad_ratio * 0.8)    # Less padding on bottom

        nx = max(0, x - pad_w)
        ny = max(0, y - pad_h_top)
        nw = min(frame_w - nx, w + 2 * pad_w)
        nh = min(frame_h - ny, h + pad_h_top + pad_h_bot)

        return nx, ny, nw, nh

    def detect_faces(self, frame: np.ndarray, detect_eyes: bool = False) -> List[Dict]:
        faces = self._detect_yunet(frame)
        fh, fw = frame.shape[:2]
        results = []
        for face in faces:
            x, y, w, h = map(int, face[0:4])
            px, py, pw, ph = self._pad_box(x, y, w, h, fh, fw)
            results.append({"x": px, "y": py, "w": pw, "h": ph})
        return results

    # ─── Image Preprocessing Pipeline ──────────────────────────

    def _preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Enhance a face crop for better recognition under degraded conditions:
        phone screens, blur, low light, moiré patterns, old photos.
        """
        try:
            # 1. Bilateral filter: removes noise while keeping edges sharp
            denoised = cv2.bilateralFilter(face_img, 5, 50, 50)

            # 2. Convert to LAB and apply CLAHE on the L channel (adaptive contrast)
            lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            # 3. Light sharpening to recover detail from blur
            kernel = np.array([[0, -0.5, 0],
                               [-0.5, 3, -0.5],
                               [0, -0.5, 0]], dtype=np.float32)
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            return sharpened
        except Exception:
            return face_img

    def _super_enhance_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Aggressive enhancement for very degraded images:
        small faces, old photos, extreme blur.
        """
        try:
            # Upscale the face to a larger size for better feature extraction
            h, w = face_img.shape[:2]
            if h < 100 or w < 100:
                face_img = cv2.resize(face_img, (112, 112), interpolation=cv2.INTER_CUBIC)

            # Strong denoising
            denoised = cv2.fastNlMeansDenoisingColored(face_img, None, 10, 10, 7, 21)

            # CLAHE with stronger parameters
            lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

            # Stronger sharpening
            kernel = np.array([[-0.5, -0.5, -0.5],
                               [-0.5, 5, -0.5],
                               [-0.5, -0.5, -0.5]], dtype=np.float32)
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            return sharpened
        except Exception:
            return face_img

    # ─── Multi-Metric Recognition ──────────────────────────────

    def _match_features(self, feature: np.ndarray) -> tuple:
        """
        Match a feature vector against all enrolled features using
        BOTH cosine similarity and L2 (Euclidean) distance.
        Returns (best_label, best_cosine_score, best_l2_score).
        """
        best_cosine = 0.0
        best_l2 = float('inf')
        best_label_cos = -1
        best_label_l2 = -1

        for label, feats in self.features.items():
            for feat in feats:
                # Cosine similarity (higher = better, range 0-1)
                cos_score = self.recognizer.match(
                    feature, feat,
                    cv2.FaceRecognizerSF_FR_COSINE
                )
                if cos_score > best_cosine:
                    best_cosine = cos_score
                    best_label_cos = label

                # L2 Euclidean distance (lower = better)
                l2_score = self.recognizer.match(
                    feature, feat,
                    cv2.FaceRecognizerSF_FR_NORM_L2
                )
                if l2_score < best_l2:
                    best_l2 = l2_score
                    best_label_l2 = label

        return best_label_cos, best_cosine, best_label_l2, best_l2

    def recognize_faces(self, frame: np.ndarray) -> List[Dict]:
        faces = self._detect_yunet(frame)
        fh, fw = frame.shape[:2]
        results = []
        for face in faces:
            x, y, w, h = map(int, face[0:4])
            px, py, pw, ph = self._pad_box(x, y, w, h, fh, fw)
            name = "Unknown"
            best_match_score = 0.0

            if self.is_trained and self.recognition_available:
                try:
                    aligned_face = self.recognizer.alignCrop(frame, face)

                    # Single-pass for speed — extract feature once
                    feature = self.recognizer.feature(aligned_face)
                    lbl_cos, best_cos, lbl_l2, best_l2 = self._match_features(feature)

                    # ── Decision Logic (dual-metric) ──
                    COSINE_THRESHOLD = 0.28
                    L2_THRESHOLD = 1.25

                    matched = False

                    # Primary: cosine match
                    if best_cos >= COSINE_THRESHOLD:
                        name = self.label_to_name.get(lbl_cos, "Unknown")
                        best_match_score = min(100.0, round(
                            ((best_cos - 0.10) / 0.70) * 100, 1
                        ))
                        matched = True

                    # Fallback: L2 match
                    elif best_l2 <= L2_THRESHOLD:
                        name = self.label_to_name.get(lbl_l2, "Unknown")
                        best_match_score = min(100.0, max(20.0, round(
                            (1.0 - best_l2 / 2.0) * 100, 1
                        )))
                        matched = True

                    # Weak fusion: both agree on same person
                    elif (best_cos >= 0.18 and best_l2 <= 1.50
                          and lbl_cos == lbl_l2):
                        name = self.label_to_name.get(lbl_cos, "Unknown")
                        cos_pct = ((best_cos - 0.10) / 0.70) * 100
                        l2_pct = (1.0 - best_l2 / 2.0) * 100
                        best_match_score = min(100.0, max(15.0, round(
                            (cos_pct * 0.6 + l2_pct * 0.4), 1
                        )))
                        matched = True

                    if not matched:
                        best_match_score = round(
                            max(0, (best_cos / 0.70) * 100 * 0.3), 1
                        )

                except Exception as e:
                    print(f"Rec Error: {e}")

            results.append({
                "name": name,
                "confidence": best_match_score,
                "x": px, "y": py, "w": pw, "h": ph
            })

        return results

    # ─── Enrollment ────────────────────────────────────────────

    def _extract_features_from_images(self, images: List[np.ndarray]) -> tuple:
        """Extract features from a list of images. Returns (features_list, saved_count, first_face_img)."""
        features = []
        saved_count = 0
        first_face_img = None

        for img in images:
            detected = self._detect_yunet(img)
            if len(detected) == 0:
                continue

            # Largest face
            face = max(detected, key=lambda f: f[2] * f[3])
            try:
                aligned_face = self.recognizer.alignCrop(img, face)

                # Extract feature from raw face
                feature_raw = self.recognizer.feature(aligned_face)
                features.append(feature_raw)

                # Also extract from enhanced version for cross-condition robustness
                enhanced = self._preprocess_face(aligned_face)
                feature_enh = self.recognizer.feature(enhanced)
                features.append(feature_enh)

                if first_face_img is None:
                    first_face_img = aligned_face

                saved_count += 1
            except Exception:
                continue

        return features, saved_count, first_face_img

    def enroll_person(self, name: str, images: List[np.ndarray]) -> Dict:
        if not self.recognition_available:
            return {"success": False, "error": "Recognition model missing"}
        if name in self.name_to_label:
            return {"success": False, "error": f"'{name}' already exists"}

        label = self.next_label
        self.next_label += 1

        features, saved_count, first_face_img = self._extract_features_from_images(images)

        if saved_count == 0:
            return {"success": False, "error": "No faces found in images"}

        self.features[label] = features

        # Save aligned images to dataset directory
        person_dir = os.path.join(self.dataset_dir, name)
        os.makedirs(person_dir, exist_ok=True)
        for i, img in enumerate(images):
            detected = self._detect_yunet(img)
            if len(detected) > 0:
                face = max(detected, key=lambda f: f[2] * f[3])
                try:
                    aligned = self.recognizer.alignCrop(img, face)
                    filepath = os.path.join(person_dir, f"{name}_{i + 1:03d}.jpg")
                    cv2.imwrite(filepath, aligned)
                except Exception:
                    pass

        self.label_to_name[label] = name
        self.name_to_label[name] = label
        self._save_model()

        thumbnail = self._generate_thumbnail(first_face_img)

        return {
            "success": True,
            "name": name,
            "label_id": label,
            "image_count": saved_count,
            "feature_count": len(features),
            "thumbnail": thumbnail
        }

    def add_photos(self, name: str, images: List[np.ndarray]) -> Dict:
        """Add more photos/features to an already enrolled person."""
        if not self.recognition_available:
            return {"success": False, "error": "Recognition model missing"}
        if name not in self.name_to_label:
            return {"success": False, "error": f"'{name}' is not enrolled"}

        label = self.name_to_label[name]
        features, saved_count, _ = self._extract_features_from_images(images)

        if saved_count == 0:
            return {"success": False, "error": "No faces found in provided images"}

        # Append new features to existing ones
        self.features[label].extend(features)

        # Save new images to dataset
        person_dir = os.path.join(self.dataset_dir, name)
        os.makedirs(person_dir, exist_ok=True)
        existing_count = len([f for f in os.listdir(person_dir) if f.endswith('.jpg')])
        for i, img in enumerate(images):
            detected = self._detect_yunet(img)
            if len(detected) > 0:
                face = max(detected, key=lambda f: f[2] * f[3])
                try:
                    aligned = self.recognizer.alignCrop(img, face)
                    filepath = os.path.join(
                        person_dir,
                        f"{name}_{existing_count + i + 1:03d}.jpg"
                    )
                    cv2.imwrite(filepath, aligned)
                except Exception:
                    pass

        self._save_model()

        return {
            "success": True,
            "name": name,
            "new_images": saved_count,
            "new_features": len(features),
            "total_features": len(self.features[label])
        }

    def remove_person(self, name: str) -> bool:
        if name not in self.name_to_label:
            return False

        label = self.name_to_label.pop(name)
        self.label_to_name.pop(label, None)
        self.features.pop(label, None)

        person_dir = os.path.join(self.dataset_dir, name)
        if os.path.exists(person_dir):
            import shutil
            shutil.rmtree(person_dir)

        self._save_model()
        return True

    def _generate_thumbnail(self, face_img: np.ndarray) -> str:
        resized = cv2.resize(face_img, (80, 80))
        _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(buffer).decode('utf-8')

    def get_people_list(self) -> List[Dict]:
        return [{"name": name, "label_id": label} for name, label in self.name_to_label.items()]

    def decode_frame(self, data: bytes) -> Optional[np.ndarray]:
        try:
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception:
            return None

    def encode_frame(self, frame: np.ndarray, quality: int = 70) -> bytes:
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buffer.tobytes()
