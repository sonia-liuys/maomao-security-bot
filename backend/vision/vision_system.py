#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vision System - Process camera input and AI recognition
視覺系統 - 處理攝像頭輸入和AI識別
"""

import logging
import threading
import time
import cv2
import numpy as np
import os
import platform
from datetime import datetime

# Real TensorFlow Lite import for actual deployment
# 實際部署時使用真實的 TensorFlow Lite

# Try to import TensorFlow Lite, fall back to simulation if not available
# 嘗試導入 TensorFlow Lite，如果不可用則回退到模擬

try:
    # Try to import TensorFlow Lite
    import tensorflow as tf
    print("Successfully imported TensorFlow version:", tf.__version__)
    HAVE_TENSORFLOW = True
except ImportError as e:
    print(f"Failed to import TensorFlow: {e}")
    HAVE_TENSORFLOW = False
    
class TFLiteModel:
    """Real TensorFlow Lite model class with fallback to simulation
真實的 TensorFlow Lite 模型類，帶有回退到模擬的功能"""
    
    def __init__(self, model_path):
        self.model_path = model_path
        self.logger = logging.getLogger("TFLiteModel")
        self.logger.info(f"載入模型: {model_path}")
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        
        # Try to load the real model if TensorFlow is available
        if HAVE_TENSORFLOW:
            try:
                self.logger.info("Using real TensorFlow Lite model")
                self.logger.info("使用真實的 TensorFlow Lite 模型")
                self.interpreter = tf.lite.Interpreter(model_path=model_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                self.logger.info(f"Model loaded successfully. Input shape: {self.input_details[0]['shape']}")
                self.logger.info(f"模型載入成功。輸入形狀: {self.input_details[0]['shape']}")
            except Exception as e:
                self.logger.error(f"Error loading TensorFlow Lite model: {e}")
                self.logger.error(f"載入 TensorFlow Lite 模型時出錯: {e}")
                self.interpreter = None
        else:
            self.logger.warning("TensorFlow not available, using simulation mode")
            self.logger.warning("TensorFlow 不可用，使用模擬模式")
    
    def predict(self, image):
        """Run model prediction on an image
        
        Args:
            image: Input image (numpy array)
            
        Returns:
            list: Prediction probabilities for each class
            
        對圖像進行模型預測
        
        Args:
            image: 輸入圖像（numpy 數組）
            
        Returns:
            list: 各類別的預測概率
        """
        # For debugging
        self.logger.info(f"Image shape: {image.shape}")
        
        # If we have a real TensorFlow Lite model, use it
        if self.interpreter is not None:
            try:
                # Preprocess the image to match the model's input shape
                input_shape = self.input_details[0]['shape'][1:3]  # Height, width
                
                # Check if we need to resize the image
                if input_shape[0] != image.shape[0] or input_shape[1] != image.shape[1]:
                    self.logger.info(f"Resizing image from {image.shape[:2]} to {input_shape}")
                    image = cv2.resize(image, (input_shape[1], input_shape[0]))
                
                # Normalize the image (0-1 range)
                processed_image = image.astype(np.float32) / 255.0
                
                # Add batch dimension
                input_data = np.expand_dims(processed_image, axis=0)
                
                # Set the input tensor
                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
                
                # Run inference
                self.logger.info("Running model inference...")
                self.interpreter.invoke()
                
                # Get the output tensor
                output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
                
                # Get probabilities
                probabilities = output_data[0]
                
                # Log the shape and values of the output
                self.logger.info(f"Output shape: {output_data.shape}")
                self.logger.info(f"Real model prediction: {probabilities}")
                
                # Return the probabilities
                return probabilities
            except Exception as e:
                self.logger.error(f"Error during model inference: {e}")
                self.logger.error(f"模型推理時出錯: {e}")
                # Fall back to simulation
        
        # Fallback: Simulation mode
        self.logger.warning("Using simulation mode for prediction")
        self.logger.warning("使用模擬模式進行預測")
        
        return self._simulate_prediction(image)
    
    def _simulate_prediction(self, image):
        """Simulate model prediction based on image characteristics
        
        Args:
            image: Input image
            
        Returns:
            list: Simulated prediction probabilities
            
        基於圖像特徵模擬模型預測
        
        Args:
            image: 輸入圖像
            
        Returns:
            list: 模擬的預測概率
        """
        height, width, _ = image.shape
        
        # Divide the image into regions
        # 將圖像分為區域
        left_region = image[0:height, 0:width//3]
        middle_region = image[0:height, width//3:2*width//3]
        right_region = image[0:height, 2*width//3:width]
        
        # Calculate average color in each region
        # 計算每個區域的平均顏色
        left_avg = np.mean(left_region, axis=(0,1))
        middle_avg = np.mean(middle_region, axis=(0,1))
        right_avg = np.mean(right_region, axis=(0,1))
        
        # Calculate average brightness in each region
        # 計算每個區域的平均亮度
        left_brightness = np.mean(cv2.cvtColor(left_region, cv2.COLOR_BGR2GRAY))
        middle_brightness = np.mean(cv2.cvtColor(middle_region, cv2.COLOR_BGR2GRAY))
        right_brightness = np.mean(cv2.cvtColor(right_region, cv2.COLOR_BGR2GRAY))
        
        self.logger.info(f"Brightness - Left: {left_brightness:.2f}, Middle: {middle_brightness:.2f}, Right: {right_brightness:.2f}")
        
        # Calculate color variance in each region
        # 計算每個區域的顏色方差
        left_variance = np.var(left_region, axis=(0,1)).sum()
        middle_variance = np.var(middle_region, axis=(0,1)).sum()
        right_variance = np.var(right_region, axis=(0,1)).sum()
        
        self.logger.info(f"Color variance - Left: {left_variance:.2f}, Middle: {middle_variance:.2f}, Right: {right_variance:.2f}")
        
        # 模擬更接近真實模型的預測結果
        # 檢測人臉特徵
        face_features = {
            "jeffrey": {
                "blue_dominant": left_avg[0] > left_avg[1] and left_avg[0] > left_avg[2],
                "variance_high": left_variance > 2500
            },
            "sonia": {
                "green_dominant": middle_avg[1] > middle_avg[0] and middle_avg[1] > middle_avg[2],
                "brightness_medium": 80 < middle_brightness < 150
            },
            "id_card": {
                "brightness_high": right_brightness > 120,
                "brightness_diff": right_brightness > left_brightness + 20 and right_brightness > middle_brightness + 20
            }
        }
        
        # 計算每個類別的分數
        jeffrey_score = 0.3  # 基礎分數
        sonia_score = 0.3    # 基礎分數
        id_score = 0.1       # 基礎分數
        
        # 根據特徵調整分數
        if face_features["jeffrey"]["blue_dominant"]:
            jeffrey_score += 0.3
            self.logger.info("Jeffrey feature: Blue dominant")
        if face_features["jeffrey"]["variance_high"]:
            jeffrey_score += 0.2
            self.logger.info("Jeffrey feature: High variance")
            
        if face_features["sonia"]["green_dominant"]:
            sonia_score += 0.3
            self.logger.info("Sonia feature: Green dominant")
        if face_features["sonia"]["brightness_medium"]:
            sonia_score += 0.2
            self.logger.info("Sonia feature: Medium brightness")
            
        if face_features["id_card"]["brightness_high"]:
            id_score += 0.4
            self.logger.info("ID card feature: High brightness")
        if face_features["id_card"]["brightness_diff"]:
            id_score += 0.3
            self.logger.info("ID card feature: Brightness difference")
        
        # 正規化分數為概率
        total = jeffrey_score + sonia_score + id_score
        jeffrey_prob = jeffrey_score / total
        sonia_prob = sonia_score / total
        id_prob = id_score / total
        
        # 輸出最終分類結果
        predictions = [jeffrey_prob, sonia_prob, id_prob]
        max_idx = np.argmax(predictions)
        class_names = ["Jeffrey", "Sonia", "Sonia_ID"]
        self.logger.info(f"Simulated classification: {class_names[max_idx]} with probability {predictions[max_idx]:.4f}")
        
        return predictions

class VisionSystem:
    """Vision System class, process camera input and AI recognition
