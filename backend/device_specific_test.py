#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Device-specific camera test for Raspberry Pi
針對樹莓派的設備特定相機測試
"""

import cv2
import time
import logging
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeviceTest")

def test_specific_devices():
    """Test specific video devices found on this system"""
    # List of devices to try, based on the diagnostic output
    devices = [
        "/dev/video1",
        "/dev/video2",
        "/dev/video20",
        "/dev/video19"
    ]
    
    results = {}
    
    for device in devices:
        logger.info(f"Testing device: {device}")
        
        # Try direct device access
        try:
            # Try with V4L2 backend explicitly
            cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
            if not cap.isOpened():
                logger.warning(f"Could not open {device} with V4L2 backend")
                cap.release()
                
                # Try with default backend
                cap = cv2.VideoCapture(device)
                if not cap.isOpened():
                    logger.warning(f"Could not open {device} with default backend")
                    results[device] = {"status": "failed", "error": "Could not open device"}
                    continue
            
            # Try to read a frame
            ret, frame = cap.read()
            if not ret:
                logger.warning(f"Could not read frame from {device}")
                results[device] = {"status": "failed", "error": "Could not read frame"}
                cap.release()
                continue
            
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Successfully opened {device}")
            logger.info(f"Resolution: {width}x{height}, FPS: {fps}")
            
            # Save a test image
            test_image_path = f"{os.path.basename(device)}_test.jpg"
            cv2.imwrite(test_image_path, frame)
            logger.info(f"Saved test image to {test_image_path}")
            
            results[device] = {
                "status": "success",
                "width": width,
                "height": height,
                "fps": fps,
                "image": test_image_path
            }
            
            # Release the camera
            cap.release()
            
        except Exception as e:
            logger.error(f"Error testing {device}: {e}")
            results[device] = {"status": "error", "error": str(e)}
    
    return results

def test_with_gstreamer():
    """Test using GStreamer pipelines"""
    devices = [1, 2, 20, 19]  # Device numbers to try
    results = {}
    
    for device_num in devices:
        device = f"/dev/video{device_num}"
        logger.info(f"Testing GStreamer with device: {device}")
        
        # Try different GStreamer pipelines
        pipelines = [
            f"v4l2src device={device} ! videoconvert ! appsink",
            f"v4l2src device={device} ! video/x-raw,format=YUY2 ! videoconvert ! appsink",
            f"v4l2src device={device} ! video/x-raw,format=MJPG ! jpegdec ! videoconvert ! appsink"
        ]
        
        success = False
        for pipeline in pipelines:
            try:
                logger.info(f"Trying pipeline: {pipeline}")
                cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                
                if not cap.isOpened():
                    logger.warning(f"Could not open with pipeline: {pipeline}")
                    cap.release()
                    continue
                
                # Try to read a frame
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Could not read frame with pipeline: {pipeline}")
                    cap.release()
                    continue
                
                # Get camera properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                logger.info(f"Successfully opened {device} with GStreamer")
                logger.info(f"Resolution: {width}x{height}")
                
                # Save a test image
                test_image_path = f"gst_{os.path.basename(device)}_test.jpg"
                cv2.imwrite(test_image_path, frame)
                logger.info(f"Saved test image to {test_image_path}")
                
                results[device] = {
                    "status": "success",
                    "pipeline": pipeline,
                    "width": width,
                    "height": height,
                    "image": test_image_path
                }
                
                success = True
                cap.release()
                break
                
            except Exception as e:
                logger.error(f"Error with pipeline {pipeline}: {e}")
        
        if not success:
            results[device] = {"status": "failed", "error": "All pipelines failed"}
    
    return results

def update_config(working_device=None, working_pipeline=None):
    """Update the config file with working camera settings"""
    if not working_device and not working_pipeline:
        logger.warning("No working camera configuration found")
        return False
    
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
            
        if "vision" not in config:
            config["vision"] = {}
            
        # Update with working device
        if working_device:
            if working_device.startswith("/dev/video"):
                device_index = int(working_device.replace("/dev/video", ""))
                config["vision"]["camera_index"] = device_index
                logger.info(f"Updated config with camera_index: {device_index}")
                
        # Update with working pipeline
        if working_pipeline:
            config["vision"]["gstreamer_pipeline"] = working_pipeline
            config["vision"]["use_gstreamer"] = True
            logger.info(f"Updated config with GStreamer pipeline")
            
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        logger.info(f"Saved updated configuration to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting device-specific camera tests...")
    
    # Test specific devices
    logger.info("\n=== Testing specific devices ===")
    device_results = test_specific_devices()
    
    # Test with GStreamer
    logger.info("\n=== Testing with GStreamer ===")
    gstreamer_results = test_with_gstreamer()
    
    # Find working configurations
    working_device = None
    working_pipeline = None
    
    for device, result in device_results.items():
        if result.get("status") == "success":
            working_device = device
            logger.info(f"Found working device: {device}")
            break
            
    for device, result in gstreamer_results.items():
        if result.get("status") == "success":
            working_pipeline = result.get("pipeline")
            logger.info(f"Found working GStreamer pipeline for {device}: {working_pipeline}")
            break
    
    # Update config if we found a working configuration
    if working_device or working_pipeline:
        update_config(working_device, working_pipeline)
    
    # Print summary
    logger.info("\n=== Test Results Summary ===")
    logger.info("Direct device access results:")
    for device, result in device_results.items():
        status = result.get("status", "unknown")
        if status == "success":
            logger.info(f"  {device}: SUCCESS - {result.get('width')}x{result.get('height')} @ {result.get('fps')} fps")
        else:
            logger.info(f"  {device}: FAILED - {result.get('error', 'Unknown error')}")
    
    logger.info("\nGStreamer results:")
    for device, result in gstreamer_results.items():
        status = result.get("status", "unknown")
        if status == "success":
            logger.info(f"  {device}: SUCCESS - {result.get('width')}x{result.get('height')} with pipeline: {result.get('pipeline')}")
        else:
            logger.info(f"  {device}: FAILED - {result.get('error', 'Unknown error')}")
    
    # Provide recommendations
    logger.info("\n=== Recommendations ===")
    if working_device:
        logger.info(f"1. Use direct access to {working_device}")
        if working_device.startswith("/dev/video"):
            device_index = int(working_device.replace("/dev/video", ""))
            logger.info(f"   Set camera_index to {device_index} in your code or config")
    elif working_pipeline:
        logger.info(f"1. Use GStreamer pipeline: {working_pipeline}")
        logger.info(f"   Set use_gstreamer=True and gstreamer_pipeline in your code or config")
    else:
        logger.info("1. Check if the camera is properly connected")
        logger.info("2. Enable the camera in raspi-config: sudo raspi-config")
        logger.info("3. Install necessary packages: sudo apt-get install -y libv4l-dev v4l-utils")
        logger.info("4. Reboot the Raspberry Pi: sudo reboot")
    
    logger.info("\nTest complete.")

if __name__ == "__main__":
    main()
