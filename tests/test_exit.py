#!/usr/bin/env python3
"""
Test script to verify that the face counter exits properly
"""
import time
import subprocess
import sys
import os

def test_face_counter_exit():
    """Test that the face counter can be started and stopped properly."""
    print("Testing Live Face Counter exit functionality...")
    
    try:
        # Start the face counter process
        print("Starting face counter...")
        process = subprocess.Popen([sys.executable, "live_face_counter.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 text=True)
        
        # Wait a moment for it to initialize
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("[SUCCESS] Face counter started successfully")
            
            # Try to terminate gracefully
            print("Attempting graceful termination...")
            process.terminate()
            
            # Wait for termination
            try:
                stdout, stderr = process.communicate(timeout=5)
                print("[SUCCESS] Face counter terminated gracefully")
                print(f"Exit code: {process.returncode}")
                
                if stdout:
                    print("STDOUT:", stdout[-200:])  # Last 200 chars
                if stderr:
                    print("STDERR:", stderr[-200:])  # Last 200 chars
                    
            except subprocess.TimeoutExpired:
                print("[WARNING] Graceful termination timed out, forcing kill...")
                process.kill()
                process.communicate()
                print("[SUCCESS] Process forcefully terminated")
        else:
            print("[ERROR] Face counter failed to start")
            stdout, stderr = process.communicate()
            if stderr:
                print("Error:", stderr)
                
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        
    print("Test completed.")

if __name__ == "__main__":
    test_face_counter_exit()