視覺系統類，處理攝像頭輸入和AI識別"""
    
    def __init__(self, config):
        """Initialize vision system
初始化視覺系統
        
        Args:
            config (dict): 視覺系統配置
        """
        self.logger = logging.getLogger("Vision")
        self.config = config
        
        # Automatically select camera index based on platform
        default_camera = 1 if platform.system() == "Linux" and os.path.exists("/etc/rpi-issue") else 0
        self.logger.info(f"Detected platform: {platform.system()}, using default camera index: {default_camera}")
        self.logger.info(f"檢測到平台: {platform.system()}, 使用默認相機索引: {default_camera}")
        
        self.camera_index = config.get("camera_index", default_camera)
        self.logger.info(f"Final camera index from config: {self.camera_index}")
        self.logger.info(f"配置中的最終相機索引: {self.camera_index}")
        
        self.frame_width = config.get("frame_width", 640)
        self.frame_height = config.get("frame_height", 480)
        self.confidence_threshold = config.get("confidence_threshold", 0.9)  # 提高置信度閾值到 90%
        
        # Initialize status variables
# 初始化狀態變數
        self.running = False
        self.camera = None
        self.latest_frame = None
        self.latest_data = {
            "timestamp": 0,
            "face_detected": False,
            "face_x": 0.5,  # 歸一化座標 (0-1)
            "face_y": 0.5,  # 歸一化座標 (0-1)
            "recognized_person": None,
            "student_id_detected": False,
            "confidence": 0.0
        }
        
        # Initialize face detector
# 初始化人臉檢測器
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Load AI model
# 載入AI模型
        self.logger.info("載入AI識別模型...")
        self.logger.info("Loading AI recognition model...")
        model_path = config.get("model_path", "models/teachable_machine_model.tflite")
        self.model = TFLiteModel(model_path)
        
        # Load labels from file
# 從文件中載入標籤
        self.logger.info("Loading labels from file...")
        self.logger.info("從文件中載入標籤...")
        labels_path = os.path.join(os.path.dirname(model_path), "labels.txt")
        self.class_names = []  # We'll populate this with labels from file
        
        try:
            if os.path.exists(labels_path):
                with open(labels_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        # Handle different label file formats
                        line = line.strip()
                        if ' ' in line:  # Format: "0 Label"
                            parts = line.split(' ', 1)
                            if len(parts) > 1:
                                self.class_names.append(parts[1])
                        else:  # Format: just "Label"
                            self.class_names.append(line)
                
                self.logger.info(f"Loaded {len(self.class_names)} labels from {labels_path}")
                self.logger.info(f"從 {labels_path} 載入了 {len(self.class_names)} 個標籤")
                self.logger.info(f"Labels: {self.class_names}")
                self.logger.info(f"標籤: {self.class_names}")
            else:
                self.logger.warning(f"Labels file not found: {labels_path}")
                self.logger.warning(f"找不到標籤文件: {labels_path}")
                # Fallback to default class names
                # 回退到默認類別名稱
                self.class_names = [
                    "Jeffrey",       # Jeffrey
                    "Sonia",         # Sonia
                    "Sonia_ID"       # Sonia's ID card
                ]
        except Exception as e:
            self.logger.error(f"Error loading labels: {e}")
            self.logger.error(f"載入標籤時出錯: {e}")
            # Fallback to default class names
            # 回退到默認類別名稱
            self.class_names = [
                "unknown",       # unknown / 未知
                "sonia_face",    # Sonia's face / Sonia的臉
                "matthew_face",  # Matthew's face / Matthew的臉
                "sonia_id",      # Sonia's student ID / Sonia的學生證
                "matthew_id"     # Matthew's student ID / Matthew的學生證
            ]
        
        # Processing thread
# 處理線程
        self.thread = None
        self.lock = threading.Lock()
        
        self.logger.info("Vision system initialization complete")
        self.logger.info("視覺系統初始化完成")
    
    def start(self):
        """Start the vision system
