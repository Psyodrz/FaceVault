#!/usr/bin/env python3
"""
Live Face Counter - Counts faces coming in front of camera
Tracks when new faces appear and disappear from the camera view
"""

import cv2
import numpy as np
import time
from datetime import datetime
from collections import deque

class LiveFaceCounter:
    def __init__(self):
        """Initialize the live face counter."""
        print("Initializing Live Face Counter...")
        
        # Load face detection cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        if self.face_cascade.empty():
            raise Exception("Error: Could not load face cascade classifier")
        
        # Counting variables
        self.current_faces = 0
        self.total_faces_seen = 0
        self.max_faces_at_once = 0
        self.face_entries = 0  # Number of times faces entered the frame
        self.face_exits = 0    # Number of times faces left the frame
        
        # History tracking for stability
        self.face_count_history = deque(maxlen=10)  # Last 10 frames
        self.stable_count = 0
        self.last_stable_count = 0
        
        # Session tracking
        self.session_start = datetime.now()
        self.detection_log = []
        
        # Display settings
        self.show_detailed_stats = True
        
        print("Live Face Counter initialized successfully!")
    
    def is_count_stable(self, current_count):
        """Check if the face count is stable across recent frames."""
        self.face_count_history.append(current_count)
        
        if len(self.face_count_history) < 5:
            return False
        
        # Check if the last 5 counts are the same
        recent_counts = list(self.face_count_history)[-5:]
        return all(count == recent_counts[0] for count in recent_counts)
    
    def update_face_statistics(self, current_count):
        """Update face counting statistics."""
        # Check for stable count changes
        if self.is_count_stable(current_count):
            if current_count != self.last_stable_count:
                # Face count changed stably
                if current_count > self.last_stable_count:
                    # New faces entered
                    new_faces = current_count - self.last_stable_count
                    self.face_entries += new_faces
                    print(f"[ENTRY] {new_faces} face(s) entered the frame")
                elif current_count < self.last_stable_count:
                    # Faces left
                    left_faces = self.last_stable_count - current_count
                    self.face_exits += left_faces
                    print(f"[EXIT] {left_faces} face(s) left the frame")
                
                self.last_stable_count = current_count
        
        # Update general statistics
        self.current_faces = current_count
        self.max_faces_at_once = max(self.max_faces_at_once, current_count)
        
        # Log detection event
        if current_count > 0:
            self.detection_log.append({
                'timestamp': datetime.now(),
                'face_count': current_count,
                'stable': self.is_count_stable(current_count)
            })
    
    def draw_face_info(self, frame, faces):
        """Draw face detection information on the frame."""
        height, width = frame.shape[:2]
        
        # Draw face rectangles and numbers
        for i, (x, y, w, h) in enumerate(faces):
            # Calculate face area for size indication
            face_area = w * h
            
            # Color coding: Green for large faces, Yellow for medium, Red for small
            if face_area > 5000:
                color = (0, 255, 0)  # Green - close/large face
                size_text = "CLOSE"
            elif face_area > 2500:
                color = (0, 255, 255)  # Yellow - medium face
                size_text = "MEDIUM"
            else:
                color = (0, 0, 255)  # Red - far/small face
                size_text = "FAR"
            
            # Draw face rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw face number and size
            cv2.putText(frame, f'Face {i+1}', (x, y - 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f'{size_text} ({w}x{h})', (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    def draw_statistics(self, frame):
        """Draw counting statistics on the frame."""
        # Background for statistics
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 200), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Current status
        cv2.putText(frame, f'CURRENT FACES: {self.current_faces}', (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Entry/Exit statistics
        cv2.putText(frame, f'Faces Entered: {self.face_entries}', (20, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f'Faces Exited: {self.face_exits}', (20, 95), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Session statistics
        cv2.putText(frame, f'Max at Once: {self.max_faces_at_once}', (20, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
        
        # Session duration
        duration = datetime.now() - self.session_start
        duration_str = str(duration).split('.')[0]  # Remove microseconds
        cv2.putText(frame, f'Session: {duration_str}', (20, 145), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Stability indicator
        stability = "STABLE" if len(self.face_count_history) >= 5 and \
                   len(set(list(self.face_count_history)[-5:])) == 1 else "DETECTING"
        color = (0, 255, 0) if stability == "STABLE" else (0, 255, 255)
        cv2.putText(frame, f'Status: {stability}', (20, 170), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Controls
        cv2.putText(frame, 'Controls: Q/ESC=Quit, R=Reset, S=Save, H=Toggle Stats', 
                   (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def reset_counters(self):
        """Reset all counters."""
        self.current_faces = 0
        self.total_faces_seen = 0
        self.max_faces_at_once = 0
        self.face_entries = 0
        self.face_exits = 0
        self.face_count_history.clear()
        self.stable_count = 0
        self.last_stable_count = 0
        self.session_start = datetime.now()
        self.detection_log.clear()
        print("All counters reset!")
    
    def save_session_report(self):
        """Save a session report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'face_counter_report_{timestamp}.txt'
        
        duration = datetime.now() - self.session_start
        
        with open(filename, 'w') as f:
            f.write("LIVE FACE COUNTER SESSION REPORT\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Session Start: {self.session_start}\n")
            f.write(f"Session Duration: {duration}\n\n")
            f.write(f"Face Entries: {self.face_entries}\n")
            f.write(f"Face Exits: {self.face_exits}\n")
            f.write(f"Maximum Faces at Once: {self.max_faces_at_once}\n")
            f.write(f"Total Detection Events: {len(self.detection_log)}\n\n")
            
            if self.detection_log:
                f.write("DETECTION LOG:\n")
                f.write("-" * 20 + "\n")
                for entry in self.detection_log[-20:]:  # Last 20 events
                    f.write(f"{entry['timestamp']}: {entry['face_count']} faces "
                           f"({'stable' if entry['stable'] else 'detecting'})\n")
        
        print(f"Session report saved to: {filename}")
    
    def start_counting(self):
        """Start the live face counting."""
        print("\nStarting Live Face Counter...")
        print("Position yourself in front of the camera to test face detection and counting.")
        print("Move in and out of frame to test entry/exit detection.")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            raise Exception("Could not open webcam")
        
        print("Live Face Counter is running!")
        print("Controls:")
        print("  Q/ESC - Quit")
        print("  R - Reset counters")
        print("  S - Save screenshot and report")
        print("  H - Toggle detailed statistics")
        print("  Ctrl+C - Force quit")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
                # Convert to grayscale for detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(50, 50),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # Update statistics
                self.update_face_statistics(len(faces))
                
                # Draw face information
                self.draw_face_info(frame, faces)
                
                # Draw statistics
                if self.show_detailed_stats:
                    self.draw_statistics(frame)
                else:
                    # Minimal display
                    cv2.putText(frame, f'Faces: {self.current_faces} | Entries: {self.face_entries} | Exits: {self.face_exits}', 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Show frame
                cv2.imshow('Live Face Counter', frame)
                
                # Handle key presses with improved exit handling
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q') or key == 27:  # 'q', 'Q', or ESC key
                    print("Exit requested by user")
                    break
                elif key == ord('r'):
                    self.reset_counters()
                elif key == ord('s'):
                    # Save screenshot and report
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_name = f'face_counter_screenshot_{timestamp}.jpg'
                    cv2.imwrite(screenshot_name, frame)
                    print(f"Screenshot saved: {screenshot_name}")
                    self.save_session_report()
                elif key == ord('h'):
                    self.show_detailed_stats = not self.show_detailed_stats
                    print(f"Detailed stats: {'ON' if self.show_detailed_stats else 'OFF'}")
                
                # Check if window was closed by clicking X button
                if cv2.getWindowProperty('Live Face Counter', cv2.WND_PROP_VISIBLE) < 1:
                    print("Window closed by user")
                    break
        
        except KeyboardInterrupt:
            print("Interrupted by user (Ctrl+C)")
        except Exception as e:
            print(f"Error during face counting: {e}")
        finally:
            # Ensure proper cleanup
            print("Cleaning up resources...")
            cap.release()
            cv2.destroyAllWindows()
            # Force destroy all OpenCV windows
            for i in range(5):
                cv2.waitKey(1)
        
        # Print final summary
        self.print_final_summary()
    
    def print_final_summary(self):
        """Print final session summary."""
        duration = datetime.now() - self.session_start
        
        print("\n" + "=" * 50)
        print("LIVE FACE COUNTER SESSION SUMMARY")
        print("=" * 50)
        print(f"Session Duration: {duration}")
        print(f"Total Face Entries: {self.face_entries}")
        print(f"Total Face Exits: {self.face_exits}")
        print(f"Maximum Faces at Once: {self.max_faces_at_once}")
        print(f"Total Detection Events: {len(self.detection_log)}")
        
        if self.detection_log:
            avg_faces = np.mean([event['face_count'] for event in self.detection_log])
            print(f"Average Faces per Detection: {avg_faces:.2f}")
        
        print("=" * 50)

def main():
    """Main function."""
    try:
        counter = LiveFaceCounter()
        counter.start_counting()
    except KeyboardInterrupt:
        print("\nFace counter stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Ensure all OpenCV windows are closed
        cv2.destroyAllWindows()
        # Additional cleanup
        for i in range(10):
            cv2.waitKey(1)
        print("Application terminated successfully")

if __name__ == "__main__":
    main()
