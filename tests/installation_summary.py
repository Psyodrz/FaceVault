#!/usr/bin/env python3
"""
Installation Summary and Face Detection Capability Test
"""

import sys
import importlib

def check_library(name, import_name=None, version_attr='__version__'):
    """Check if a library is installed and get its version."""
    if import_name is None:
        import_name = name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, version_attr, 'Unknown')
        return True, version
    except ImportError:
        return False, None

def main():
    print("=" * 60)
    print("FACE DETECTION LIBRARIES INSTALLATION SUMMARY")
    print("=" * 60)
    
    # Core libraries for face detection
    libraries = [
        ('OpenCV (with contrib)', 'cv2', '__version__'),
        ('NumPy', 'numpy', '__version__'),
        ('Pillow (PIL)', 'PIL', '__version__'),
        ('Matplotlib', 'matplotlib', '__version__'),
        ('Pandas', 'pandas', '__version__'),
        ('Seaborn', 'seaborn', '__version__'),
    ]
    
    # Optional libraries
    optional_libraries = [
        ('face_recognition', 'face_recognition', '__version__'),
        ('dlib', 'dlib', 'version'),
        ('CMake', 'cmake', '__version__'),
    ]
    
    print("\nCORE LIBRARIES (Required for face detection):")
    print("-" * 50)
    
    all_core_installed = True
    for name, import_name, version_attr in libraries:
        installed, version = check_library(name, import_name, version_attr)
        status = "[OK]" if installed else "[MISSING]"
        version_str = f"v{version}" if version else ""
        print(f"{status:<10} {name:<25} {version_str}")
        if not installed:
            all_core_installed = False
    
    print("\nOPTIONAL LIBRARIES (Enhanced features):")
    print("-" * 50)
    
    for name, import_name, version_attr in optional_libraries:
        installed, version = check_library(name, import_name, version_attr)
        status = "[OK]" if installed else "[MISSING]"
        version_str = f"v{version}" if version else ""
        print(f"{status:<10} {name:<25} {version_str}")
    
    print("\nFACE DETECTION CAPABILITIES:")
    print("-" * 50)
    
    # Test OpenCV face detection
    try:
        import cv2
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if not face_cascade.empty():
            print("[OK]       Basic face detection (Haar Cascades)")
        else:
            print("[ERROR]    Face cascade classifier failed to load")
            all_core_installed = False
    except Exception as e:
        print(f"[ERROR]    OpenCV face detection: {e}")
        all_core_installed = False
    
    # Test OpenCV face recognition
    try:
        import cv2
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        print("[OK]       OpenCV face recognition (LBPH)")
    except Exception as e:
        print(f"[MISSING]  OpenCV face recognition: {e}")
    
    # Test webcam access
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("[OK]       Webcam access")
            cap.release()
        else:
            print("[ERROR]    Webcam not accessible")
    except Exception as e:
        print(f"[ERROR]    Webcam test: {e}")
    
    print("\nRECOMMENDED FACE DETECTION SCRIPTS:")
    print("-" * 50)
    
    if all_core_installed:
        print("[OK] live_face_counter.py      - Advanced face counting with entry/exit tracking")
        print("[OK] simple_face_counter.py    - Simple face counter with prominent display")
        print("[OK] opencv_face_recognition.py - OpenCV-based face recognition")
        print("[OK] comprehensive_face_test.py - Complete test suite")
        print("[OK] simple_face_detection.py  - Basic detection with optional recognition")
    else:
        print("[ERROR] Some core libraries are missing. Install them first.")
    
    print("\nINSTALLATION STATUS:")
    print("-" * 50)
    
    if all_core_installed:
        print("[SUCCESS] All core libraries installed!")
        print("   Your system is ready for face detection and counting.")
        print("\n   To start face counting, run:")
        print("   python live_face_counter.py")
    else:
        print("[WARNING] Some core libraries are missing.")
        print("   Run: pip install opencv-contrib-python numpy pillow")
    
    # Check for dlib/face_recognition
    dlib_installed, _ = check_library('dlib', 'dlib')
    face_rec_installed, _ = check_library('face_recognition', 'face_recognition')
    
    if not dlib_installed and not face_rec_installed:
        print("\n[NOTE] dlib and face_recognition are not installed.")
        print("   This is OK! OpenCV-based recognition works great on Windows.")
        print("   If you need dlib, install Visual Studio Build Tools first.")

if __name__ == "__main__":
    main()
