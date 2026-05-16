import cv2
import sys
import os
import pickle
import numpy as np
from datetime import datetime

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Face recognition library not available. Install with: pip install face-recognition")

class SimpleFaceRecognition:
    def __init__(self):
        """Initialize simple face recognition system."""
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if self.face_cascade.empty():
            raise Exception("Error: Could not load face cascade classifier. Check OpenCV installation.")
        self.known_face_encodings = []
        self.known_face_names = []
        self.encodings_file = "simple_face_encodings.pkl"
        
        # Load existing face data
        self.load_face_data()
    
    def load_face_data(self):
        """Load saved face encodings."""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                print(f"Loaded {len(self.known_face_names)} known faces: {', '.join(self.known_face_names)}")
            except Exception as e:
                print(f"Error loading face data: {e}")
    
    def save_face_data(self):
        """Save face encodings to file."""
        try:
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            print("Face data saved successfully")
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def add_face_from_webcam(self, name):
        """Capture and add a face from webcam."""
        if not FACE_RECOGNITION_AVAILABLE:
            print("Face recognition not available")
            return False
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return False
        
        print(f"Position your face in the frame and press SPACE to capture for {name}")
        print("Press 'q' to cancel")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB for face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_frame)
            
            # Draw rectangles around faces
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, "Press SPACE to capture", (left, top-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.putText(frame, f"Adding: {name} | SPACE=capture, Q=cancel", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.imshow('Add Face', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') and len(face_locations) > 0:
                # Capture the face
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if len(face_encodings) > 0:
                    self.known_face_encodings.append(face_encodings[0])
                    self.known_face_names.append(name)
                    self.save_face_data()
                    print(f"Successfully added {name} to the database!")
                    cap.release()
                    cv2.destroyAllWindows()
                    return True
                else:
                    print("Could not encode face, try again")
            elif key == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return False
    
    def detect_and_recognize_faces(self):
        """Face detection and recognition using webcam."""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return
        
        recognition_enabled = FACE_RECOGNITION_AVAILABLE and len(self.known_face_names) > 0
        
        print("Face detection and recognition started.")
        print("Controls:")
        print("  'q' - quit")
        print("  'a' - add new face")
        print("  's' - save screenshot")
        if recognition_enabled:
            print(f"  Known faces: {', '.join(self.known_face_names)}")
        else:
            print("  No known faces loaded or face recognition unavailable")
        
        process_this_frame = True
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every other frame for better performance
            if process_this_frame and recognition_enabled:
                # Resize frame for faster processing
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Find faces and encodings
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                for face_encoding in face_encodings:
                    # Compare with known faces
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                    name = "Unknown"
                    
                    if True in matches:
                        # Find the best match
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]
                    
                    face_names.append(name)
                
                # Scale back up face locations
                face_locations = [(top*4, right*4, bottom*4, left*4) for (top, right, bottom, left) in face_locations]
            
            elif not recognition_enabled:
                # Fall back to basic detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                face_locations = [(y, x+w, y+h, x) for (x, y, w, h) in faces]
                face_names = ["Unknown"] * len(faces)
            
            process_this_frame = not process_this_frame
            
            # Draw results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Choose color based on recognition
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # Add status information
            status = f'Faces: {len(face_locations)}'
            if recognition_enabled:
                known_count = sum(1 for name in face_names if name != "Unknown")
                status += f' | Known: {known_count}/{len(self.known_face_names)}'
            
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, 'Q=quit, A=add face, S=save', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow('Face Recognition', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                name = input("\nEnter name for new face: ").strip()
                if name and name not in self.known_face_names:
                    print("Position yourself in front of the camera...")
                    self.add_face_from_webcam(name)
                elif name in self.known_face_names:
                    print(f"Name '{name}' already exists!")
                else:
                    print("Invalid name!")
            elif key == ord('s'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f'face_recognition_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved as: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()

def detect_faces_simple():
    """Simple face detection using webcam - quick start version."""
    # Load the face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier. Check OpenCV installation.")
        return
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("Face detection started. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        # Show frame
        cv2.imshow('Face Detection', frame)
        
        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def main():
    """Main function with menu options."""
    print("Simple Face Detection & Recognition")
    print("=" * 40)
    print("1. Basic face detection only")
    print("2. Face detection with recognition")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == '1':
        detect_faces_simple()
    elif choice == '2':
        if not FACE_RECOGNITION_AVAILABLE:
            print("Face recognition not available. Install with: pip install face-recognition")
            print("Falling back to basic detection...")
            detect_faces_simple()
        else:
            recognizer = SimpleFaceRecognition()
            recognizer.detect_and_recognize_faces()
    else:
        print("Invalid choice. Running basic detection...")
        detect_faces_simple()

if __name__ == "__main__":
    main()
