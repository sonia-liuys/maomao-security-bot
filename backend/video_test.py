#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Simple WebSocket video streaming server for Raspberry Pi
# 樹莓派簡易WebSocket視頻流服務器
"""
Video Test Script - Test video streaming with WebSocket
視頻測試腳本 - 測試帶有WebSocket的視頻流
"""

import cv2
import base64
import json
import asyncio
import websockets
import time
import logging
import argparse
import platform
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VideoTest")

async def send_video_frames(websocket, camera_index=None):
    """Send video frames through WebSocket"""
    logger.info("Starting video streaming test")
    
    # Determine camera index based on platform
    if camera_index is None:
        default_camera = 1 if platform.system() == "Linux" and os.path.exists("/etc/rpi-issue") else 0
        camera_index = default_camera
        logger.info(f"Using default camera index for this platform: {camera_index}")
    
    # Open camera
    logger.info(f"Opening camera with index: {camera_index}")
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        logger.error(f"Failed to open camera with index {camera_index}")
        await websocket.send(json.dumps({
            "type": "error",
            "data": {
                "message": f"Failed to open camera with index {camera_index}"
            }
        }))
        return
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Get actual width and height
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logger.info(f"Camera resolution: {width}x{height}")
    
    # Initialize face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    try:
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                logger.error("Failed to capture frame")
                await asyncio.sleep(0.1)
                continue
            
            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time
                logger.info(f"FPS: {fps:.1f}")
                frame_count = 0
                start_time = time.time()
            
            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Initialize face data
            face_detected = False
            face_x = 0.5  # Default center
            face_y = 0.5  # Default center
            
            # Draw rectangles around faces and update face coordinates
            for (x, y, w, h) in faces:
                # Draw rectangle
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Update face data (use center of the face)
                face_detected = True
                face_x = (x + w/2) / width  # Normalize to 0-1
                face_y = (y + h/2) / height  # Normalize to 0-1
                
                # Only use the first face
                break
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(frame, timestamp, (10, height - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Encode frame to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            
            # Create message with face detection data
            current_time = time.time() * 1000  # milliseconds
            message = {
                "type": "video_frame",
                "data": {
                    "image": jpg_as_text,
                    "timestamp": current_time,
                    "width": width,
                    "height": height,
                    "face_detected": face_detected,
                    "face_x": face_x,
                    "face_y": face_y
                }
            }
            
            # Also send status update with face data
            status_message = {
                "type": "status_update",
                "data": {
                    "timestamp": current_time,
                    "face_detected": face_detected,
                    "face_x": face_x,
                    "face_y": face_y,
                    "recognized_person": "Test Person" if face_detected else None,
                    "confidence": 0.95 if face_detected else 0.0
                }
            }
            
            # Send video frame
            try:
                await websocket.send(json.dumps(message))
                
                # Send status update every 5 frames
                if frame_count % 5 == 0:
                    await websocket.send(json.dumps(status_message))
                    logger.info(f"Sent status update: face_detected={face_detected}, face_x={face_x:.2f}, face_y={face_y:.2f}")
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket connection closed")
                break
            
            # Sleep to control frame rate
            await asyncio.sleep(0.1)  # Approx 10 FPS
    
    except Exception as e:
        logger.error(f"Error in video streaming: {e}")
    finally:
        # Release camera
        cap.release()
        logger.info("Camera released")

async def handle_client(websocket, path):
    """Handle WebSocket client connection"""
    logger.info(f"Client connected from {websocket.remote_address}, path: {path}")
    
    try:
        # Wait for commands
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received command: {data}")
                
                if data.get('type') == 'start_video_stream':
                    logger.info("Starting video stream")
                    await websocket.send(json.dumps({
                        "type": "status",
                        "data": {
                            "message": "Starting video stream"
                        }
                    }))
                    await send_video_frames(websocket)
                
                elif data.get('type') == 'stop_video_stream':
                    logger.info("Stopping video stream")
                    await websocket.send(json.dumps({
                        "type": "status",
                        "data": {
                            "message": "Video stream stopped"
                        }
                    }))
                
                elif data.get('type') == 'ping':
                    # Respond to ping
                    await websocket.send(json.dumps({
                        "type": "pong",
                        "data": {
                            "timestamp": data.get('data', {}).get('timestamp', time.time() * 1000)
                        }
                    }))
                
                else:
                    logger.warning(f"Unknown command: {data.get('type')}")
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {message}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info("Connection closed")
    except Exception as e:
        logger.error(f"Error handling client: {e}")

async def main(port=8765, camera_index=None):
    """Main function"""
    logger.info(f"Starting WebSocket server on port {port}")
    logger.info(f"Using camera index: {camera_index if camera_index is not None else 'auto-detect'}")
    
    # Check websockets version to determine the correct way to start the server
    import websockets
    ws_version = tuple(map(int, websockets.__version__.split('.')))
    
    if ws_version >= (10, 0):
        # For websockets 10.0 and above, use the new API
        logger.info(f"Using websockets version {websockets.__version__} with new API")
        async with websockets.serve(handle_client, "0.0.0.0", port):
            logger.info(f"WebSocket server started on port {port}")
            try:
                # Keep the server running
                await asyncio.Future()  # Run forever
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
            finally:
                logger.info("Server stopped")
    else:
        # For older versions of websockets
        logger.info(f"Using websockets version {websockets.__version__} with legacy API")
        server = await websockets.serve(handle_client, "0.0.0.0", port)
        logger.info(f"WebSocket server started on port {port}")
        
        try:
            await asyncio.get_event_loop().create_future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        finally:
            server.close()
            await server.wait_closed()
            logger.info("Server stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video streaming test with WebSocket")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port")
    parser.add_argument("--camera", type=int, help="Camera index (default: auto-detect)")
    args = parser.parse_args()
    
    asyncio.run(main(args.port, args.camera))
