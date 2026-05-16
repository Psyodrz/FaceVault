# Face Detection & Recognition Application

A comprehensive face detection and recognition application using OpenCV, face_recognition, and Python. This project provides multiple ways to detect and identify faces in images and real-time video streams.

## Features

### Face Detection
- **Real-time face detection** using webcam
- **Static image face detection** with file input
- **Batch processing** for multiple images
- **Eye detection** within detected faces
- **Screenshot capture** during real-time detection
- **Simple and advanced** detection modes

### Face Recognition (New!)
- **Learn and identify specific individuals**
- **Real-time face recognition** with confidence scores
- **Face database management** with persistent storage
- **Multiple image training** for improved accuracy
- **Recognition statistics** and tracking
- **Automatic fallback** to detection when recognition unavailable

## Installation

### Basic Installation (Face Detection Only)
1. Install Python 3.7 or higher
2. Install basic dependencies:

```bash
pip install opencv-python numpy pillow
```

### Full Installation (Face Detection + Recognition)
1. Install Python 3.7 or higher
2. Install all dependencies including face recognition:

```bash
pip install -r requirements.txt
```

**Note:** Face recognition requires additional system dependencies:
- **Windows:** Visual Studio Build Tools
- **macOS:** Xcode command line tools
- **Linux:** cmake, build-essential

If face recognition installation fails, the application will still work in detection-only mode.

## Usage

### Quick Start (Simple Version)

For a quick face detection demo using your webcam:

```bash
python simple_face_detection.py
```

- Press 'q' to quit the application

### Full Application

For the complete face detection and recognition application:

```bash
python face_detection.py
```

The application will present a menu with options that vary based on available libraries:

#### Face Detection Features (Always Available)
1. **Real-time webcam detection**
   - Uses your default camera for live face detection
   - Press 'q' to quit, 's' to save screenshot
   - Shows face count and eye detection

2. **Detect faces in image file**
   - Enter the path to an image file
   - Detects faces and saves result with bounding boxes
   - Supports JPG, PNG, BMP, TIFF formats

3. **Batch process images in folder**
   - Process multiple images in a folder
   - Optional output folder for saving results
   - Provides summary statistics

#### Face Recognition Features (When Libraries Available)
4. **Add person to recognition database**
   - Train the system to recognize specific individuals
   - Supports multiple training images per person
   - Automatic face encoding and storage

5. **Real-time face recognition (webcam)**
   - Live recognition with confidence scores
   - Green boxes for known people, red for unknown
   - Real-time statistics display

6. **Recognize faces in image file**
   - Identify people in static images
   - Confidence scores and result saving
   - Detailed recognition results

7. **List known people**
   - View database statistics
   - Recognition counts and last seen dates
   - Database management information

## File Structure

```
facedectection/
├── face_detection.py              # Main application with detection & recognition
├── face_recognition_system.py     # Standalone face recognition system
├── simple_face_detection.py       # Quick start detection-only version
├── requirements.txt               # Python dependencies
├── face_encodings.pkl            # Face recognition database (created automatically)
├── face_database.json           # Face metadata and statistics (created automatically)
└── README.md                     # This file
```

## Dependencies

### Core Dependencies (Always Required)
- **opencv-python**: Computer vision library for face detection
- **numpy**: Numerical computing library
- **pillow**: Image processing library

### Face Recognition Dependencies (Optional)
- **face-recognition**: High-level face recognition library
- **dlib**: Machine learning library for face recognition
- **cmake**: Build system (required for dlib compilation)

## How It Works

### Face Detection
The application uses OpenCV's pre-trained Haar Cascade classifiers:
- `haarcascade_frontalface_default.xml` for face detection
- `haarcascade_eye.xml` for eye detection

These classifiers are included with OpenCV and provide reliable face detection for most use cases.

### Face Recognition
The face recognition system uses:
- **dlib's face recognition model**: State-of-the-art deep learning model
- **128-dimensional face encodings**: Unique numerical representations of faces
- **Euclidean distance comparison**: Measures similarity between face encodings
- **Persistent storage**: Face encodings and metadata saved to disk
- **Confidence scoring**: Distance-based confidence measurements

## Troubleshooting

### Common Issues

1. **Webcam not working**
   - Check if your camera is being used by another application
   - Try changing the camera index in the code (0, 1, 2, etc.)

2. **Poor detection accuracy**
   - Ensure good lighting conditions
   - Face should be clearly visible and not too small
   - Adjust the `scaleFactor` and `minNeighbors` parameters

3. **Face recognition installation fails**
   - Install Visual Studio Build Tools (Windows)
   - Install cmake: `pip install cmake`
   - Try installing dlib separately: `pip install dlib`
   - Use conda instead: `conda install -c conda-forge dlib`

4. **Poor recognition accuracy**
   - Use multiple high-quality training images per person
   - Ensure good lighting in training images
   - Adjust tolerance parameter (lower = more strict)
   - Re-train with better quality images

5. **Installation issues**
   - Make sure you have Python 3.7+
   - Try upgrading pip: `python -m pip install --upgrade pip`
   - Install dependencies one by one if batch install fails

### Performance Tips

- For better performance, reduce the input image size
- Adjust detection parameters based on your specific use case
- Use the simple version for basic real-time detection
- Face recognition processes every other frame for better performance
- Consider using lower resolution for real-time recognition
- Batch process images when possible for better efficiency

## Example Output

### Face Detection Mode
When faces are detected, you'll see:
- Blue rectangles around detected faces
- Green rectangles around detected eyes
- Face count displayed on screen
- Console output with detection statistics

### Face Recognition Mode
When faces are recognized, you'll see:
- Green rectangles around known people
- Red rectangles around unknown faces
- Names and confidence scores displayed
- Real-time statistics (faces detected, known people, database size)
- Console output with recognition results and database updates

## Getting Started with Face Recognition

1. **Install dependencies** (including face-recognition)
2. **Run the application**: `python face_detection.py`
3. **Add people to database**: Choose option 4, provide name and image paths
4. **Start recognition**: Choose option 5 for live recognition
5. **View statistics**: Choose option 7 to see database info

### Training Tips
- Use 3-5 high-quality images per person
- Ensure good lighting and clear face visibility
- Include different angles and expressions
- Avoid blurry or low-resolution images

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.
