#!/usr/bin/env python3
"""Quick library check script"""

print("Checking required libraries...")

# Check OpenCV
try:
    import cv2
    print(f"[OK] OpenCV version: {cv2.__version__}")
    
    # Check cascade classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    if not face_cascade.empty():
        print("[OK] Face cascade classifier loaded successfully")
    else:
        print("[ERROR] Face cascade classifier failed to load")
        
    # Check if cv2.face is available (opencv-contrib)
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        print("[OK] OpenCV face recognition module available")
    except AttributeError:
        print("[ERROR] OpenCV face recognition module not available (need opencv-contrib-python)")
        
except ImportError as e:
    print(f"[ERROR] OpenCV not available: {e}")

# Check face_recognition library
try:
    import face_recognition
    print("[OK] face_recognition library available")
except ImportError as e:
    print(f"[ERROR] face_recognition library not available: {e}")

# Check numpy
try:
    import numpy as np
    print(f"[OK] NumPy version: {np.__version__}")
except ImportError as e:
    print(f"[ERROR] NumPy not available: {e}")

# Check webcam availability
try:
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print("[OK] Webcam is available")
        cap.release()
    else:
        print("[ERROR] Webcam not available or in use")
except Exception as e:
    print(f"[ERROR] Error checking webcam: {e}")

print("\nLibrary check complete!")
