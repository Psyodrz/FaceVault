import cv2
import numpy as np
import os
from typing import List, Tuple, Optional, Dict
try:
    import face_recognition
    import pickle
    import json
    from datetime import datetime
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Face recognition libraries not installed. Only face detection will be available.")
    print("To enable face recognition, install: pip install face-recognition dlib")

class FaceDetector:
    """
    A comprehensive face detection and recognition class using OpenCV's Haar Cascade classifiers
    and face_recognition library. Supports both real-time webcam detection and static image processing
    with optional face recognition capabilities.
    """
    
    def __init__(self, enable_recognition: bool = True):
        """Initialize the face detector with pre-trained Haar cascade and optional face recognition."""
        # Load the pre-trained Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Check if cascades loaded successfully
        if self.face_cascade.empty():
            raise Exception("Error loading face cascade classifier")
        if self.eye_cascade.empty():
            raise Exception("Error loading eye cascade classifier")
        
        # Face recognition setup
        self.recognition_enabled = enable_recognition and FACE_RECOGNITION_AVAILABLE
        if self.recognition_enabled:
            self.encodings_file = "face_encodings.pkl"
            self.database_file = "face_database.json"
            self.known_face_encodings = []
            self.known_face_names = []
            self.face_database = {}
            self.tolerance = 0.6
            self.load_face_data()
        else:
            print("Face recognition disabled or libraries not available")
    
    def detect_faces_in_image(self, image_path: str, save_result: bool = True) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a static image file.
        
        Args:
            image_path (str): Path to the input image
            save_result (bool): Whether to save the result with bounding boxes
            
        Returns:
            List of tuples containing (x, y, width, height) for each detected face
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        print(f"Found {len(faces)} face(s) in the image")
        
        # Draw rectangles around faces and detect eyes
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            
            # Region of interest for eyes (within the face)
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = img[y:y + h, x:x + w]
            
            # Detect eyes within the face region
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
        
        # Save result if requested
        if save_result and len(faces) > 0:
            output_path = os.path.splitext(image_path)[0] + "_detected.jpg"
            cv2.imwrite(output_path, img)
            print(f"Result saved to: {output_path}")
        
        # Display the result
        cv2.imshow('Face Detection Result', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return faces.tolist()
    
    def detect_faces_webcam_with_recognition(self, camera_index: int = 0):
        """Real-time face detection and recognition using webcam."""
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise Exception("Could not open webcam")
        
        recognition_status = "enabled" if self.recognition_enabled and len(self.known_face_names) > 0 else "disabled"
        print(f"Starting face detection with recognition {recognition_status}. Press 'q' to quit, 's' to save screenshot.")
        if self.recognition_enabled:
            print(f"Known people: {', '.join(self.known_face_names) if self.known_face_names else 'None'}")
        
        process_this_frame = True
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every other frame for better performance
            if process_this_frame:
                if self.recognition_enabled and len(self.known_face_names) > 0:
                    face_locations, face_names, face_confidences = self.recognize_faces_in_frame(frame)
                else:
                    # Fall back to basic detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
                    face_locations = [(y, x+w, y+h, x) for (x, y, w, h) in faces]
                    face_names = ["Unknown"] * len(faces)
                    face_confidences = [0.0] * len(faces)
            
            process_this_frame = not process_this_frame
            
            # Draw results
            for (top, right, bottom, left), name, confidence in zip(face_locations, face_names, face_confidences):
                # Draw rectangle around face
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label with name and confidence
                label = f"{name}"
                if name != "Unknown" and confidence > 0:
                    label += f" ({confidence:.2f})"
                
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # Add status information
            status_text = f'Faces: {len(face_locations)}'
            if self.recognition_enabled:
                known_count = sum(1 for name in face_names if name != "Unknown")
                status_text += f' | Known: {known_count} | DB: {len(self.known_face_names)}'
            
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, 'Press q to quit, s to save', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow('Face Detection & Recognition', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                timestamp = cv2.getTickCount()
                filename = f'face_recognition_screenshot_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved as: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save updated recognition data
        if self.recognition_enabled:
            self.save_face_data()
    
    def detect_faces_webcam(self, camera_index: int = 0):
        """
        Real-time face detection using webcam.
        
        Args:
            camera_index (int): Camera index (usually 0 for default camera)
        """
        # Initialize webcam
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise Exception("Could not open webcam")
        
        print("Starting real-time face detection. Press 'q' to quit, 's' to save screenshot.")
        
        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            # Draw rectangles around faces
            for i, (x, y, w, h) in enumerate(faces):
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Add face number text
                face_num = i + 1
                cv2.putText(frame, f'Face {face_num}', (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                
                # Detect eyes within face region
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray)
                
                for (ex, ey, ew, eh) in eyes:
                    cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)
            
            # Add instructions
            cv2.putText(frame, f'Faces detected: {len(faces)}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, 'Press q to quit, s to save', (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Display the frame
            cv2.imshow('Real-time Face Detection', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save screenshot
                timestamp = cv2.getTickCount()
                filename = f'face_detection_screenshot_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved as: {filename}")
        
        # Release everything
        cap.release()
        cv2.destroyAllWindows()
    
    def batch_process_images(self, input_folder: str, output_folder: str = None):
        """
        Process multiple images in a folder for face detection.
        
        Args:
            input_folder (str): Path to folder containing images
            output_folder (str): Path to save processed images (optional)
        """
        if not os.path.exists(input_folder):
            raise FileNotFoundError(f"Input folder not found: {input_folder}")
        
        if output_folder and not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Supported image extensions
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        processed_count = 0
        total_faces = 0
        
        for filename in os.listdir(input_folder):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                image_path = os.path.join(input_folder, filename)
                
                try:
                    faces = self.detect_faces_in_image(image_path, save_result=False)
                    total_faces += len(faces)
                    processed_count += 1
                    
                    if output_folder:
                        # Process and save to output folder
                        img = cv2.imread(image_path)
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        faces_detected = self.face_cascade.detectMultiScale(gray, 1.1, 5)
                        
                        for (x, y, w, h) in faces_detected:
                            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        
                        output_path = os.path.join(output_folder, f"detected_{filename}")
                        cv2.imwrite(output_path, img)
                    
                    print(f"Processed {filename}: {len(faces)} faces detected")
                    
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
        
        print(f"\nBatch processing complete!")
        print(f"Processed {processed_count} images")
        print(f"Total faces detected: {total_faces}")

    def load_face_data(self):
        """Load existing face encodings and database from files."""
        if not self.recognition_enabled:
            return
                
        try:
            # Load encodings
            if os.path.exists(self.encodings_file):
                with open(self.encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                print(f"Loaded {len(self.known_face_encodings)} face encodings")
                
            # Load database metadata
            if os.path.exists(self.database_file):
                with open(self.database_file, 'r') as f:
                    self.face_database = json.load(f)
                print(f"Loaded database with {len(self.face_database)} people")
                    
        except Exception as e:
            print(f"Error loading face data: {str(e)}")
            self.known_face_encodings = []
            self.known_face_names = []
            self.face_database = {}

    def save_face_data(self):
        """Save face encodings and database to files."""
        if not self.recognition_enabled:
            return
                
        try:
            # Save encodings
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(data, f)
            
            # Save database metadata
            with open(self.database_file, 'w') as f:
                json.dump(self.face_database, f, indent=2)
                    
            print("Face data saved successfully")
                
        except Exception as e:
            print(f"Error saving face data: {str(e)}")

    def add_person_to_database(self, name: str, image_paths: List[str]) -> bool:
        """Add a new person to the face recognition database."""
        if not self.recognition_enabled:
            print("Face recognition not available")
            return False
                
        if name in self.known_face_names:
            print(f"Person '{name}' already exists in the database")
            return False
            
        person_encodings = []
        valid_images = 0
            
        for image_path in image_paths:
            if not os.path.exists(image_path):
                print(f"Image not found: {image_path}")
                continue
                    
            try:
                # Load image
                image = face_recognition.load_image_file(image_path)
                    
                # Get face encodings
                face_encodings = face_recognition.face_encodings(image)
                    
                if len(face_encodings) == 0:
                    print(f"No face found in {image_path}")
                    continue
                elif len(face_encodings) > 1:
                    print(f"Multiple faces found in {image_path}, using the first one")
                
                person_encodings.append(face_encodings[0])
                valid_images += 1
                    
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
                continue
            
        if valid_images == 0:
            print(f"No valid images found for {name}")
            return False
            
        # Add to known faces (use average encoding if multiple images)
        if len(person_encodings) == 1:
            final_encoding = person_encodings[0]
        else:
            # Average multiple encodings for better accuracy
            final_encoding = np.mean(person_encodings, axis=0)
        
        self.known_face_encodings.append(final_encoding)
        self.known_face_names.append(name)
            
        # Add to database metadata
        self.face_database[name] = {
            'added_date': datetime.now().isoformat(),
            'image_count': valid_images,
            'image_paths': image_paths,
            'recognition_count': 0,
            'last_seen': None
        }
            
        self.save_face_data()
        print(f"Successfully added {name} with {valid_images} image(s)")
        return True

    def recognize_faces_in_frame(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[str], List[float]]:
        """Recognize faces in a video frame using face recognition."""
        if not self.recognition_enabled or len(self.known_face_encodings) == 0:
            # Fall back to basic detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
            locations = [(y, x+w, y+h, x) for (x, y, w, h) in faces]  # Convert to (top, right, bottom, left)
            names = ["Unknown"] * len(faces)
            confidences = [0.0] * len(faces)
            return locations, names, confidences
            
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
        # Find faces and encodings
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
        face_names = []
        face_confidences = []
            
        for face_encoding in face_encodings:
            # Compare with known faces
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
            name = "Unknown"
            confidence = 0.0
                
            # Use the known face with the smallest distance
            if len(self.known_face_encodings) > 0:
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    confidence = 1 - face_distances[best_match_index]  # Convert distance to confidence
                        
                    # Update recognition count and last seen
                    if name in self.face_database:
                        self.face_database[name]['recognition_count'] += 1
                        self.face_database[name]['last_seen'] = datetime.now().isoformat()
            
            face_names.append(name)
            face_confidences.append(confidence)
            
        # Scale back up face locations
        scaled_locations = []
        for (top, right, bottom, left) in face_locations:
            scaled_locations.append((top * 4, right * 4, bottom * 4, left * 4))
            
        return scaled_locations, face_names, face_confidences
    
    def recognize_faces_in_image(self, image_path: str, save_result: bool = True) -> List[Dict]:
        """Recognize faces in a static image."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Recognize faces
        face_locations, face_names, face_confidences = self.recognize_faces_in_frame(image)
        
        results = []
        for (top, right, bottom, left), name, confidence in zip(face_locations, face_names, face_confidences):
            # Draw rectangle and label
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(image, (left, top), (right, bottom), color, 2)
            
            label = f"{name}"
            if name != "Unknown" and confidence > 0:
                label += f" ({confidence:.2f})"
            
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(image, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            results.append({
                'name': name,
                'confidence': confidence,
                'location': (top, right, bottom, left)
            })
        
        # Save result
        if save_result:
            output_path = os.path.splitext(image_path)[0] + "_recognized.jpg"
            cv2.imwrite(output_path, image)
            print(f"Recognition result saved to: {output_path}")
        
        # Display result
        cv2.imshow('Face Recognition Result', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        return results
    
    def list_known_people(self):
        """Display information about all known people."""
        if not self.recognition_enabled:
            print("Face recognition not available")
            return
            
        if not self.known_face_names:
            print("No people in the database")
            return
        
        print("\nKnown People Database:")
        print("=" * 50)
        
        for name in self.known_face_names:
            if name in self.face_database:
                data = self.face_database[name]
                print(f"Name: {name}")
                print(f"  Added: {data.get('added_date', 'Unknown')}")
                print(f"  Images: {data.get('image_count', 0)}")
                print(f"  Recognitions: {data.get('recognition_count', 0)}")
                print(f"  Last seen: {data.get('last_seen', 'Never')}")
                print("-" * 30)


def main():
    """Main function to demonstrate face detection capabilities."""
    try:
        # Initialize face detector
        detector = FaceDetector()
        
        print("Face Detection & Recognition Application")
        print("=" * 50)
        print("1. Real-time webcam detection")
        print("2. Detect faces in image file")
        print("3. Batch process images in folder")
        if detector.recognition_enabled:
            print("4. Add person to recognition database")
            print("5. Real-time face recognition (webcam)")
            print("6. Recognize faces in image file")
            print("7. List known people")
            print("8. Exit")
        else:
            print("4. Exit")
            print("\nNote: Face recognition features disabled.")
            print("Install face-recognition library to enable: pip install face-recognition dlib")
        
        while True:
            max_choice = 8 if detector.recognition_enabled else 4
            choice = input(f"\nEnter your choice (1-{max_choice}): ").strip()
            
            if choice == '1':
                try:
                    detector.detect_faces_webcam()
                except Exception as e:
                    print(f"Webcam error: {str(e)}")
            
            elif choice == '2':
                image_path = input("Enter image file path: ").strip()
                try:
                    faces = detector.detect_faces_in_image(image_path)
                    print(f"Detection complete! Found {len(faces)} faces.")
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            elif choice == '3':
                input_folder = input("Enter input folder path: ").strip()
                output_folder = input("Enter output folder path (optional, press Enter to skip): ").strip()
                output_folder = output_folder if output_folder else None
                
                try:
                    detector.batch_process_images(input_folder, output_folder)
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            elif choice == '4' and not detector.recognition_enabled:
                print("Goodbye!")
                break
            
            elif choice == '4' and detector.recognition_enabled:
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
                    detector.add_person_to_database(name, image_paths)
                else:
                    print("No image paths provided")
            
            elif choice == '5' and detector.recognition_enabled:
                try:
                    # Enhanced webcam with recognition
                    detector.detect_faces_webcam_with_recognition()
                except Exception as e:
                    print(f"Webcam error: {str(e)}")
            
            elif choice == '6' and detector.recognition_enabled:
                image_path = input("Enter image file path: ").strip()
                try:
                    results = detector.recognize_faces_in_image(image_path)
                    print(f"Recognition complete! Found {len(results)} face(s).")
                    for result in results:
                        print(f"  {result['name']} (confidence: {result['confidence']:.2f})")
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            elif choice == '7' and detector.recognition_enabled:
                detector.list_known_people()
            
            elif choice == '8' and detector.recognition_enabled:
                print("Goodbye!")
                break
            
            else:
                max_choice = 8 if detector.recognition_enabled else 4
                print(f"Invalid choice. Please enter 1-{max_choice}.")
    
    except Exception as e:
        print(f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
