#!/usr/bin/env python3
# -*- coding: utf-8 -*-
### AI GENERATED CODE ###

"""
伺服馬達控制器 - 管理機器人的9個伺服馬達
"""

import logging
import threading
import time
import random
import math
import os
import sys
import platform

# 檢測運行環境
IS_RASPBERRY_PI = platform.system() == 'Linux' and os.path.exists('/sys/firmware/devicetree/base/model')

# 有條件地導入硬體相關庫
if IS_RASPBERRY_PI:
    try:
        from adafruit_servokit import ServoKit
        import board
        import neopixel_spi as neopixel
        HARDWARE_AVAILABLE = True
    except ImportError:
        HARDWARE_AVAILABLE = False
        logging.warning("硬體相關庫導入失敗，將使用模擬模式")
else:
    HARDWARE_AVAILABLE = False
    logging.info("在非樹莓派環境運行，將使用模擬模式")

class ServoController:
    """伺服馬達控制器類，管理機器人的伺服馬達"""
    
    # 伺服馬達ID常量 (基於參考程式)
    SERVO_EYE = 1             # 眼睛伺服
    SERVO_NECK = 2            # 頸部伺服（水平移動）
    SERVO_RIGHT_ARM_UPPER = 3 # 右手臂上部
    SERVO_RIGHT_ARM_LOWER = 4 # 右手臂下部
    SERVO_LEFT_ARM_UPPER = 5  # 左手臂上部
    SERVO_LEFT_ARM_LOWER = 6  # 左手臂下部
    
    # 眼睛顏色映射
    EYE_COLORS = {
        "green": (0, 255, 0),
        "red": (255, 0, 0),
        "yellow": (255, 255, 0),
        "blue": (0, 0, 255),
        "white": (255, 255, 255),
        "off": (0, 0, 0)
    }
    
    def __init__(self, config):
        """初始化伺服馬達控制器
        
        Args:
            config (dict): 伺服馬達配置
        """
        self.logger = logging.getLogger("Servo")
        self.config = config
        
        # 初始化狀態變數
        self.running = False
        self.servo_positions = {i: 90 for i in range(1, 7)}  # 1-6號伺服，初始位置90度
        self.eye_color = "green"
        self.laser_active = False
        
        # 動作控制標誌
        self.natural_blinking = False
        self.arm_swinging = False
        
        # 眨眼和顏色變化參數
        self.blink_interval_min = config.get("blink_interval_min", 2.0)  # 最小眨眼間隔（秒）
        self.blink_interval_max = config.get("blink_interval_max", 6.0)  # 最大眨眼間隔（秒）
        self.next_blink_time = time.time() + random.uniform(self.blink_interval_min, self.blink_interval_max)
        
        # 處理線程
        self.thread = None
        self.lock = threading.Lock()
        
        # 初始化硬體連接
        self._init_hardware()
        
        self.logger.info("伺服馬達控制器初始化完成")
    
    def _init_hardware(self):
        """初始化硬體連接
        
        根據環境初始化真實硬體或模擬硬體
        """
        self.logger.info("初始化伺服馬達硬體連接...")
        
        # 初始化變數
        self.kit = None
        self.pixels = None
        self.num_pixels = 7  # LED數量
        
        if IS_RASPBERRY_PI and HARDWARE_AVAILABLE:
            try:
                # 初始化ServoKit
                self.logger.info("初始化Adafruit ServoKit...")
                self.kit = ServoKit(channels=16)
                
                # 設置初始位置
                self.kit.servo[self.SERVO_EYE].angle = 90
                self.kit.servo[self.SERVO_NECK].angle = 90
                self.kit.servo[self.SERVO_RIGHT_ARM_UPPER].angle = 160
                self.kit.servo[self.SERVO_RIGHT_ARM_LOWER].angle = 20
                self.kit.servo[self.SERVO_LEFT_ARM_UPPER].angle = 20
                self.kit.servo[self.SERVO_LEFT_ARM_LOWER].angle = 160
                
                # 初始化NeoPixel LED
                self.logger.info("初始化NeoPixel LED...")
                spi = board.SPI()
                self.pixels = neopixel.NeoPixel_SPI(spi, self.num_pixels, pixel_order=neopixel.GRB, auto_write=False)
                
                # 設置初始顏色
                self._set_all_pixels(self.EYE_COLORS[self.eye_color])
                
                self.logger.info("硬體初始化成功")
                return True
                
            except Exception as e:
                self.logger.error(f"硬體初始化失敗: {e}")
                self.logger.warning("切換到模擬模式")
        else:
            self.logger.info("在開發環境中使用模擬模式")
        
        # 模擬模式初始化
        time.sleep(0.5)
        self.logger.info("模擬伺服馬達初始化完成")
        return False
        
    def _set_all_pixels(self, color):
        """設置所有LED像素為相同顏色
        
        Args:
            color (tuple): RGB顏色值
        """
        if self.pixels is None:
            return
            
        for i in range(self.num_pixels):
            self.pixels[i] = color
        self.pixels.show()
    
    def start(self):
        """啟動伺服馬達控制器"""
        if self.running:
            return
            
        self.logger.info("啟動伺服馬達控制器...")
        self.running = True
        
        # 重置所有伺服馬達到初始位置
        self.reset_all()
        
        # 啟動處理線程
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("伺服馬達控制器已啟動")
    
    def stop(self):
        """停止伺服馬達控制器"""
        if not self.running:
            return
            
        self.logger.info("停止伺服馬達控制器...")
        self.running = False
        
        # 停止所有動作
        self.natural_blinking = False
        self.arm_swinging = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
        
        # 重置所有伺服馬達到安全位置
        self.reset_all()
        
        self.logger.info("伺服馬達控制器已停止")
    
    def _update_loop(self):
        """伺服馬達更新循環"""
        last_arm_swing_time = 0
        last_idle_movement_time = 0
        idle_movement_interval = 5.0  # 閒置動作間隔（秒）
        
        while self.running:
            current_time = time.time()
            
            # 處理自然眨眼
            self._check_for_blink()
            
            # 處理手臂擺動
            if self.arm_swinging and current_time - last_arm_swing_time > random.uniform(3.0, 8.0):
                self._swing_arms()
                last_arm_swing_time = current_time
            
            # 閒置時的自然動作
            if current_time - last_idle_movement_time > idle_movement_interval:
                self._idle_movement()
                last_idle_movement_time = current_time
                idle_movement_interval = random.uniform(5.0, 15.0)  # 隨機閒置間隔
            
            # 控制更新頻率
            time.sleep(0.05)  # 20Hz
    
    def _idle_movement(self):
        """閒置時的自然動作"""
        if not self.running or random.random() > 0.3:  # 30%機率執行
            return
            
        # 隨機選擇一種閒置動作
        action = random.choice(['look_around', 'small_neck_movement'])
        
        if action == 'look_around':
            # 四處張望動作
            positions = [70, 110, 90]  # 左、右、中
            for pos in positions:
                self.move_servo_smooth(self.SERVO_NECK, pos, step_size=2, delay=0.02)
                self.move_servo_smooth(self.SERVO_EYE, pos, step_size=2, delay=0.01)
                time.sleep(random.uniform(0.3, 0.8))
        else:
            # 小幅度頸部移動
            current_pos = self.servo_positions[self.SERVO_NECK]
            new_pos = current_pos + random.uniform(-10, 10)
            new_pos = max(70, min(110, new_pos))  # 限制範圍
            self.move_servo_smooth(self.SERVO_NECK, new_pos, step_size=1, delay=0.02)
    
    def set_position(self, servo_id, position):
        """設置伺服馬達位置
        
        Args:
            servo_id (int): 伺服馬達ID (1-6)
            position (float): 位置角度 (0-180)
        
        Returns:
            bool: 操作是否成功
        """
        if not 1 <= servo_id <= 6:
            self.logger.error(f"無效的伺服馬達ID: {servo_id}")
            return False
            
        position = max(0, min(180, position))  # 限制在0-180範圍內
        
        self.logger.debug(f"設置伺服馬達 {servo_id} 位置為 {position}")
        
        with self.lock:
            self.servo_positions[servo_id] = position
            
        # 實際控制伺服馬達
        self._control_servo(servo_id, position)
        
        return True
    
    def move_servo_smooth(self, servo_id, target_angle, step_size=1, delay=0.02):
        """平滑地移動伺服馬達到目標角度
        
        Args:
            servo_id (int): 伺服馬達ID (1-6)
            target_angle (float): 目標角度 (0-180)
            step_size (int, optional): 每步的角度大小
            delay (float, optional): 每步之間的延遲（秒）
            
        Returns:
            bool: 操作是否成功
        """
        if not 1 <= servo_id <= 6:
            self.logger.error(f"無效的伺服馬達ID: {servo_id}")
            return False
            
        target_angle = max(0, min(180, target_angle))  # 限制在0-180範圍內
        
        with self.lock:
            current_angle = self.servo_positions[servo_id]
        
        steps = int(abs(target_angle - current_angle))
        
        for _ in range(0, steps, step_size):
            if current_angle < target_angle:
                current_angle += step_size
            else:
                current_angle -= step_size
                
            current_angle = max(0, min(180, current_angle))  # 限制範圍
            self.set_position(servo_id, current_angle)
            time.sleep(delay)
            
            # 檢查是否應該眨眼
            self._check_for_blink()
        
        # 確保最終到達目標角度
        self.set_position(servo_id, target_angle)
        return True
    
    def _control_servo(self, servo_id, position):
        """實際控制伺服馬達
        
        Args:
            servo_id (int): 伺服馬達ID
            position (float): 位置角度
        """
        if self.kit is not None:
            try:
                self.kit.servo[servo_id].angle = position
            except Exception as e:
                self.logger.error(f"控制伺服馬達失敗: {e}")
        # 在模擬模式下，不需要實際控制硬體
    
    def reset_all(self):
        """重置所有伺服馬達到初始位置"""
        self.logger.info("重置所有伺服馬達")
        
        # 眼睛位置居中
        self.set_position(self.SERVO_EYE, 90)
        
        # 頸部居中
        self.set_position(self.SERVO_NECK, 90)
        
        # 手臂初始位置
        self.set_position(self.SERVO_RIGHT_ARM_UPPER, 160)
        self.set_position(self.SERVO_RIGHT_ARM_LOWER, 20)
        self.set_position(self.SERVO_LEFT_ARM_UPPER, 20)
        self.set_position(self.SERVO_LEFT_ARM_LOWER, 160)
        
        # 設置眼睛顏色為綠色
        self.set_eye_color("green")
        
        # 關閉激光
        self.deactivate_laser()
    
    def follow_face(self, face_x, face_y):
        """控制眼睛和頸部跟隨人臉
        
        Args:
            face_x (float): 人臉X座標 (0-1)
            face_y (float): 人臉Y座標 (0-1)
        """
        # 將0-1的座標映射到伺服馬達角度
        # 眼睛方向: 0->60, 0.5->90, 1->120
        eye_angle = 60 + face_x * 60
        
        # 頸部方向: 0->70, 0.5->90, 1->110
        neck_angle = 70 + face_x * 40
        
        # 平滑設置眼睛和頸部位置
        self.move_servo_smooth(self.SERVO_EYE, eye_angle, step_size=2, delay=0.01)
        self.move_servo_smooth(self.SERVO_NECK, neck_angle, step_size=2, delay=0.01)
    

    
    def _swing_arms(self):
        """執行手臂擺動動作"""
        # 隨機選擇一個手臂 (左或右)
        arm_side = random.choice(['left', 'right'])
        
        if arm_side == 'right':
            # 右手臂小幅度擺動
            current_upper = self.servo_positions[self.SERVO_RIGHT_ARM_UPPER]
            current_lower = self.servo_positions[self.SERVO_RIGHT_ARM_LOWER]
            
            # 計算新位置 (小幅度擺動)
            new_upper = current_upper + random.uniform(-10, 10)
            new_upper = max(120, min(170, new_upper))  # 限制範圍
            
            new_lower = current_lower + random.uniform(-10, 10)
            new_lower = max(10, min(60, new_lower))  # 限制範圍
            
            # 設置新位置
            self.move_servo_smooth(self.SERVO_RIGHT_ARM_UPPER, new_upper, step_size=2, delay=0.02)
            self.move_servo_smooth(self.SERVO_RIGHT_ARM_LOWER, new_lower, step_size=2, delay=0.02)
        else:
            # 左手臂小幅度擺動
            current_upper = self.servo_positions[self.SERVO_LEFT_ARM_UPPER]
            current_lower = self.servo_positions[self.SERVO_LEFT_ARM_LOWER]
            
            # 計算新位置 (小幅度擺動)
            new_upper = current_upper + random.uniform(-10, 10)
            new_upper = max(10, min(60, new_upper))  # 限制範圍
            
            new_lower = current_lower + random.uniform(-10, 10)
            new_lower = max(120, min(170, new_lower))  # 限制範圍
            
            # 設置新位置
            self.move_servo_smooth(self.SERVO_LEFT_ARM_UPPER, new_upper, step_size=2, delay=0.02)
            self.move_servo_smooth(self.SERVO_LEFT_ARM_LOWER, new_lower, step_size=2, delay=0.02)
    
    def start_natural_blinking(self):
        """開始自然眨眼"""
        self.natural_blinking = True
    
    def stop_natural_blinking(self):
        """停止自然眨眼"""
        self.natural_blinking = False
    
    def start_arm_swinging(self):
        """開始手臂擺動"""
        self.arm_swinging = True
    
    def stop_arm_swinging(self):
        """停止手臂擺動"""
        self.arm_swinging = False
    
    def set_eye_color(self, color):
        """設置眼睛顏色
        
        Args:
            color (str): 顏色名稱 ("green", "red", "yellow", "blue", "white", "off")
        
        Returns:
            bool: 操作是否成功
        """
        if color not in self.EYE_COLORS:
            self.logger.error(f"無效的眼睛顏色: {color}")
            return False
            
        self.logger.info(f"設置眼睛顏色為 {color}")
        self.logger.info(f"Setting eye color to {color}")
        
        with self.lock:
            self.eye_color = color
            
        # 設置 LED 顏色
        rgb = self.EYE_COLORS[color]
        self._set_all_pixels(rgb)
        
        return True
        
    def _check_for_blink(self):
        """檢查是否應該眨眼"""
        current_time = time.time()
        
        if current_time > self.next_blink_time and self.natural_blinking:
            self.logger.debug("眨眼")
            self._blink()
            self.next_blink_time = current_time + random.uniform(self.blink_interval_min, self.blink_interval_max)
    
    def _blink(self):
        """執行眨眼動作"""
        # 保存當前顏色
        with self.lock:
            saved_color = self.eye_color
        
        # 關閉LED（眨眼）
        self.set_eye_color("off")
        time.sleep(0.1)  # 眼睛關閉時間
        
        # 恢復原來顏色
        self.set_eye_color(saved_color)
    
    def raise_right_arm(self):
        """舉起右手臂"""
        self.move_servo_smooth(self.SERVO_RIGHT_ARM_UPPER, 120, step_size=2, delay=0.02)
        self.move_servo_smooth(self.SERVO_RIGHT_ARM_LOWER, 60, step_size=2, delay=0.02)
    
    def raise_arms(self):
        """舉起雙手"""
        # 右手臂
        self.move_servo_smooth(self.SERVO_RIGHT_ARM_UPPER, 120, step_size=2, delay=0.02)
        self.move_servo_smooth(self.SERVO_RIGHT_ARM_LOWER, 60, step_size=2, delay=0.02)
        
        # 左手臂
        self.move_servo_smooth(self.SERVO_LEFT_ARM_UPPER, 60, step_size=2, delay=0.02)
        self.move_servo_smooth(self.SERVO_LEFT_ARM_LOWER, 120, step_size=2, delay=0.02)
    
    def lower_arms(self):
        """放下雙手"""
        # 右手臂
        self.move_servo_smooth(self.SERVO_RIGHT_ARM_UPPER, 160, step_size=2, delay=0.02)
        self.move_servo_smooth(self.SERVO_RIGHT_ARM_LOWER, 20, step_size=2, delay=0.02)
        
        # 左手臂
        self.move_servo_smooth(self.SERVO_LEFT_ARM_UPPER, 20, step_size=2, delay=0.02)
        self.move_servo_smooth(self.SERVO_LEFT_ARM_LOWER, 160, step_size=2, delay=0.02)
    
    def activate_laser(self):
        """啟動激光指示器"""
        self.logger.info("啟動激光指示器")
        self.laser_active = True
        # 實際部署時，這裡會控制激光指示器
    
    def deactivate_laser(self):
        """關閉激光指示器"""
        self.logger.info("關閉激光指示器")
        self.laser_active = False
        # 實際部署時，這裡會控制激光指示器
    
    def get_status(self):
        """獲取伺服馬達狀態
        
        Returns:
            dict: 伺服馬達狀態
        """
        with self.lock:
            return {
                "positions": self.servo_positions.copy(),
                "eye_color": self.eye_color,
                "laser_active": self.laser_active,
                "natural_blinking": self.natural_blinking,
                "arm_swinging": self.arm_swinging
            }
