import cv2
import numpy as np

def simple_face_counter():
    """Simple face counter with prominent display of face count."""
    # Load face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier. Check OpenCV installation.")
        return
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("Simple Face Counter started. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(50, 50))
        face_count = len(faces)
        
        # Draw rectangles around faces and number them
        for i, (x, y, w, h) in enumerate(faces):
            # Draw face rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Add face number
            cv2.putText(frame, f'{i+1}', (x + 10, y + 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Display face count prominently at the top
        cv2.putText(frame, f'FACES DETECTED: {face_count}', (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        # Add background rectangle for better visibility
        cv2.rectangle(frame, (10, 10), (450, 60), (255, 255, 255), -1)
        cv2.putText(frame, f'FACES DETECTED: {face_count}', (20, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        # Show frame
        cv2.imshow('Simple Face Counter', frame)
        
        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    simple_face_counter()
