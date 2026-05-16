import cv2
import numpy as np
import os
import json
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import time

class FaceCounter:
    """
    Enhanced face detection and counting system with statistics tracking.
    Counts faces, tracks people, and provides detailed analytics.
    """
    
    def __init__(self):
        """Initialize the face counter with detection and tracking capabilities."""
        # Load face detection cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        if self.face_cascade.empty() or self.eye_cascade.empty():
            raise Exception("Error loading cascade classifiers")
        
        # Counting variables
        self.total_faces_detected = 0
        self.max_faces_at_once = 0
        self.session_start_time = datetime.now()
        self.face_detection_log = []
        
        # Statistics tracking
        self.hourly_counts = defaultdict(int)
        self.daily_counts = defaultdict(int)
        self.face_size_stats = []
        
        # Counter display settings
        self.show_detailed_stats = True
        self.log_detections = True
        
        # Files for persistent storage
        self.stats_file = "face_counter_stats.json"
        self.log_file = "face_detection_log.json"
        
        # Load existing data
        self.load_statistics()
    
    def load_statistics(self):
        """Load existing statistics from file."""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_faces_detected = data.get('total_faces_detected', 0)
                    self.max_faces_at_once = data.get('max_faces_at_once', 0)
                    self.hourly_counts = defaultdict(int, data.get('hourly_counts', {}))
                    self.daily_counts = defaultdict(int, data.get('daily_counts', {}))
                    self.face_size_stats = data.get('face_size_stats', [])
                print(f"Loaded statistics: {self.total_faces_detected} total faces detected")
        except Exception as e:
            print(f"Error loading statistics: {e}")
    
    def save_statistics(self):
        """Save current statistics to file."""
        try:
            data = {
                'total_faces_detected': self.total_faces_detected,
                'max_faces_at_once': self.max_faces_at_once,
                'hourly_counts': dict(self.hourly_counts),
                'daily_counts': dict(self.daily_counts),
                'face_size_stats': self.face_size_stats,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save detection log
            if self.log_detections and self.face_detection_log:
                with open(self.log_file, 'w') as f:
                    json.dump(self.face_detection_log, f, indent=2)
                    
        except Exception as e:
            print(f"Error saving statistics: {e}")
    
    def update_counts(self, face_count: int, face_locations: List[Tuple[int, int, int, int]]):
        """Update counting statistics."""
        if face_count > 0:
            self.total_faces_detected += face_count
            self.max_faces_at_once = max(self.max_faces_at_once, face_count)
            
            # Update time-based counts
            now = datetime.now()
            hour_key = now.strftime("%Y-%m-%d %H:00")
            day_key = now.strftime("%Y-%m-%d")
            
            self.hourly_counts[hour_key] += face_count
            self.daily_counts[day_key] += face_count
            
            # Track face sizes for analytics
            for (x, y, w, h) in face_locations:
                face_area = w * h
                self.face_size_stats.append({
                    'area': face_area,
                    'width': w,
                    'height': h,
                    'timestamp': now.isoformat()
                })
            
            # Log detection event
            if self.log_detections:
                self.face_detection_log.append({
                    'timestamp': now.isoformat(),
                    'face_count': face_count,
                    'face_locations': face_locations
                })
                
                # Keep only last 1000 log entries
                if len(self.face_detection_log) > 1000:
                    self.face_detection_log = self.face_detection_log[-1000:]
    
    def detect_and_count_webcam(self, camera_index: int = 0):
        """Real-time face detection and counting using webcam."""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise Exception("Could not open webcam")
        
        print("Face Counter started. Press 'q' to quit, 'r' to reset counters, 's' to save screenshot")
        print("Press 'h' to toggle detailed stats display")
        
        # Frame processing variables
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Calculate FPS
            if frame_count % 30 == 0:
                fps = 30 / (time.time() - fps_start_time)
                fps_start_time = time.time()
            
            # Convert to grayscale for detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            current_face_count = len(faces)
            face_locations = [(x, y, w, h) for (x, y, w, h) in faces]
            
            # Update counts
            if current_face_count > 0:
                self.update_counts(current_face_count, face_locations)
            
            # Draw face rectangles and numbers
            for i, (x, y, w, h) in enumerate(faces):
                # Draw face rectangle
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Add face number
                cv2.putText(frame, f'Face {i+1}', (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                # Detect eyes within face
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
            # Display face count prominently
            cv2.putText(frame, f'Faces: {current_face_count}', (10, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            
            # Display counters and statistics
            self.draw_statistics(frame, current_face_count, fps)
            
            # Show frame
            cv2.imshow('Face Counter', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.reset_counters()
                print("Counters reset!")
            elif key == ord('s'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'face_count_screenshot_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
            elif key == ord('h'):
                self.show_detailed_stats = not self.show_detailed_stats
                print(f"Detailed stats: {'ON' if self.show_detailed_stats else 'OFF'}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save statistics before closing
        self.save_statistics()
        self.print_session_summary()
    
    def draw_statistics(self, frame: np.ndarray, current_faces: int, fps: float):
        """Draw counting statistics on the frame."""
        height, width = frame.shape[:2]
        
        # Background for stats (moved down to avoid overlap with main counter)
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 80), (400, 280 if self.show_detailed_stats else 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Basic stats (always shown)
        stats_text = [
            f"Current Faces: {current_faces}",
            f"Total Detected: {self.total_faces_detected}",
            f"Max at Once: {self.max_faces_at_once}",
            f"FPS: {fps:.1f}"
        ]
        
        # Detailed stats (toggleable)
        if self.show_detailed_stats:
            session_duration = datetime.now() - self.session_start_time
            session_minutes = session_duration.total_seconds() / 60
            
            today = datetime.now().strftime("%Y-%m-%d")
            today_count = self.daily_counts.get(today, 0)
            
            avg_per_minute = self.total_faces_detected / max(session_minutes, 0.1)
            
            stats_text.extend([
                f"Session: {session_minutes:.1f}m",
                f"Today: {today_count}",
                f"Avg/min: {avg_per_minute:.1f}"
            ])
        
        # Draw stats text (adjusted y position)
        for i, text in enumerate(stats_text):
            y_pos = 105 + (i * 25)
            cv2.putText(frame, text, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw controls help
        help_y = height - 60
        cv2.putText(frame, "Controls: Q=Quit, R=Reset, S=Save, H=Stats", 
                   (10, help_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    def detect_and_count_image(self, image_path: str, save_result: bool = True) -> Dict:
        """Detect and count faces in a static image."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        face_count = len(faces)
        face_locations = []
        
        # Update statistics
        if face_count > 0:
            face_locations = [(x, y, w, h) for (x, y, w, h) in faces]
            self.update_counts(face_count, face_locations)
        
        # Draw results
        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(img, f'Face {i+1}', (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
            # Detect eyes
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
        
        # Add count text to image
        cv2.putText(img, f'Faces Detected: {face_count}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Save result
        if save_result:
            output_path = os.path.splitext(image_path)[0] + "_counted.jpg"
            cv2.imwrite(output_path, img)
            print(f"Result saved to: {output_path}")
        
        # Display result
        cv2.imshow('Face Count Result', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return {
            'face_count': face_count,
            'face_locations': face_locations,
            'image_path': image_path,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_counters(self):
        """Reset all counters and start fresh."""
        self.total_faces_detected = 0
        self.max_faces_at_once = 0
        self.session_start_time = datetime.now()
        self.face_detection_log = []
        self.hourly_counts.clear()
        self.daily_counts.clear()
        self.face_size_stats = []
    
    def print_session_summary(self):
        """Print summary of the current session."""
        session_duration = datetime.now() - self.session_start_time
        
        print("\n" + "="*50)
        print("FACE COUNTING SESSION SUMMARY")
        print("="*50)
        print(f"Session Duration: {session_duration}")
        print(f"Total Faces Detected: {self.total_faces_detected}")
        print(f"Maximum Faces at Once: {self.max_faces_at_once}")
        session_minutes = max(session_duration.total_seconds() / 60, 0.1)  # Avoid division by zero
        print(f"Average per Minute: {self.total_faces_detected / session_minutes:.1f}")
        
        if self.face_size_stats:
            avg_size = np.mean([stat['area'] for stat in self.face_size_stats])
            print(f"Average Face Size: {avg_size:.0f} pixels²")
        
        print("="*50)
    
    def get_detailed_statistics(self) -> Dict:
        """Get comprehensive statistics."""
        now = datetime.now()
        session_duration = now - self.session_start_time
        
        # Calculate hourly and daily averages
        hourly_avg = np.mean(list(self.hourly_counts.values())) if self.hourly_counts else 0
        daily_avg = np.mean(list(self.daily_counts.values())) if self.daily_counts else 0
        
        # Face size statistics
        face_size_avg = np.mean([stat['area'] for stat in self.face_size_stats]) if self.face_size_stats else 0
        
        return {
            'session': {
                'duration_minutes': session_duration.total_seconds() / 60,
                'start_time': self.session_start_time.isoformat(),
                'faces_detected': self.total_faces_detected,
                'max_faces_at_once': self.max_faces_at_once
            },
            'averages': {
                'per_hour': hourly_avg,
                'per_day': daily_avg,
                'face_size_pixels': face_size_avg
            },
            'totals': {
                'total_faces': self.total_faces_detected,
                'detection_events': len(self.face_detection_log),
                'days_tracked': len(self.daily_counts)
            }
        }


def main():
    """Main function for face counter application."""
    try:
        counter = FaceCounter()
        
        print("Face Counter Application")
        print("=" * 40)
        print("1. Real-time webcam counting")
        print("2. Count faces in image file")
        print("3. View detailed statistics")
        print("4. Reset all counters")
        print("5. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                try:
                    counter.detect_and_count_webcam()
                except Exception as e:
                    print(f"Webcam error: {e}")
            
            elif choice == '2':
                image_path = input("Enter image file path: ").strip()
                try:
                    result = counter.detect_and_count_image(image_path)
                    print(f"Found {result['face_count']} faces in the image")
                except Exception as e:
                    print(f"Error: {e}")
            
            elif choice == '3':
                stats = counter.get_detailed_statistics()
                print("\nDETAILED STATISTICS")
                print("=" * 30)
                print(f"Session Duration: {stats['session']['duration_minutes']:.1f} minutes")
                print(f"Total Faces Detected: {stats['totals']['total_faces']}")
                print(f"Max Faces at Once: {stats['session']['max_faces_at_once']}")
                print(f"Average per Hour: {stats['averages']['per_hour']:.1f}")
                print(f"Average Face Size: {stats['averages']['face_size_pixels']:.0f} pixels²")
                print(f"Detection Events: {stats['totals']['detection_events']}")
                print(f"Days Tracked: {stats['totals']['days_tracked']}")
            
            elif choice == '4':
                confirm = input("Reset all counters? (y/N): ").strip().lower()
                if confirm == 'y':
                    counter.reset_counters()
                    print("All counters reset!")
                else:
                    print("Reset cancelled")
            
            elif choice == '5':
                counter.save_statistics()
                print("Statistics saved. Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1-5.")
    
    except Exception as e:
        print(f"Application error: {e}")


if __name__ == "__main__":
    main()
