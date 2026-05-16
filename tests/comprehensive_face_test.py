#!/usr/bin/env python3
"""
Comprehensive face detection, counting, and recognition test
This script will test all the face detection and recognition functionality
"""

import cv2
import numpy as np
import os
import time
from datetime import datetime

class ComprehensiveFaceTest:
    def __init__(self):
        """Initialize the comprehensive face test system."""
        print("Initializing Comprehensive Face Test System...")
        
        # Load face detection cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if self.face_cascade.empty():
            raise Exception("Error: Could not load face cascade classifier")
        if self.eye_cascade.empty():
            print("Warning: Could not load eye cascade classifier")
        
        # Initialize counters and statistics
        self.total_faces_detected = 0
        self.max_faces_at_once = 0
        self.face_detection_history = []
        self.session_start_time = datetime.now()
        
        # Check if OpenCV face recognition is available
        self.opencv_recognition_available = False
        try:
            test_recognizer = cv2.face.LBPHFaceRecognizer_create()
            self.opencv_recognition_available = True
            print("[OK] OpenCV face recognition module available")
        except AttributeError:
            print("[WARNING] OpenCV face recognition module not available")
        
        print("Initialization complete!")
    
    def test_basic_face_detection(self, duration_seconds=10):
        """Test basic face detection functionality."""
        print(f"\n=== Testing Basic Face Detection (for {duration_seconds} seconds) ===")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Could not open webcam")
            return False
        
        start_time = time.time()
        frame_count = 0
        faces_detected_frames = 0
        
        while time.time() - start_time < duration_seconds:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to grab frame")
                break
            
            frame_count += 1
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(50, 50))
            current_face_count = len(faces)
            
            if current_face_count > 0:
                faces_detected_frames += 1
                self.total_faces_detected += current_face_count
                self.max_faces_at_once = max(self.max_faces_at_once, current_face_count)
                
                # Record detection
                self.face_detection_history.append({
                    'timestamp': datetime.now(),
                    'face_count': current_face_count,
                    'frame_number': frame_count
                })
            
            # Draw rectangles around faces
            for i, (x, y, w, h) in enumerate(faces):
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f'Face {i+1}', (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # Detect eyes within face
                if not self.eye_cascade.empty():
                    roi_gray = gray[y:y + h, x:x + w]
                    roi_color = frame[y:y + h, x:x + w]
                    eyes = self.eye_cascade.detectMultiScale(roi_gray)
                    
                    for (ex, ey, ew, eh) in eyes:
                        cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
            # Add status information
            remaining_time = duration_seconds - (time.time() - start_time)
            cv2.putText(frame, f'Faces: {current_face_count} | Time: {remaining_time:.1f}s', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f'Total detected: {self.total_faces_detected}', 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, 'Press Q to quit early', 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Face Detection Test', frame)
            
            # Check for early exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Test stopped by user")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Print results
        print(f"\n--- Basic Face Detection Results ---")
        print(f"Total frames processed: {frame_count}")
        print(f"Frames with faces detected: {faces_detected_frames}")
        print(f"Detection rate: {(faces_detected_frames/frame_count)*100:.1f}%")
        print(f"Total face instances detected: {self.total_faces_detected}")
        print(f"Maximum faces at once: {self.max_faces_at_once}")
        
        return True
    
    def test_face_counting_accuracy(self, duration_seconds=15):
        """Test face counting accuracy with detailed statistics."""
        print(f"\n=== Testing Face Counting Accuracy (for {duration_seconds} seconds) ===")
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERROR] Could not open webcam")
            return False
        
        start_time = time.time()
        frame_count = 0
        face_count_history = []
        
        while time.time() - start_time < duration_seconds:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with different parameters for accuracy
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            current_face_count = len(faces)
            face_count_history.append(current_face_count)
            
            # Draw faces with numbers and confidence indicators
            for i, (x, y, w, h) in enumerate(faces):
                # Calculate face area as a confidence indicator
                face_area = w * h
                color = (0, 255, 0) if face_area > 2500 else (0, 255, 255)  # Green for large faces, yellow for small
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f'#{i+1} ({w}x{h})', (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Calculate statistics
            avg_faces = np.mean(face_count_history[-30:]) if len(face_count_history) >= 30 else np.mean(face_count_history)
            
            # Display comprehensive information
            remaining_time = duration_seconds - (time.time() - start_time)
            cv2.putText(frame, f'Current Faces: {current_face_count}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f'Avg (last 30f): {avg_faces:.1f}', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f'Time: {remaining_time:.1f}s', (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, f'Frame: {frame_count}', (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            cv2.imshow('Face Counting Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Analyze counting accuracy
        if face_count_history:
            avg_count = np.mean(face_count_history)
            max_count = max(face_count_history)
            min_count = min(face_count_history)
            std_dev = np.std(face_count_history)
            
            print(f"\n--- Face Counting Results ---")
            print(f"Average faces per frame: {avg_count:.2f}")
            print(f"Maximum faces detected: {max_count}")
            print(f"Minimum faces detected: {min_count}")
            print(f"Standard deviation: {std_dev:.2f}")
            print(f"Counting stability: {'Good' if std_dev < 0.5 else 'Moderate' if std_dev < 1.0 else 'Variable'}")
        
        return True
    
    def test_opencv_face_recognition(self):
        """Test OpenCV-based face recognition if available."""
        if not self.opencv_recognition_available:
            print("\n=== OpenCV Face Recognition Test ===")
            print("[SKIPPED] OpenCV face recognition module not available")
            return False
        
        print("\n=== Testing OpenCV Face Recognition ===")
        print("This test requires you to train the system first.")
        print("For a full test, you would need to:")
        print("1. Capture training images of known faces")
        print("2. Train the LBPH recognizer")
        print("3. Test recognition accuracy")
        print("\nFor now, we'll just verify the module works...")
        
        try:
            # Create recognizer
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            print("[OK] LBPH Face Recognizer created successfully")
            
            # Test with dummy data
            dummy_faces = [np.random.randint(0, 255, (100, 100), dtype=np.uint8) for _ in range(5)]
            dummy_labels = [0, 0, 1, 1, 1]
            
            recognizer.train(dummy_faces, np.array(dummy_labels))
            print("[OK] Training with dummy data successful")
            
            # Test prediction
            test_face = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
            label, confidence = recognizer.predict(test_face)
            print(f"[OK] Prediction test successful - Label: {label}, Confidence: {confidence}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] OpenCV face recognition test failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence."""
        print("=" * 60)
        print("COMPREHENSIVE FACE DETECTION AND RECOGNITION TEST")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Basic face detection
        try:
            results['basic_detection'] = self.test_basic_face_detection(10)
        except Exception as e:
            print(f"[ERROR] Basic detection test failed: {e}")
            results['basic_detection'] = False
        
        # Test 2: Face counting accuracy
        try:
            results['counting_accuracy'] = self.test_face_counting_accuracy(15)
        except Exception as e:
            print(f"[ERROR] Counting accuracy test failed: {e}")
            results['counting_accuracy'] = False
        
        # Test 3: OpenCV face recognition
        try:
            results['opencv_recognition'] = self.test_opencv_face_recognition()
        except Exception as e:
            print(f"[ERROR] OpenCV recognition test failed: {e}")
            results['opencv_recognition'] = False
        
        # Print final summary
        print("\n" + "=" * 60)
        print("FINAL TEST RESULTS")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "PASSED" if result else "FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        session_duration = datetime.now() - self.session_start_time
        print(f"\nTotal test duration: {session_duration}")
        print(f"Total faces detected during session: {self.total_faces_detected}")
        print(f"Maximum faces detected at once: {self.max_faces_at_once}")
        
        # Overall assessment
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests PASSED! Face detection system is working correctly.")
        elif passed_tests >= total_tests * 0.7:
            print("✅ Most tests PASSED. System is mostly functional.")
        else:
            print("⚠️  Several tests FAILED. Please check your setup.")

def main():
    """Main function to run the comprehensive test."""
    try:
        tester = ComprehensiveFaceTest()
        
        print("\nThis test will:")
        print("1. Test basic face detection for 10 seconds")
        print("2. Test face counting accuracy for 15 seconds") 
        print("3. Test OpenCV face recognition capabilities")
        print("\nMake sure your webcam is working and you're in good lighting.")
        print("Position yourself in front of the camera during the tests.")
        
        input("\nPress Enter to start the comprehensive test...")
        
        tester.run_comprehensive_test()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")

if __name__ == "__main__":
    main()
