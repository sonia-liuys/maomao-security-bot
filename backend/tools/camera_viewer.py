#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Camera Viewer - Display camera feed with recognition labels
攝像頭查看器 - 顯示攝像頭畫面和識別標籤
"""

import cv2
import sys
import time
import os
import numpy as np
import logging
from datetime import datetime

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.vision_system import VisionSystem
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

# Setup logging
logger = setup_logger()

class CameraViewer:
    """Camera viewer class to display camera feed with recognition labels
    攝像頭查看器類，用於顯示攝像頭畫面和識別標籤"""
    
    def __init__(self, config):
        """Initialize camera viewer
        初始化攝像頭查看器
        
        Args:
            config (dict): Configuration dictionary
            config (dict): 配置字典
        """
        self.logger = logging.getLogger("CameraViewer")
        self.config = config
        
        # Initialize vision system
        self.logger.info("Initializing vision system...")
        self.logger.info("初始化視覺系統...")
        self.vision_system = VisionSystem(config["vision"])
        
        # Window name
        self.window_name = "Maomao Security Robot - Camera Feed"
        
        # Font settings for OpenCV
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.7
        self.font_thickness = 2
        self.text_color = (0, 255, 0)  # Green
        self.text_color_alert = (0, 0, 255)  # Red
        
        self.running = False
    
    def start(self):
        """Start the camera viewer
        啟動攝像頭查看器"""
        if self.running:
            return
            
        self.logger.info("Starting camera viewer...")
        self.logger.info("啟動攝像頭查看器...")
        
        # Start vision system
        self.vision_system.start()
        
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 600)
        
        self.running = True
        
        # Main loop
        try:
            while self.running:
                # Get latest frame and data
                frame = self.vision_system.get_latest_frame()
                data = self.vision_system.get_latest_data()
                
                if frame is not None:
                    # Draw recognition results on frame
                    self._draw_recognition_results(frame, data)
                    
                    # Show frame
                    cv2.imshow(self.window_name, frame)
                    
                    # Check for key press (ESC to exit)
                    key = cv2.waitKey(1) & 0xFF
                    if key == 27:  # ESC key
                        break
                
                # Sleep to reduce CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received, stopping...")
            self.logger.info("收到鍵盤中斷，正在停止...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the camera viewer
        停止攝像頭查看器"""
        if not self.running:
            return
            
        self.logger.info("Stopping camera viewer...")
        self.logger.info("停止攝像頭查看器...")
        
        # Stop vision system
        self.vision_system.stop()
        
        # Close window
        cv2.destroyAllWindows()
        
        self.running = False
        self.logger.info("Camera viewer stopped")
        self.logger.info("攝像頭查看器已停止")
    
    def _draw_recognition_results(self, frame, data):
        """Draw recognition results on frame
        在畫面上繪製識別結果
        
        Args:
            frame: The camera frame
            data (dict): Recognition data
            
            frame: 攝像頭畫面
            data (dict): 識別數據
        """
        # Draw timestamp
        timestamp = datetime.fromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), self.font, self.font_scale, self.text_color, self.font_thickness)
        
        # Draw face detection results
        if data["face_detected"]:
            # Calculate face position in pixels
            height, width = frame.shape[:2]
            face_x = int(data["face_x"] * width)
            face_y = int(data["face_y"] * height)
            
            # Draw circle at face position
            cv2.circle(frame, (face_x, face_y), 20, self.text_color, 2)
            
            # Draw recognized person
            if data["recognized_person"]:
                text = f"Person: {data['recognized_person']}"
                confidence = f"Confidence: {data['confidence']:.2f}"
                cv2.putText(frame, text, (10, 70), self.font, self.font_scale, self.text_color, self.font_thickness)
                cv2.putText(frame, confidence, (10, 100), self.font, self.font_scale, self.text_color, self.font_thickness)
            else:
                text = "Unknown Person"
                cv2.putText(frame, text, (10, 70), self.font, self.font_scale, self.text_color_alert, self.font_thickness)
            
            # Draw student ID detection
            if data["student_id_detected"]:
                text = f"Student ID: {data['recognized_person']}"
                cv2.putText(frame, text, (10, 130), self.font, self.font_scale, self.text_color, self.font_thickness)
        else:
            # No face detected
            cv2.putText(frame, "No face detected", (10, 70), self.font, self.font_scale, self.text_color, self.font_thickness)

def main():
    """Main function
    主函數"""
    logger.info("Starting camera viewer application...")
    logger.info("啟動攝像頭查看器應用程序...")
    
    # Load configuration
    config = ConfigLoader().load_config()
    logger.info(f"Loaded configuration: {config['robot']['name']}")
    logger.info(f"已載入配置: {config['robot']['name']}")
    
    # Override model path to use test_model and test_labels
    config['vision']['model_path'] = "models/test_model.tflite"
    logger.info(f"Using test model: {config['vision']['model_path']}")
    logger.info(f"使用測試模型: {config['vision']['model_path']}")
    
    # Create a custom labels file path that will be used by the vision system
    # The vision system looks for labels.txt in the same directory as the model file
    # So we need to create a symlink or copy the test_labels.txt to the right location
    import shutil
    import os
    
    # Get the directory of the model file
    model_dir = os.path.dirname(os.path.join(os.getcwd(), config['vision']['model_path']))
    labels_path = os.path.join(model_dir, "labels.txt")
    test_labels_path = os.path.join(model_dir, "test_labels.txt")
    
    # Backup original labels.txt if it exists and we haven't backed it up yet
    backup_path = os.path.join(model_dir, "labels.txt.backup")
    if os.path.exists(labels_path) and not os.path.exists(backup_path):
        logger.info(f"Backing up original labels file to: {backup_path}")
        logger.info(f"備份原始標籤文件到: {backup_path}")
        shutil.copy2(labels_path, backup_path)
    
    # Copy test_labels.txt to labels.txt
    if os.path.exists(test_labels_path):
        logger.info(f"Copying test labels from {test_labels_path} to {labels_path}")
        logger.info(f"從 {test_labels_path} 複製測試標籤到 {labels_path}")
        shutil.copy2(test_labels_path, labels_path)
    else:
        logger.warning(f"Test labels file not found: {test_labels_path}")
        logger.warning(f"找不到測試標籤文件: {test_labels_path}")
    
    # Create and start camera viewer
    viewer = CameraViewer(config)
    
    try:
        viewer.start()
    except Exception as e:
        logger.error(f"Error in camera viewer: {e}")
        logger.error(f"攝像頭查看器錯誤: {e}")
    finally:
        viewer.stop()

if __name__ == "__main__":
    main()
