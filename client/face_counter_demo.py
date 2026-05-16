 #!/usr/bin/env python3
"""
Demo script showing how to properly start and stop the Live Face Counter
"""
import subprocess
import sys
import time

def run_face_counter_demo():
    """Demonstrate the Live Face Counter with proper exit handling."""
    print("=" * 60)
    print("LIVE FACE COUNTER - DEMO & USAGE GUIDE")
    print("=" * 60)
    print()
    print("This demo will show you how to use the Live Face Counter safely.")
    print()
    print("IMPORTANT: The face counter has been fixed to prevent hanging!")
    print()
    print("Exit Methods Available:")
    print("1. Press 'Q' key while the camera window is active")
    print("2. Press 'ESC' key while the camera window is active") 
    print("3. Click the X button on the camera window")
    print("4. Press Ctrl+C in the terminal")
    print("5. Close the terminal window")
    print()
    print("Additional Controls:")
    print("- R: Reset all counters")
    print("- S: Save screenshot and session report")
    print("- H: Toggle detailed statistics display")
    print()
    
    choice = input("Do you want to start the Live Face Counter now? (y/n): ").lower().strip()
    
    if choice == 'y' or choice == 'yes':
        print()
        print("Starting Live Face Counter...")
        print("Remember: Press 'Q' or 'ESC' to exit safely!")
        print()
        
        try:
            # Start the face counter
            result = subprocess.run([sys.executable, "live_face_counter.py"], 
                                  check=False, 
                                  timeout=None)
            
            print(f"Face counter exited with code: {result.returncode}")
            
        except KeyboardInterrupt:
            print("\nFace counter interrupted by user")
        except Exception as e:
            print(f"Error running face counter: {e}")
    else:
        print("Demo cancelled. You can run the face counter anytime with:")
        print("python live_face_counter.py")
    
    print()
    print("=" * 60)
    print("TROUBLESHOOTING:")
    print("=" * 60)
    print("If the face counter ever hangs or doesn't respond:")
    print("1. Press Ctrl+C in the terminal")
    print("2. Close the terminal window")
    print("3. Use Task Manager to end python.exe processes")
    print("4. Run this command: taskkill /f /im python.exe")
    print()
    print("The fixes implemented should prevent hanging issues!")
    print("=" * 60)

if __name__ == "__main__":
    run_face_counter_demo()
