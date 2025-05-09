#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Camera Test Script - Test if camera and TensorFlow Lite model are working
相機測試腳本 - 測試相機和 TensorFlow Lite 模型是否正常工作
"""

import cv2
import numpy as np
import os
import time
import tensorflow as tf
import argparse
from datetime import datetime

# Parse command line arguments
parser = argparse.ArgumentParser(description='Test camera and TensorFlow Lite model')
parser.add_argument('--camera', type=int, default=0, help='Camera index to use (default: 0)')
parser.add_argument('--model', type=str, default='models/teachable_machine_model.tflite', 
                    help='Path to TFLite model (default: models/teachable_machine_model.tflite)')
parser.add_argument('--labels', type=str, default='models/labels.txt', 
                    help='Path to labels file (default: models/labels.txt)')
parser.add_argument('--width', type=int, default=640, help='Camera frame width (default: 640)')
parser.add_argument('--height', type=int, default=480, help='Camera frame height (default: 480)')
parser.add_argument('--threshold', type=float, default=0.7, help='Confidence threshold (default: 0.7)')
parser.add_argument('--no-display', action='store_true', help='Run without display (for headless systems)')
args = parser.parse_args()

def load_labels(label_path):
    """Load labels from file"""
    print(f"載入標籤文件: {label_path}")
    print(f"Loading labels from: {label_path}")
    try:
        with open(label_path, 'r') as f:
            labels = [line.strip() for line in f.readlines()]
        print(f"載入了 {len(labels)} 個標籤: {labels}")
        print(f"Loaded {len(labels)} labels: {labels}")
        return labels
    except Exception as e:
        print(f"載入標籤文件時出錯: {e}")
        print(f"Error loading labels: {e}")
        return ["Class 1", "Class 2"]  # Default labels

def load_model(model_path):
    """Load TensorFlow Lite model"""
    print(f"載入模型: {model_path}")
    print(f"Loading model: {model_path}")
    try:
        interpreter = tf.lite.Interpreter(model_path=model_path)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        input_shape = input_details[0]['shape'][1:3]  # Height, width
        print(f"模型輸入形狀: {input_shape}")
        print(f"Model input shape: {input_shape}")
        
        return interpreter, input_details, output_details, input_shape
    except Exception as e:
        print(f"載入模型時出錯: {e}")
        print(f"Error loading model: {e}")
        return None, None, None, (224, 224)

def predict(interpreter, input_details, output_details, image):
    """Run model prediction on image"""
    try:
        # Set the input tensor
        interpreter.set_tensor(input_details[0]['index'], image)
        
        # Run inference
        interpreter.invoke()
        
        # Get output tensor
        output_data = interpreter.get_tensor(output_details[0]['index'])
        
        return output_data[0]
    except Exception as e:
        print(f"預測時出錯: {e}")
        print(f"Error during prediction: {e}")
        return [0.5, 0.5]  # Default prediction

def main():
    """Main function"""
    print("相機測試腳本啟動")
    print("Camera Test Script started")
    
    # Load labels
    labels = load_labels(args.labels)
    
    # Load model
    interpreter, input_details, output_details, input_shape = load_model(args.model)
    if interpreter is None:
        print("無法載入模型，僅測試相機")
        print("Could not load model, testing camera only")
    
    # Initialize camera
    print(f"嘗試開啟相機 (索引: {args.camera})")
    print(f"Trying to open camera (index: {args.camera})")
    cap = cv2.VideoCapture(args.camera)
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print(f"錯誤: 無法開啟相機 {args.camera}")
        print(f"Error: Could not open camera {args.camera}")
        print("請嘗試不同的相機索引: 0, 1, 2, 等")
        print("Try different camera indices: 0, 1, 2, etc.")
        return
    
    print("相機開啟成功！")
    print("Camera opened successfully!")
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    
    # Get actual width and height (might be different from requested)
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"相機解析度: {actual_width}x{actual_height}")
    print(f"Camera resolution: {actual_width}x{actual_height}")
    
    frame_count = 0
    start_time = time.time()
    fps = 0
    
    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print("無法從相機獲取幀")
                print("Failed to get frame from camera")
                break
            
            # Calculate FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:
                fps = frame_count / elapsed_time
                frame_count = 0
                start_time = time.time()
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Process image if model is loaded
            if interpreter is not None:
                # Prepare image for model
                resized_frame = cv2.resize(frame, (input_shape[1], input_shape[0]))
                normalized_frame = resized_frame.astype(np.float32) / 255.0
                input_data = np.expand_dims(normalized_frame, axis=0)
                
                # Run inference
                predictions = predict(interpreter, input_details, output_details, input_data)
                
                # Get top prediction
                top_index = np.argmax(predictions)
                top_confidence = predictions[top_index]
                
                # Display prediction if confidence is above threshold
                if top_confidence > args.threshold:
                    label_text = f"{labels[top_index]}: {top_confidence:.2f}"
                    
                    # Check if the recognized label contains 'sonia' (based on your memory)
                    if 'sonia' in labels[top_index].lower():
                        color = (0, 255, 0)  # Green for Sonia
                    else:
                        color = (0, 0, 255)  # Red for others
                    
                    cv2.putText(frame, label_text, (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
            # Add FPS counter
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, frame.shape[0] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Add timestamp
            cv2.putText(frame, timestamp, (frame.shape[1] - 230, frame.shape[0] - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display the frame
            if not args.no_display:
                cv2.imshow('Camera Test', frame)
                
                # Press 'q' to exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                # Print results to console in headless mode
                if interpreter is not None:
                    top_index = np.argmax(predictions)
                    print(f"Top prediction: {labels[top_index]} ({predictions[top_index]:.2f})")
                
                # Slow down the loop in headless mode
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("程序被用戶中斷")
        print("Program interrupted by user")
    except Exception as e:
        print(f"發生錯誤: {e}")
        print(f"An error occurred: {e}")
    finally:
        # Release resources
        cap.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        print("相機測試腳本結束")
        print("Camera Test Script ended")

if __name__ == "__main__":
    main()
