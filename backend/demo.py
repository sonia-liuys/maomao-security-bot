#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
毛毛安全機器人演示程式 - 隨機動作、人臉追蹤和音效播放
MaoMao Security Robot Demo - Random movements, face tracking and sound effects
"""

import cv2
import numpy as np
import random
import time
import threading
import logging
import os
import sys
import json
import pygame
from datetime import datetime
import colorama
from colorama import Fore, Back, Style

# 導入機器人控制器組件
from servo.servo_controller import ServoController
from vision.vision_system import VisionSystem
from utils.config_loader import ConfigLoader

# 初始化 colorama
colorama.init(autoreset=True)

# 自定義日誌格式化器，支持顏色
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.WHITE
    }
    
    def format(self, record):
        # 保存原始消息
        original_msg = record.msg
        
        # 檢查是否包含特殊標記，用於人臉追蹤位置
        if '[FACE_X]' in str(record.msg):
            # 使用紫色突出顯示人臉 X 坐標
            record.msg = str(record.msg).replace('[FACE_X]', f'{Fore.MAGENTA}[FACE_X]{Fore.RESET}')
        
        if '[ACTION]' in str(record.msg):
            # 使用青色突出顯示動作
            record.msg = str(record.msg).replace('[ACTION]', f'{Fore.CYAN}[ACTION]{Fore.RESET}')
        
        # 應用顏色到日誌級別
        levelname_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{levelname_color}{record.levelname}{Style.RESET_ALL}"
        
        # 調用原始格式化
        result = super().format(record)
        
        # 恢復原始消息
        record.msg = original_msg
        return result

# 設置日誌
logger = logging.getLogger("Demo")
logger.setLevel(logging.INFO)

# 創建控制台處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 設置格式化器
formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 添加處理器到日誌器
logger.addHandler(console_handler)

class RobotDemo:
    """機器人演示類，實現各種隨機動作和人臉追蹤"""
    
    def __init__(self):
        """初始化演示程式"""
        logger.info("初始化機器人演示程式...")
        logger.info("Initializing robot demo...")
        
        # 載入配置
        self.config = ConfigLoader().load_config()
        logger.info(f"已載入配置: {self.config['robot']['name']}")
        logger.info(f"Loaded configuration: {self.config['robot']['name']}")
        
        # 初始化伺服馬達控制器
        self.servo_controller = ServoController(self.config["servo"])
        
        # 初始化視覺系統（不載入TensorFlow模型）
        vision_config = self.config["vision"].copy()
        vision_config["skip_model_loading"] = True  # 跳過模型載入
        self.vision_system = VisionSystem(vision_config)
        
        # 初始化音效播放器
        pygame.mixer.init()
        self.sound_files = self._load_sound_files()
        logger.info(f"找到 {len(self.sound_files)} 個音效文件")
        logger.info(f"Found {len(self.sound_files)} sound files")
        
        # 控制標誌
        self.running = False
        self.demo_thread = None
        self.face_tracking = False
        self.face_position = {"x": 0.5, "y": 0.5}  # 歸一化座標 (0-1)
        
        # 動作計時器
        self.last_blink_time = 0
        self.last_color_change_time = 0
        self.last_sound_time = 0
        self.last_random_movement_time = 0
        
        # 間隔設定
        self.blink_interval = (2.0, 6.0)  # 眨眼間隔範圍（秒）
        self.color_change_interval = (5.0, 15.0)  # 顏色變換間隔範圍（秒）
        self.sound_interval = (30, 60)  # 音效播放間隔範圍（秒）
        self.random_movement_interval = (3.0, 8.0)  # 隨機動作間隔範圍（秒）
        
        logger.info("機器人演示程式初始化完成")
        logger.info("Robot demo initialization complete")
    
    def _load_sound_files(self):
        """載入聲音文件"""
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sound")
        sound_files = []
        
        if os.path.exists(sound_dir):
            for file in os.listdir(sound_dir):
                if file.endswith(".wav"):
                    sound_files.append(os.path.join(sound_dir, file))
        
        return sound_files
    
    def start(self):
        """啟動演示程式"""
        if self.running:
            return
        
        logger.info("啟動機器人演示程式...")
        logger.info("Starting robot demo...")
        
        # 啟動伺服馬達控制器
        self.servo_controller.start()
        
        # 啟動視覺系統
        self.vision_system.start()
        
        # 設置初始狀態
        self.servo_controller.set_eye_color("green")
        
        # 啟動眼睛 LED 和眼皮眨眼，使 LED 眨眼更频繁
        self.servo_controller.start_led_blinking()
        self.servo_controller.start_eyelid_blinking()
        
        # 啟動主循環
        self.running = True
        self.demo_thread = threading.Thread(target=self._demo_loop)
        self.demo_thread.daemon = True
        self.demo_thread.start()
        
        logger.info("機器人演示程式已啟動")
        logger.info("Robot demo started")
    
    def stop(self):
        """停止演示程式"""
        logger.info("停止演示程式")
        logger.info("Stopping demo program")
        self.running = False
        
        # 停止 LED 和眼皮眨眼
        self.servo_controller.stop_led_blinking()
        self.servo_controller.stop_eyelid_blinking()
        
        # 停止視覺系統
        self.vision_system.stop()
        
        logger.info("機器人演示程式已停止")
        logger.info("Robot demo stopped")
    
    def _demo_loop(self):
        """演示主循環"""
        logger.info("開始演示主循環")
        logger.info("Starting demo main loop")
        
        while self.running:
            current_time = time.time()
            
            # 處理人臉追蹤
            self._update_face_tracking()
            
            # 隨機眨眼
            if current_time - self.last_blink_time > random.uniform(*self.blink_interval):
                self._blink_eyes()
                self.last_blink_time = current_time
            
            # 隨機變換眼睛顏色
            if current_time - self.last_color_change_time > random.uniform(*self.color_change_interval):
                self._change_eye_color()
                self.last_color_change_time = current_time
            
            # 隨機播放音效
            if current_time - self.last_sound_time > random.uniform(*self.sound_interval):
                self._play_random_sound()
                self.last_sound_time = current_time
            
            # 隨機動作
            if current_time - self.last_random_movement_time > random.uniform(*self.random_movement_interval):
                self._perform_random_movement()
                self.last_random_movement_time = current_time
            
            # 控制循環頻率
            time.sleep(0.05)  # 20Hz
    
    def _update_face_tracking(self):
        """更新人臉追蹤"""
        # 獲取最新的視覺數據
        vision_data = self.vision_system.get_latest_data()
        
        if vision_data["face_detected"]:
            # 更新人臉位置
            self.face_position["x"] = vision_data["face_x"]
            self.face_position["y"] = vision_data["face_y"]
            
            # 記錄人臉位置，使用特殊標記使 X 坐標以不同顏色顯示
            logger.info(f"[FACE_X] 人臉位置: X={self.face_position['x']:.2f}, Y={self.face_position['y']:.2f}")
            logger.info(f"[FACE_X] Face position: X={self.face_position['x']:.2f}, Y={self.face_position['y']:.2f}")
            
            # 將歸一化座標轉換為伺服馬達角度
            # 頸部水平移動（左右）- 70-110度範圍
            neck_angle = 90 - (self.face_position["x"] - 0.5) * 40
            # 眼睛垂直移動（上下）- 70-110度範圍
            eye_angle = 90 - (self.face_position["y"] - 0.5) * 40
            
            logger.info(f"追蹤人臉: 頸部角度={neck_angle:.1f}度, 眼睛角度={eye_angle:.1f}度")
            logger.info(f"Tracking face: Neck angle={neck_angle:.1f}°, Eye angle={eye_angle:.1f}°")
            
            # 平滑移動伺服馬達
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_NECK, 
                neck_angle, 
                step_size=2, 
                delay=0.01
            )
            
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_EYE, 
                eye_angle, 
                step_size=2, 
                delay=0.01
            )
            
            # 如果檢測到人臉，眼睛變綠色
            if not vision_data["recognized_person"]:
                logger.info("檢測到未識別的人臉，眼睛變為黃色")
                logger.info("Detected unrecognized face, eyes turning yellow")
                self.servo_controller.set_eye_color("yellow")
            else:
                logger.info(f"識別到已知人臉: {vision_data['recognized_person']}，眼睛變為綠色")
                logger.info(f"Recognized known face: {vision_data['recognized_person']}, eyes turning green")
                self.servo_controller.set_eye_color("green")
        else:
            # 沒有檢測到人臉
            if random.random() < 0.05:  # 只記錄一小部分，避免日誌過多
                logger.debug("未檢測到人臉")
                logger.debug("No face detected")
    
    def _blink_eyes(self):
        """眨眼動作"""
        logger.info("[ACTION] 執行眨眼動作")
        logger.info("[ACTION] Performing eye blink")
        
        # 使用新的關閉眼皮方法
        self.servo_controller.close_eyelids()
        
        # 短暫停頓
        time.sleep(0.1)
        
        # 使用新的打開眼皮方法
        self.servo_controller.open_eyelids()
    
    def _change_eye_color(self):
        """變換眼睛顏色"""
        colors = list(self.servo_controller.EYE_COLORS.keys())
        colors.remove("off")  # 不使用關閉狀態
        
        # 獲取當前顏色
        current_color = self.servo_controller.eye_color
        
        # 選擇一個不同的顏色
        available_colors = [c for c in colors if c != current_color]
        new_color = random.choice(available_colors)
        
        logger.info(f"[ACTION] 變換眼睛顏色: {current_color} -> {new_color}")
        logger.info(f"[ACTION] Changing eye color: {current_color} -> {new_color}")
        
        # 設置新顏色
        self.servo_controller.set_eye_color(new_color)
    
    def _play_random_sound(self):
        """播放隨機音效"""
        if not self.sound_files:
            return
        
        # 選擇一個隨機音效文件
        sound_file = random.choice(self.sound_files)
        
        logger.info(f"[ACTION] 播放音效: {os.path.basename(sound_file)}")
        logger.info(f"[ACTION] Playing sound: {os.path.basename(sound_file)}")
        
        try:
            # 播放音效
            sound = pygame.mixer.Sound(sound_file)
            sound.play()
        except Exception as e:
            logger.error(f"播放音效時出錯: {e}")
            logger.error(f"Error playing sound: {e}")
    
    def _perform_random_movement(self):
        """執行隨機動作"""
        # 隨機選擇一種動作
        action = random.choice([
            'look_around',
            'arm_movement',
            'head_tilt',
            'curious_look'
        ])
        
        logger.info(f"[ACTION] 執行隨機動作: {action}")
        logger.info(f"[ACTION] Performing random movement: {action}")
        
        if action == 'look_around':
            # 四處張望
            positions = [70, 110, 90]  # 左、右、中
            position_names = ["左", "右", "中"]
            position_names_en = ["left", "right", "center"]
            
            for i, pos in enumerate(positions):
                logger.info(f"頸部轉向{position_names[i]}側: {pos}度")
                logger.info(f"Neck turning to {position_names_en[i]}: {pos}°")
                self.servo_controller.move_servo_smooth(
                    self.servo_controller.SERVO_NECK, 
                    pos, 
                    step_size=2, 
                    delay=0.02
                )
                time.sleep(random.uniform(0.3, 0.8))
        
        elif action == 'arm_movement':
            # 手臂動作
            # 右手臂
            right_arm_angle = random.uniform(20, 160)
            logger.info(f"移動右手臂: 角度={right_arm_angle:.1f}度")
            logger.info(f"Moving right arm: Angle={right_arm_angle:.1f}°")
            
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_RIGHT_ARM,
                right_arm_angle,
                step_size=3,
                delay=0.02
            )
            
            # 左手臂
            left_arm_angle = random.uniform(20, 160)
            logger.info(f"移動左手臂: 角度={left_arm_angle:.1f}度")
            logger.info(f"Moving left arm: Angle={left_arm_angle:.1f}°")
            
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_LEFT_ARM,
                left_arm_angle,
                step_size=3,
                delay=0.02
            )
        
        elif action == 'head_tilt':
            # 頭部傾斜
            # 安全地獲取伺服馬達位置，如果不存在則使用預設值 90
            current_eye = self.servo_controller.servo_positions.get(self.servo_controller.SERVO_EYE, 90)
            current_neck = self.servo_controller.servo_positions.get(self.servo_controller.SERVO_NECK, 90)
            
            # 隨機傾斜
            eye_tilt = random.uniform(-15, 15)
            neck_tilt = random.uniform(-15, 15)
            
            new_eye_angle = current_eye + eye_tilt
            new_neck_angle = current_neck + neck_tilt
            
            logger.info(f"頭部傾斜: 眼睛從{current_eye:.1f}度到{new_eye_angle:.1f}度, 頸部從{current_neck:.1f}度到{new_neck_angle:.1f}度")
            logger.info(f"Head tilt: Eye from {current_eye:.1f}° to {new_eye_angle:.1f}°, Neck from {current_neck:.1f}° to {new_neck_angle:.1f}°")
            
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_EYE,
                new_eye_angle,
                step_size=2,
                delay=0.02
            )
            
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_NECK,
                new_neck_angle,
                step_size=2,
                delay=0.02
            )
        
        elif action == 'curious_look':
            # 好奇的觀察
            # 先看左邊
            logger.info("好奇觀察: 先看左邊 (70度)")
            logger.info("Curious look: First looking left (70°)")
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_NECK,
                70,
                step_size=3,
                delay=0.02
            )
            time.sleep(0.5)
            
            # 再看右邊
            logger.info("好奇觀察: 再看右邊 (110度)")
            logger.info("Curious look: Then looking right (110°)")
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_NECK,
                110,
                step_size=3,
                delay=0.02
            )
            time.sleep(0.5)
            
            # 回到中間
            logger.info("好奇觀察: 回到中間 (90度)")
            logger.info("Curious look: Back to center (90°)")
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_NECK,
                90,
                step_size=3,
                delay=0.02
            )

def main():
    """主程序入口"""
    logger.info("啟動毛毛安全機器人演示程式...")
    logger.info("Starting MaoMao Security Robot Demo...")
    
    # 創建演示實例
    demo = RobotDemo()
    
    try:
        # 啟動演示
        demo.start()
        
        # 主循環
        print("演示程式已啟動，按 Ctrl+C 停止...")
        print("Demo started, press Ctrl+C to stop...")
        
        while True:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("接收到中斷信號，停止演示...")
        logger.info("Received interrupt signal, stopping demo...")
    finally:
        # 停止演示
        demo.stop()
        logger.info("演示程式已結束")
        logger.info("Demo program ended")

if __name__ == "__main__":
    main()
