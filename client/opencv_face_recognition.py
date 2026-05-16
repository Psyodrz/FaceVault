import cv2
import numpy as np
import os
import pickle
import json
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class OpenCVFaceRecognizer:
    """
    Face recognition system using OpenCV's built-in face recognizers.
    Alternative to dlib-based face recognition that works without compilation issues.
    """
    
    def __init__(self, model_type='LBPH'):
        """Initialize OpenCV face recognizer."""
        self.model_type = model_type
        
        # Initialize face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if self.face_cascade.empty():
            raise Exception("Error: Could not load face cascade classifier. Check OpenCV installation.")
        
        # Initialize face recognizer
        try:
            if model_type == 'LBPH':
                self.recognizer = cv2.face.LBPHFaceRecognizer_create()
            elif model_type == 'Eigen':
                self.recognizer = cv2.face.EigenFaceRecognizer_create()
            elif model_type == 'Fisher':
                self.recognizer = cv2.face.FisherFaceRecognizer_create()
            else:
                raise ValueError("Model type must be 'LBPH', 'Eigen', or 'Fisher'")
        except AttributeError:
            raise ImportError("OpenCV face recognition module not available. Install opencv-contrib-python instead of opencv-python: pip install opencv-contrib-python")
        
        # Database files
        self.model_file = f"opencv_face_model_{model_type.lower()}.yml"
        self.labels_file = "face_labels.pkl"
        self.database_file = "opencv_face_database.json"
        
        # Initialize data structures
        self.label_to_name = {}
        self.name_to_label = {}
        self.face_database = {}
        self.next_label = 0
        self.is_trained = False
        
        # Load existing data
        self.load_data()
    
    def load_data(self):
        """Load existing model and database."""
        try:
            # Load labels mapping
            if os.path.exists(self.labels_file):
                with open(self.labels_file, 'rb') as f:
                    data = pickle.load(f)
                    self.label_to_name = data.get('label_to_name', {})
                    self.name_to_label = data.get('name_to_label', {})
                    self.next_label = data.get('next_label', 0)
            
            # Load face database
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r') as f:
                    self.face_database = json.load(f)
            
            # Load trained model
            if os.path.exists(self.model_file) and self.label_to_name:
                self.recognizer.read(self.model_file)
                self.is_trained = True
                print(f"Loaded trained model with {len(self.label_to_name)} people")
            
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def save_data(self):
        """Save model and database."""
        try:
            # Save labels mapping
            data = {
                'label_to_name': self.label_to_name,
                'name_to_label': self.name_to_label,
                'next_label': self.next_label
            }
            with open(self.labels_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Save face database
            with open(self.database_file, 'w') as f:
                json.dump(self.face_database, f, indent=2)
            
            # Save trained model
            if self.is_trained:
                self.recognizer.write(self.model_file)
            
            print("Data saved successfully")
            
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def add_person(self, name: str, image_paths: List[str]) -> bool:
        """Add a new person to the recognition system."""
        if name in self.name_to_label:
            print(f"Person '{name}' already exists")
            return False
        
        faces = []
        labels = []
        valid_images = 0
        
        # Assign new label
        label = self.next_label
        self.next_label += 1
        
        for image_path in image_paths:
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                continue
            
            try:
                # Load and convert image
                img = cv2.imread(image_path)
                if img is None:
                    print(f"Could not read image: {image_path}")
                    continue
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                face_locations = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                if len(face_locations) == 0:
                    print(f"No face found in {image_path}")
                    continue
                elif len(face_locations) > 1:
                    print(f"Multiple faces found in {image_path}, using largest")
                
                # Use the largest face
                (x, y, w, h) = max(face_locations, key=lambda rect: rect[2] * rect[3])
                face_roi = gray[y:y+h, x:x+w]
                
                # Resize face to standard size
                face_roi = cv2.resize(face_roi, (100, 100))
                
                faces.append(face_roi)
                labels.append(label)
                valid_images += 1
                
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                continue
        
        if valid_images == 0:
            print(f"No valid images found for {name}")
            return False
        
        # Update mappings
        self.label_to_name[label] = name
        self.name_to_label[name] = label
        
        # Add to database
        self.face_database[name] = {
            'added_date': datetime.now().isoformat(),
            'image_count': valid_images,
            'image_paths': image_paths,
            'recognition_count': 0,
            'last_seen': None,
            'label': label
        }
        
        # Retrain model with all existing data
        self._retrain_model()
        
        print(f"Successfully added {name} with {valid_images} image(s)")
        return True
    
    def add_person_via_webcam(self, name: str, samples: int = 25, save_root: str = "opencv_dataset", camera_index: int = 0) -> bool:
        """Capture face samples from webcam for a given person and enroll them.

        - Creates a dataset folder structure like: opencv_dataset/<name>/
        - Detects face in live frames, saves cropped grayscale face ROIs to disk
        - After collecting the requested number of samples, calls add_person()
        """
        if not name or not name.strip():
            print("Name cannot be empty")
            return False

        name = name.strip()
        person_dir = os.path.join(save_root, name)
        os.makedirs(person_dir, exist_ok=True)

        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("Could not open webcam")
            return False

        print(f"Starting webcam capture for '{name}'.")
        print("Instructions: Look at the camera. We'll auto-capture faces when detected.")
        print("Press 'q' to cancel, 's' to force-save current face if detected.")

        saved = 0
        frame_count = 0
        image_paths: List[str] = []

        try:
            while saved < samples:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from webcam")
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(80, 80))

                # Draw and optionally save the largest detected face
                if len(faces) > 0:
                    (x, y, w, h) = max(faces, key=lambda r: r[2] * r[3])
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi_resized = cv2.resize(face_roi, (100, 100))

                    # Visuals
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Capturing {saved+1}/{samples}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

                    # Auto-save every few frames when a face is present
                    if frame_count % 5 == 0:
                        filename = os.path.join(person_dir, f"{name}_{saved+1:03d}.jpg")
                        cv2.imwrite(filename, face_roi_resized)
                        image_paths.append(filename)
                        saved += 1
                else:
                    cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                cv2.putText(frame, "Press q to cancel, s to save now", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.imshow('Enroll via Webcam', frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Enrollment cancelled by user")
                    break
                elif key == ord('s') and len(faces) > 0:
                    # Force save current detected face
                    filename = os.path.join(person_dir, f"{name}_{saved+1:03d}.jpg")
                    cv2.imwrite(filename, face_roi_resized)
                    image_paths.append(filename)
                    saved += 1

                frame_count += 1

        finally:
            cap.release()
            cv2.destroyAllWindows()

        if saved == 0:
            print("No samples captured. Nothing to add.")
            return False

        print(f"Captured {saved} sample(s) for '{name}'. Training model...")
        return self.add_person(name, image_paths)

    def _retrain_model(self):
        """Retrain the model with all known faces."""
        all_faces = []
        all_labels = []
        
        for name, data in self.face_database.items():
            label = data['label']
            
            for image_path in data['image_paths']:
                if not os.path.exists(image_path):
                    continue
                
                try:
                    img = cv2.imread(image_path)
                    if img is None:
                        continue
                    
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    face_locations = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                    
                    if len(face_locations) > 0:
                        (x, y, w, h) = max(face_locations, key=lambda rect: rect[2] * rect[3])
                        face_roi = gray[y:y+h, x:x+w]
                        face_roi = cv2.resize(face_roi, (100, 100))
                        
                        all_faces.append(face_roi)
                        all_labels.append(label)
                
                except Exception as e:
                    print(f"Error retraining with {image_path}: {e}")
                    continue
        
        if len(all_faces) > 0:
            self.recognizer.train(all_faces, np.array(all_labels))
            self.is_trained = True
            self.save_data()
            print(f"Model retrained with {len(all_faces)} face samples")
        else:
            print("No faces available for training")
    
    def recognize_face(self, face_roi: np.ndarray) -> Tuple[str, float]:
        """Recognize a single face ROI."""
        if not self.is_trained:
            return "Unknown", 0.0
        
        try:
            # Resize to standard size
            face_roi = cv2.resize(face_roi, (100, 100))
            
            # Predict
            label, confidence = self.recognizer.predict(face_roi)
            
            # Convert confidence to similarity (lower confidence = higher similarity for LBPH)
            if self.model_type == 'LBPH':
                # LBPH returns distance (lower is better)
                similarity = max(0, 1 - (confidence / 100))  # Normalize to 0-1
                threshold = 0.4  # Minimum similarity threshold
            else:
                # Eigen/Fisher return confidence (higher is better)
                similarity = confidence / 10000  # Normalize
                threshold = 0.3
            
            if similarity > threshold and label in self.label_to_name:
                name = self.label_to_name[label]
                
                # Update recognition stats
                if name in self.face_database:
                    self.face_database[name]['recognition_count'] += 1
                    self.face_database[name]['last_seen'] = datetime.now().isoformat()
                
                return name, similarity
            else:
                return "Unknown", 0.0
                
        except Exception as e:
            print(f"Error in recognition: {e}")
            return "Unknown", 0.0
    
    def recognize_faces_in_frame(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[str], List[float]]:
        """Recognize faces in a video frame."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        face_locations = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(50, 50))
        
        names = []
        confidences = []
        locations = []
        
        for (x, y, w, h) in face_locations:
            # Extract face ROI
            face_roi = gray[y:y+h, x:x+w]
            
            # Recognize face
            name, confidence = self.recognize_face(face_roi)
            
            names.append(name)
            confidences.append(confidence)
            locations.append((y, x+w, y+h, x))  # Convert to (top, right, bottom, left)
        
        return locations, names, confidences
    
    def recognize_webcam(self, camera_index: int = 0):
        """Real-time face recognition using webcam."""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise Exception("Could not open webcam")
        
        print("OpenCV Face Recognition started. Press 'q' to quit, 's' to save screenshot.")
        print(f"Known people: {list(self.name_to_label.keys())}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Recognize faces
            face_locations, face_names, face_confidences = self.recognize_faces_in_frame(frame)
            
            # Draw results
            for (top, right, bottom, left), name, confidence in zip(face_locations, face_names, face_confidences):
                # Draw rectangle
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label
                label = f"{name}"
                if name != "Unknown":
                    label += f" ({confidence:.2f})"
                
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # Add status
            status = f"Faces: {len(face_locations)} | Known: {len([n for n in face_names if n != 'Unknown'])}"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, "Press q to quit, s to save", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow('OpenCV Face Recognition', frame)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                timestamp = cv2.getTickCount()
                filename = f'opencv_recognition_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        self.save_data()
    
    def list_known_people(self):
        """List all known people in the database."""
        if not self.face_database:
            print("No people in database")
            return
        
        print("\nOpenCV Face Recognition Database:")
        print("=" * 50)
        
        for name, data in self.face_database.items():
            print(f"Name: {name}")
            print(f"  Added: {data.get('added_date', 'Unknown')}")
            print(f"  Images: {data.get('image_count', 0)}")
            print(f"  Recognitions: {data.get('recognition_count', 0)}")
            print(f"  Last seen: {data.get('last_seen', 'Never')}")
            print(f"  Model: {self.model_type}")
            print("-" * 30)


def main():
    """Main function for OpenCV face recognition."""
    try:
        recognizer = OpenCVFaceRecognizer()
        
        print("OpenCV Face Recognition System")
        print("=" * 40)
        print("1. Add person from image files")
        print("2. Add person via webcam capture")
        print("3. Real-time face recognition")
        print("4. List known people")
        print("5. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                name = input("Enter person's name: ").strip()
                if not name:
                    print("Name cannot be empty")
                    continue
                
                print("Enter image file paths (one per line, empty line to finish):")
                image_paths = []
                while True:
                    path = input("Image path: ").strip()
                    if not path:
                        break
                    image_paths.append(path)
                
                if image_paths:
                    recognizer.add_person(name, image_paths)
                else:
                    print("No image paths provided")
            
            elif choice == '2':
                try:
                    name = input("Enter person's name: ").strip()
                    if not name:
                        print("Name cannot be empty")
                    else:
                        samples_inp = input("How many samples to capture? [default 25]: ").strip()
                        samples = int(samples_inp) if samples_inp.isdigit() else 25
                        recognizer.add_person_via_webcam(name, samples=samples)
                except Exception as e:
                    print(f"Webcam enrollment error: {e}")

            elif choice == '3':
                try:
                    recognizer.recognize_webcam()
                except Exception as e:
                    print(f"Webcam error: {e}")
            
            elif choice == '4':
                recognizer.list_known_people()
            
            elif choice == '5':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1-5.")
    
    except Exception as e:
        print(f"Application error: {e}")


if __name__ == "__main__":
    main()
