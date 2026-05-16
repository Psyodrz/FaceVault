"""
FaceVault Anonymizer Engine - Privacy Shield for face anonymization.
"""

import cv2
import numpy as np
import base64


class AnonymizerEngine:
    """Face anonymization engine for privacy protection."""

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        print("[Anonymizer] Engine initialized")

    def anonymize_image(self, image, mode="blur", blur_strength=51, color=(0,0,0)):
        result = image.copy()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        if blur_strength % 2 == 0:
            blur_strength += 1

        for (x, y, w, h) in faces:
            pad = int(max(w, h) * 0.15)
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2 = min(image.shape[1], x + w + pad)
            y2 = min(image.shape[0], y + h + pad)
            roi = result[y1:y2, x1:x2]

            if mode == "blur":
                result[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (blur_strength, blur_strength), 30)
            elif mode == "pixelate":
                small = cv2.resize(roi, (8, 8), interpolation=cv2.INTER_LINEAR)
                result[y1:y2, x1:x2] = cv2.resize(small, (x2-x1, y2-y1), interpolation=cv2.INTER_NEAREST)
            elif mode == "solid":
                cv2.rectangle(result, (x1, y1), (x2, y2), color, -1)

        return result, len(faces)

    def anonymize_to_base64(self, image, mode="blur", blur_strength=51):
        anon, count = self.anonymize_image(image, mode, blur_strength)
        _, buf = cv2.imencode('.jpg', anon, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return {"image_base64": base64.b64encode(buf).decode(), "faces_anonymized": count, "mode": mode}
