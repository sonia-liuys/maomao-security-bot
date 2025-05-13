#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Camera Check Script - Diagnose camera issues on Raspberry Pi
相機檢查腳本 - 診斷樹莓派上的相機問題
"""

import os
import sys
import subprocess
import time
import cv2
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CameraCheck")

def run_command(cmd):
    """Run a shell command and return the output"""
    logger.info(f"Running command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return e.stderr

def check_v4l_devices():
    """Check available V4L devices"""
    logger.info("Checking V4L devices...")
    
    # Check if /dev/video* devices exist
    video_devices = run_command("ls -l /dev/video*")
    logger.info(f"Video devices:\n{video_devices}")
    
    # Get detailed info about video devices
    v4l2_info = run_command("v4l2-ctl --list-devices")
    logger.info(f"V4L2 device info:\n{v4l2_info}")
    
    # Check driver info
    driver_info = run_command("v4l2-ctl --info")
    logger.info(f"V4L2 driver info:\n{driver_info}")
    
    return video_devices

def check_camera_permissions():
    """Check camera permissions"""
    logger.info("Checking camera permissions...")
    
    # Check if current user is in the video group
    user_groups = run_command("groups")
    logger.info(f"Current user groups: {user_groups}")
    
    # Check permissions on video devices
    video_perms = run_command("ls -la /dev/video*")
    logger.info(f"Video device permissions:\n{video_perms}")
    
    return "video" in user_groups

def test_camera_with_cv2():
    """Test camera with OpenCV"""
    logger.info("Testing camera with OpenCV...")
    
    # Try different camera indices
    for idx in range(10):  # Try indices 0-9
        logger.info(f"Trying camera index {idx}...")
        
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened():
            logger.warning(f"Could not open camera with index {idx}")
            continue
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Could not read frame from camera {idx}")
            cap.release()
            continue
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"Successfully opened camera {idx}")
        logger.info(f"Resolution: {width}x{height}, FPS: {fps}")
        
        # Save a test image
        test_image_path = f"camera_{idx}_test.jpg"
        cv2.imwrite(test_image_path, frame)
        logger.info(f"Saved test image to {test_image_path}")
        
        # Release the camera
        cap.release()
        
        return idx, width, height
    
    logger.error("Could not open any camera")
    return None, None, None

def test_camera_with_gstreamer():
    """Test camera with GStreamer"""
    logger.info("Testing camera with GStreamer...")
    
    # Try different camera indices
    for idx in range(10):  # Try indices 0-9
        gst_pipeline = f"v4l2src device=/dev/video{idx} ! videoconvert ! appsink"
        logger.info(f"Trying GStreamer pipeline: {gst_pipeline}")
        
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            logger.warning(f"Could not open camera with GStreamer (index {idx})")
            continue
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Could not read frame from GStreamer camera {idx}")
            cap.release()
            continue
        
        # Get camera properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"Successfully opened camera {idx} with GStreamer")
        logger.info(f"Resolution: {width}x{height}")
        
        # Save a test image
        test_image_path = f"gstreamer_camera_{idx}_test.jpg"
        cv2.imwrite(test_image_path, frame)
        logger.info(f"Saved test image to {test_image_path}")
        
        # Release the camera
        cap.release()
        
        return idx, width, height
    
    logger.error("Could not open any camera with GStreamer")
    return None, None, None

def check_picamera():
    """Check if Raspberry Pi camera module is enabled"""
    logger.info("Checking Raspberry Pi camera module...")
    
    try:
        camera_info = run_command("vcgencmd get_camera")
        logger.info(f"Camera info: {camera_info}")
        
        if "detected=1" in camera_info:
            logger.info("Raspberry Pi camera module is detected")
            return True
        else:
            logger.warning("Raspberry Pi camera module is not detected")
            return False
    except Exception as e:
        logger.error(f"Error checking Pi camera: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting camera diagnostics...")
    
    # Check system information
    system_info = run_command("uname -a")
    logger.info(f"System info: {system_info}")
    
    # Check if this is a Raspberry Pi
    is_raspberry_pi = os.path.exists("/etc/rpi-issue")
    logger.info(f"Is Raspberry Pi: {is_raspberry_pi}")
    
    # Check V4L devices
    video_devices = check_v4l_devices()
    
    # Check camera permissions
    has_permissions = check_camera_permissions()
    if not has_permissions:
        logger.warning("Current user may not have sufficient permissions to access the camera")
        logger.info("Consider running: sudo usermod -a -G video $USER")
    
    # Check Raspberry Pi camera module
    if is_raspberry_pi:
        picamera_enabled = check_picamera()
    
    # Test camera with OpenCV
    logger.info("\n--- Testing camera with OpenCV ---")
    cv2_idx, cv2_width, cv2_height = test_camera_with_cv2()
    
    # Test camera with GStreamer
    logger.info("\n--- Testing camera with GStreamer ---")
    gst_idx, gst_width, gst_height = test_camera_with_gstreamer()
    
    # Print summary
    logger.info("\n=== Camera Diagnostics Summary ===")
    logger.info(f"System: {system_info.strip()}")
    logger.info(f"Video devices found: {'Yes' if video_devices else 'No'}")
    logger.info(f"User has video group permissions: {has_permissions}")
    
    if is_raspberry_pi:
        logger.info(f"Raspberry Pi camera module enabled: {picamera_enabled}")
    
    logger.info(f"OpenCV camera test: {'Success' if cv2_idx is not None else 'Failed'}")
    if cv2_idx is not None:
        logger.info(f"  - Working camera index: {cv2_idx}")
        logger.info(f"  - Resolution: {cv2_width}x{cv2_height}")
    
    logger.info(f"GStreamer camera test: {'Success' if gst_idx is not None else 'Failed'}")
    if gst_idx is not None:
        logger.info(f"  - Working camera index: {gst_idx}")
        logger.info(f"  - Resolution: {gst_width}x{gst_height}")
    
    # Provide recommendations
    logger.info("\n=== Recommendations ===")
    if not video_devices:
        logger.info("1. Check if the camera is properly connected")
        logger.info("2. Install V4L utilities: sudo apt-get install v4l-utils")
    
    if not has_permissions:
        logger.info("1. Add your user to the video group: sudo usermod -a -G video $USER")
        logger.info("2. Log out and log back in for the changes to take effect")
    
    if is_raspberry_pi and not picamera_enabled:
        logger.info("1. Enable the camera module: sudo raspi-config")
        logger.info("2. Navigate to Interfacing Options > Camera > Enable")
        logger.info("3. Reboot the Raspberry Pi: sudo reboot")
    
    if cv2_idx is None and gst_idx is None:
        logger.info("1. Try installing libv4l: sudo apt-get install libv4l-dev")
        logger.info("2. Reinstall OpenCV with V4L support")
        logger.info("3. Check if the camera is supported by the Raspberry Pi")
    
    if gst_idx is not None and cv2_idx is None:
        logger.info("1. Use GStreamer pipeline for camera access in your application")
    
    logger.info("\nDiagnostics complete.")

if __name__ == "__main__":
    main()
