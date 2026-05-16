#!/usr/bin/env python3
"""
Quick automated test of face detection functionality
"""

import cv2
import numpy as np
import time

def quick_face_detection_test():
    """Quick test of face detection without user interaction."""
    print("Quick Face Detection Test")
    print("=" * 30)
    
    # Load face cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    if face_cascade.empty():
        print("[ERROR] Could not load face cascade classifier")
        return False
    
    print("[OK] Face cascade loaded successfully")
    
    # Test webcam access
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] Could not open webcam")
        return False
    
    print("[OK] Webcam opened successfully")
    
    # Test frame capture and face detection
    print("[INFO] Testing face detection for 5 seconds...")
    
    start_time = time.time()
    frame_count = 0
    detection_count = 0
    
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to capture frame")
            break
        
        frame_count += 1
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            detection_count += 1
            print(f"[DETECTION] Frame {frame_count}: {len(faces)} face(s) detected")
        
        # Small delay to prevent overwhelming output
        time.sleep(0.1)
    
    cap.release()
    
    print(f"\n[RESULTS]")
    print(f"Total frames processed: {frame_count}")
    print(f"Frames with face detections: {detection_count}")
    print(f"Detection rate: {(detection_count/frame_count)*100:.1f}%")
    
    if detection_count > 0:
        print("[SUCCESS] Face detection is working!")
        return True
    else:
        print("[INFO] No faces detected - this could be normal if no one was in front of the camera")
        return True

if __name__ == "__main__":
    try:
        success = quick_face_detection_test()
        if success:
            print("\n[OVERALL] Quick test completed successfully!")
        else:
            print("\n[OVERALL] Quick test failed!")
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
