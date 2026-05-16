import cv2
import sys
import datetime

def test_face_detection():
    """Test face detection using webcam - auto-run version."""
    print("Starting face detection test...")
    
    # Load the face detection classifier
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier")
        return
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        print("Make sure your camera is connected and not being used by another application")
        return
    
    print("Face detection started successfully!")
    print("Controls:")
    print("  'q' - quit")
    print("  's' - save screenshot")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        frame_count += 1
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangles around faces
        for i, (x, y, w, h) in enumerate(faces):
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            # Add face number
            cv2.putText(frame, f'Face {i+1}', (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        
        # Add status information
        cv2.putText(frame, f'Faces detected: {len(faces)}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, 'Press Q to quit, S to save', (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(frame, f'Frame: {frame_count}', (10, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Display the frame
        cv2.imshow('Face Detection Test', frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Quitting face detection...")
            break
        elif key == ord('s'):
            # Save screenshot
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'face_detection_test_{timestamp}.jpg'
            cv2.imwrite(filename, frame)
            print(f"Screenshot saved as: {filename}")
        
        # Auto-quit after 30 seconds for testing (remove this in production)
        if frame_count > 900:  # ~30 seconds at 30 FPS
            print("Auto-stopping test after 30 seconds...")
            break
    
    # Release everything
    cap.release()
    cv2.destroyAllWindows()
    print("Face detection test completed!")

if __name__ == "__main__":
    test_face_detection()
