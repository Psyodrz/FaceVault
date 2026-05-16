import cv2
import face_recognition
import numpy as np
import pickle
import os
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

class FaceRecognitionSystem:
    """
    Advanced face recognition system that can learn and identify specific individuals.
    Uses face_recognition library for high-accuracy facial recognition.
    """
    
    def __init__(self, encodings_file: str = "face_encodings.pkl", database_file: str = "face_database.json"):
        """
        Initialize the face recognition system.
        
        Args:
            encodings_file (str): Path to save/load face encodings
            database_file (str): Path to save/load face database metadata
        """
        self.encodings_file = encodings_file
        self.database_file = database_file
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_database = {}
        
        # Load existing data if available
        self.load_face_data()
        
        # Recognition settings
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.tolerance = 0.6  # Lower = more strict recognition
        
    def load_face_data(self):
        """Load existing face encodings and database from files."""
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
    
    def add_person(self, name: str, image_paths: List[str]) -> bool:
        """
        Add a new person to the recognition system.
        
        Args:
            name (str): Name of the person
            image_paths (List[str]): List of image file paths containing the person's face
            
        Returns:
            bool: True if person was added successfully
        """
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
    
    def remove_person(self, name: str) -> bool:
        """
        Remove a person from the recognition system.
        
        Args:
            name (str): Name of the person to remove
            
        Returns:
            bool: True if person was removed successfully
        """
        if name not in self.known_face_names:
            print(f"Person '{name}' not found in database")
            return False
        
        # Find and remove the person
        index = self.known_face_names.index(name)
        self.known_face_encodings.pop(index)
        self.known_face_names.pop(index)
        
        # Remove from database
        if name in self.face_database:
            del self.face_database[name]
        
        self.save_face_data()
        print(f"Successfully removed {name} from database")
        return True
    
    def recognize_faces_in_frame(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[str], List[float]]:
        """
        Recognize faces in a video frame.
        
        Args:
            frame (np.ndarray): Input video frame
            
        Returns:
            Tuple containing face locations, names, and confidence scores
        """
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find faces and encodings
        self.face_locations = face_recognition.face_locations(rgb_small_frame)
        self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
        
        self.face_names = []
        face_confidences = []
        
        for face_encoding in self.face_encodings:
            # Compare with known faces
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=self.tolerance)
            name = "Unknown"
            confidence = 0.0
            
            # Use the known face with the smallest distance
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    confidence = 1 - face_distances[best_match_index]  # Convert distance to confidence
                    
                    # Update recognition count and last seen
                    if name in self.face_database:
                        self.face_database[name]['recognition_count'] += 1
                        self.face_database[name]['last_seen'] = datetime.now().isoformat()
            
            self.face_names.append(name)
            face_confidences.append(confidence)
        
        # Scale back up face locations
        scaled_locations = []
        for (top, right, bottom, left) in self.face_locations:
            scaled_locations.append((top * 4, right * 4, bottom * 4, left * 4))
        
        return scaled_locations, self.face_names, face_confidences
    
    def recognize_faces_webcam(self, camera_index: int = 0):
        """
        Real-time face recognition using webcam.
        
        Args:
            camera_index (int): Camera index
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise Exception("Could not open webcam")
        
        print("Starting face recognition. Press 'q' to quit, 's' to save screenshot.")
        print(f"Known people: {', '.join(self.known_face_names) if self.known_face_names else 'None'}")
        
        process_this_frame = True
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process every other frame for better performance
            if process_this_frame:
                face_locations, face_names, face_confidences = self.recognize_faces_in_frame(frame)
            
            process_this_frame = not process_this_frame
            
            # Draw results
            for (top, right, bottom, left), name, confidence in zip(face_locations, face_names, face_confidences):
                # Draw rectangle around face
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label with name and confidence
                label = f"{name}"
                if name != "Unknown":
                    label += f" ({confidence:.2f})"
                
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            # Add instructions
            cv2.putText(frame, f'Known: {len(self.known_face_names)} | Detected: {len(face_locations)}', 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, 'Press q to quit, s to save', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow('Face Recognition', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                timestamp = cv2.getTickCount()
                filename = f'recognition_screenshot_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved as: {filename}")
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Save updated recognition data
        self.save_face_data()
    
    def recognize_faces_in_image(self, image_path: str, save_result: bool = True) -> List[Dict]:
        """
        Recognize faces in a static image.
        
        Args:
            image_path (str): Path to the image file
            save_result (bool): Whether to save the result
            
        Returns:
            List of dictionaries containing recognition results
        """
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
            if name != "Unknown":
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
    
    def get_statistics(self) -> Dict:
        """Get system statistics."""
        total_recognitions = sum(data.get('recognition_count', 0) for data in self.face_database.values())
        
        return {
            'total_people': len(self.known_face_names),
            'total_recognitions': total_recognitions,
            'database_size_mb': os.path.getsize(self.encodings_file) / (1024*1024) if os.path.exists(self.encodings_file) else 0,
            'tolerance': self.tolerance
        }


def main():
    """Main function for face recognition system."""
    try:
        # Initialize face recognition system
        fr_system = FaceRecognitionSystem()
        
        print("Face Recognition System")
        print("=" * 40)
        print("1. Add new person to database")
        print("2. Remove person from database")
        print("3. Real-time face recognition (webcam)")
        print("4. Recognize faces in image file")
        print("5. List known people")
        print("6. Show system statistics")
        print("7. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-7): ").strip()
            
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
                    fr_system.add_person(name, image_paths)
                else:
                    print("No image paths provided")
            
            elif choice == '2':
                name = input("Enter person's name to remove: ").strip()
                if name:
                    fr_system.remove_person(name)
            
            elif choice == '3':
                try:
                    fr_system.recognize_faces_webcam()
                except Exception as e:
                    print(f"Webcam error: {str(e)}")
            
            elif choice == '4':
                image_path = input("Enter image file path: ").strip()
                try:
                    results = fr_system.recognize_faces_in_image(image_path)
                    print(f"Recognition complete! Found {len(results)} face(s).")
                    for result in results:
                        print(f"  {result['name']} (confidence: {result['confidence']:.2f})")
                except Exception as e:
                    print(f"Error: {str(e)}")
            
            elif choice == '5':
                fr_system.list_known_people()
            
            elif choice == '6':
                stats = fr_system.get_statistics()
                print("\nSystem Statistics:")
                print(f"  Total people: {stats['total_people']}")
                print(f"  Total recognitions: {stats['total_recognitions']}")
                print(f"  Database size: {stats['database_size_mb']:.2f} MB")
                print(f"  Recognition tolerance: {stats['tolerance']}")
            
            elif choice == '7':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1-7.")
    
    except Exception as e:
        print(f"Application error: {str(e)}")


if __name__ == "__main__":
    main()