啟動視覺系統"""
        if self.running:
            return
            
        self.logger.info("Starting vision system...")
        self.logger.info(f"啟動視覺系統..., Camera Index: {self.camera_index}")
        
        # Open camera
        # 打開攝像頭
        self.camera = cv2.VideoCapture(self.camera_index)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        
        if not self.camera.isOpened():
            self.logger.error("Cannot open camera")
            self.logger.error("無法打開攝像頭")
            return
            
        self.running = True
        
        # Start processing thread
        # 啟動處理線程
        self.thread = threading.Thread(target=self._process_frames)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("Vision system started")
        self.logger.info("視覺系統已啟動")
    
    def stop(self):
        """Stop the vision system
停止視覺系統"""
        if not self.running:
            return
            
        self.logger.info("Stopping vision system...")
        self.logger.info("停止視覺系統...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
            
        if self.camera:
            self.camera.release()
            self.camera = None
            
        self.logger.info("Vision system stopped")
        self.logger.info("視覺系統已停止")
    
    def _process_frames(self):
        """Main loop for processing camera frames
處理攝像頭幀的主循環"""
        last_classification_time = 0
        classification_interval = 3.0  # 每3秒分類一次
        
        while self.running:
            current_time = time.time()
            
            # Read a frame
            # 讀取一幀
            ret, frame = self.camera.read()
            if not ret or frame is None:
                self.logger.warning("Cannot read camera frame")
                self.logger.warning("無法讀取攝像頭幀")
                time.sleep(0.1)
                continue
                
            # Update latest frame
            # 更新最新幀
            with self.lock:
                self.latest_frame = frame.copy()
            
            # 只在指定間隔時間進行分類
            if current_time - last_classification_time >= classification_interval:
                # Process frame
                # 處理幀
                self._analyze_frame(frame)
                last_classification_time = current_time
                self.logger.info(f"Classification performed at {datetime.now().strftime('%H:%M:%S')}")
            
            # Control frame capture frequency
            # 控制幀捕獲頻率
            time.sleep(0.03)  # 約30fps的幀捕獲率
    
    def _analyze_frame(self, frame):
        """Analyze a frame
        
        Args:
            frame: The image frame to analyze
            
        分析一幀圖像
        
        Args:
            frame: 要分析的圖像幀
        """
        # Convert to grayscale for face detection
        # 轉換為灰度圖像用於人臉檢測
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces (still used for face position tracking)
        # 檢測人臉（仍用於人臉位置追蹤）
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )
        
        # Initialize data dictionary
        # 初始化數據字典
        data = {
            "timestamp": time.time(),
            "face_detected": len(faces) > 0,
            "face_x": 0.5,  # Default center
            "face_y": 0.5,  # Default center
            "recognized_person": None,
            "student_id_detected": False,
            "confidence": 0.0
        }
        
        # If no faces detected, return early
        # 如果沒有檢測到人臉，提前返回
        if len(faces) == 0:
            # Update latest data
            # 更新最新數據
            with self.lock:
                self.latest_data = data
            return
            
        # Process the largest face
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, w, h = largest_face
        # Calculate face center position (normalized 0-1)
        frame_w = getattr(self, 'frame_width', frame.shape[1]) or frame.shape[1]
        frame_h = getattr(self, 'frame_height', frame.shape[0]) or frame.shape[0]
        if frame_w == 0: frame_w = frame.shape[1]
        if frame_h == 0: frame_h = frame.shape[0]
        face_center_x = (x + w/2) / frame_w
        face_center_y = (y + h/2) / frame_h
        face_center_x = max(0.0, min(1.0, face_center_x))
        face_center_y = max(0.0, min(1.0, face_center_y))
        data["face_x"] = face_center_x
        data["face_y"] = face_center_y
        # English: Save normalized face center position to data dict for downstream tracking
        # 中文：將正規化的人臉中心位置寫入 data 字典，供後續追蹤用
        
        # Resize frame to match model input size
        # 調整幀大小以匹配模型輸入大小
        resized_frame = cv2.resize(frame, (224, 224))
        
        # Get model predictions
        # 獲取模型預測
        predictions = self.model.predict(resized_frame)
        
        # Find the class with highest probability
        # 找到概率最高的類別
        max_prob_idx = np.argmax(predictions)
        max_prob = predictions[max_prob_idx]
        
        # Check if confidence is above threshold
        # 檢查置信度是否高於閾值
        if max_prob >= self.confidence_threshold:
            class_name = self.class_names[max_prob_idx]
            self.logger.info(f"Recognized class: {class_name}, index: {max_prob_idx}, probability: {max_prob:.4f}")
            self.logger.info(f"識別出的類別: {class_name}, 索引: {max_prob_idx}, 概率: {max_prob:.4f}")
            
            # 只將 Sonia 視為已知人員，其他人都視為未知人員
            if "sonia" in class_name.lower() and "id" not in class_name.lower() and "card" not in class_name.lower():
                self.logger.info("Recognized Sonia as known person")
                self.logger.info("識別出 Sonia 為已知人員")
                data["recognized_person"] = "Sonia"
            else:
                # Jeffrey 和其他人都視為未知人員
                if "jeffrey" in class_name.lower():
                    self.logger.info("Jeffrey is treated as unknown person")
                    self.logger.info("Jeffrey 被視為未知人員")
                    # 確保 recognized_person 是 None，使 mode_manager 將其視為未知人員
                    data["recognized_person"] = None
            
            # 檢查是否識別出學生證
            if "id" in class_name.lower() or "card" in class_name.lower():
                self.logger.info(f"Detected student ID card: {class_name}")
                self.logger.info(f"檢測到學生證: {class_name}")
                
                # 只有 Sonia 的學生證才被認可
                if "sonia" in class_name.lower():
                    self.logger.info("Recognized Sonia's student ID")
                    self.logger.info("識別出 Sonia 的學生證")
                    data["recognized_person"] = "Sonia"
                    data["student_id_detected"] = True
                
                # Special case for test model: only Sonia is recognized as known person
                # 測試模型的特殊情況：只有 Sonia 被識別為已知人員
                if class_name == "Sonia":
                    data["recognized_person"] = "Sonia"
                elif class_name == "Sonia_ID":
                    data["recognized_person"] = "Sonia"
                    data["student_id_detected"] = True
                elif class_name == "Jeffrey":
                    # 確保 Jeffrey 被視為未知人員
                    self.logger.info("Jeffrey is treated as unknown person (special case)")
                    self.logger.info("Jeffrey 被視為未知人員（特殊情況）")
                    data["recognized_person"] = None
            
            data["confidence"] = float(max_prob)
        
        # Update latest data
        # 更新最新數據
        with self.lock:
            self.latest_data = data
    
    def get_latest_data(self):
        """Get the latest vision data
        
        Returns:
            dict: The latest vision data
            
        獲取最新的視覺數據
        
        Returns:
            dict: 最新的視覺數據
        """
        with self.lock:
            return self.latest_data.copy()
    
    def get_latest_frame(self):
        """Get the latest camera frame
        
        Returns:
            numpy.ndarray: The latest camera frame, or None if not available
            
        獲取最新的攝像頭幀
        
        Returns:
            numpy.ndarray: 最新的攝像頭幀，如果沒有則返回None
        """
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()
    
    def get_timestamp(self):
        """Get the timestamp of the latest data
        
        Returns:
            float: Timestamp
            
        獲取最新數據的時間戳
        
        Returns:
            float: 時間戳
        """
        with self.lock:
            return self.latest_data["timestamp"]
    
    def get_status(self):
        """Get vision system status
        獲取視覺系統狀態
        
        Returns:
            dict: Vision system status
            dict: 視覺系統狀態
        """
        with self.lock:
            latest_data = self.latest_data
            # 首先記錄最新数据中的值
            # First log the values in the latest data
            self.logger.info(f"VisionSystem.get_status: latest_data = {latest_data}")
            
            # 初始化狀態字典
            # Initialize status dictionary
            status = {
                "camera_active": self.camera is not None and self.camera.isOpened(),
                "resolution": f"{self.frame_width}x{self.frame_height}",
                "face_detected": latest_data["face_detected"],
                "recognized_person": latest_data["recognized_person"],
                "student_id_detected": latest_data["student_id_detected"],
                "confidence": latest_data["confidence"]
            }
            
            # 添加人臉座標
            # Add face coordinates
            if "face_x" in latest_data and "face_y" in latest_data:
                try:
                    status["face_x"] = latest_data["face_x"]
                    status["face_y"] = latest_data["face_y"]
                    self.logger.info(f"VisionSystem.get_status: 添加人臉座標到狀態中: x={status['face_x']:.2f}, y={status['face_y']:.2f}")
                    self.logger.info(f"VisionSystem.get_status: Adding face coordinates to status: x={status['face_x']:.2f}, y={status['face_y']:.2f}")
                except Exception as e:
                    self.logger.error(f"VisionSystem.get_status: 提取人臉座標時出錯: {e}")
                    self.logger.error(f"VisionSystem.get_status: Error extracting face coordinates: {e}")
            else:
                self.logger.warning("VisionSystem.get_status: latest_data 中沒有人臉座標信息")
                self.logger.warning("VisionSystem.get_status: No face coordinates in latest_data")
            
            self.logger.info(f"VisionSystem.get_status: 返回狀態 = {status}")
            return status
    
    def get_latest_data(self):
        """Get the latest vision data
        
        Returns:
            dict: The latest vision data
            
        獲取最新的視覺數據
        
        Returns:
            dict: 最新的視覺數據
        """
        with self.lock:
            return self.latest_data.copy()
    
    def get_latest_frame(self):
        """Get the latest camera frame
        
        Returns:
            numpy.ndarray: The latest camera frame, or None if not available
            
        獲取最新的攝像頭幀
        
        Returns:
            numpy.ndarray: 最新的攝像頭幀，如果沒有則返回None
        """
        with self.lock:
            if self.latest_frame is None:
                return None
            return self.latest_frame.copy()
    
    def get_timestamp(self):
        """Get the timestamp of the latest data
        
        Returns:
            float: Timestamp
            
        獲取最新數據的時間戳
        
        Returns:
            float: 時間戳
        """
        with self.lock:
            return self.latest_data["timestamp"]
    
    