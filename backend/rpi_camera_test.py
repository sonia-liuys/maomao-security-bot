#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Raspberry Pi Camera Test Script
樹莓派攝像頭測試腳本
"""

import cv2
import time
import os
import platform

def test_camera(camera_index):
    """Test camera with specified index
    測試指定索引的攝像頭
    """
    print(f"Testing camera with index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Failed to open camera with index {camera_index}")
        return False
    
    # Get camera info
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Camera opened successfully:")
    print(f"- Resolution: {width}x{height}")
    print(f"- FPS: {fps}")
    
    # Try to read a frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame from camera")
        cap.release()
        return False
    
    print("Successfully read frame from camera")
    print(f"Frame shape: {frame.shape}")
    
    # Display the frame (if running on a system with display)
    try:
        window_name = f"Camera {camera_index} Test"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, frame)
        print("Press any key to close the window...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Could not display frame: {e}")
    
    # Release the camera
    cap.release()
    return True

def main():
    """Main function to test cameras
    測試攝像頭的主函數
    """
    print(f"Platform: {platform.system()}")
    is_raspberry_pi = platform.system() == "Linux" and os.path.exists("/etc/rpi-issue")
    print(f"Is Raspberry Pi: {is_raspberry_pi}")
    
    # Test camera index 0
    print("\n=== Testing camera index 0 ===")
    success_0 = test_camera(0)
    
    # Test camera index 1
    print("\n=== Testing camera index 1 ===")
    success_1 = test_camera(1)
    
    # Test camera index 2 (some systems might have multiple cameras)
    print("\n=== Testing camera index 2 ===")
    success_2 = test_camera(2)
    
    # Summary
    print("\n=== Summary ===")
    print(f"Camera 0: {'SUCCESS' if success_0 else 'FAILED'}")
    print(f"Camera 1: {'SUCCESS' if success_1 else 'FAILED'}")
    print(f"Camera 2: {'SUCCESS' if success_2 else 'FAILED'}")
    
    # Recommendation
    if is_raspberry_pi:
        if success_1:
            print("\nRecommendation for Raspberry Pi: Use camera_index = 1")
        elif success_0:
            print("\nRecommendation for Raspberry Pi: Use camera_index = 0")
        else:
            print("\nNo working camera found. Please check your camera connection.")
    else:
        if success_0:
            print("\nRecommendation for non-Raspberry Pi: Use camera_index = 0")
        elif success_1:
            print("\nRecommendation for non-Raspberry Pi: Use camera_index = 1")
        else:
            print("\nNo working camera found. Please check your camera connection.")

if __name__ == "__main__":
    main()
