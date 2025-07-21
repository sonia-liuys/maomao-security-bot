#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模式管理器 - 控制機器人的不同運行模式
Mode Manager - Controls different operating modes of the robot
"""

import logging
import os
import time
import threading
from enum import Enum, auto
import random
from utils.sound_manager import SoundManager

# 定義ANSI顏色代碼用於彩色日誌輸出
# Define ANSI color codes for colored log output
COLORS = {
    'RESET': '\033[0m',
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'MAGENTA': '\033[95m',
    'CYAN': '\033[96m',
    'WHITE': '\033[97m',
    'BOLD': '\033[1m'
}

class RobotMode(Enum):
    """機器人運行模式枚舉"""
    MANUAL = auto()       # 手動模式
    PATROL = auto()       # 巡邏模式
    SURVEILLANCE = auto() # 監視模式

class ModeManager:
    """機器人模式管理器，處理不同模式的邏輯和轉換"""
    
    def __init__(self, vision_system, servo_controller, movement_controller, config):
        """初始化模式管理器
        
        # 音效播放狀態
        self.last_thinking_sound_time = 0
        self.last_face_detected = False
        
        Args:
            vision_system: 視覺系統實例
            servo_controller: 伺服馬達控制器實例
            movement_controller: 移動控制器實例
            config (dict): 模式配置
        """
        self.logger = logging.getLogger("ModeManager")
        self.vision_system = vision_system
        self.servo_controller = servo_controller
        self.movement_controller = movement_controller
        self.config = config
        
        # Sound manager may be part of the config
        self.sound_manager = config.get("sound_manager", None)
        self.websocket_server = config.get("websocket_server", None)
        
        self.current_mode = None
        self.mode_start_time = 0
        
        # 巡邏模式相關狀態
        self.patrol_active = False  # 巡邏模式活動狀態
        self.patrol_last_move_time = 0
        self.patrol_last_arm_time = 0
        self.patrol_last_eye_blink_time = 0
        self.patrol_eye_blink_interval = 0  # Will be set randomly
        
        # LED眨眼相關變量
        self.patrol_last_led_blink_time = 0
        self.patrol_led_blink_interval = 0  # Will be set randomly
        
        # 監視模式相關狀態
        self.surveillance_countdown = 0
        self.surveillance_intruder_detected = False
        self.surveillance_yellow_warning = False  # 黃色警告狀態
        self.surveillance_yellow_start_time = 0  # 黃色警告開始時間
        self.detection_pause_until = 0  # 暂停偵測直到指定時間
        self.student_id_detection_pause_until = 0
        
        # 人臂追蹤相關狀態
        self.face_tracking_enabled = True  # 預設開啟人臂追蹤
        self.alarm_active = False  # 警報狀態屬性
        
        # 初始化音效管理器
        # Initialize sound manager
        self.sound_manager = SoundManager(logger=self.logger)
        
        self.logger.info("模式管理器初始化完成")
    
    def set_mode(self, mode):
        """設置機器人運行模式
        
        Args:
            mode (RobotMode): 要設置的模式
        """
        if self.current_mode == mode:
            self.logger.info(f"已經處於{mode.name}模式，無需切換")
            return
            
        self.logger.info(f"切換模式: {self.current_mode} -> {mode}")
        
        # 如果當前有活動模式，先退出
        if self.current_mode:
            self._exit_mode(self.current_mode)
            
        # 設置新模式
        self.current_mode = mode
        self.mode_start_time = time.time()
        
        # 進入新模式
        self._enter_mode(mode)
        
        self.logger.info(f"已切換到{mode.name}模式")
    
    def _enter_mode(self, mode):
        """進入指定模式時的處理
        
        Args:
            mode (RobotMode): 要進入的模式
        """
        # 使用彩色日誌輸出模式切換信息
        # Use colored log output for mode switching information
        mode_color = COLORS['CYAN']
        mode_name = mode.name
        self.logger.info(f"{COLORS['BOLD']}{mode_color}[MODE CHANGE] 進入{mode_name}模式{COLORS['RESET']}")
        self.logger.info(f"{COLORS['BOLD']}{mode_color}[MODE CHANGE] Entering {mode_name} mode{COLORS['RESET']}")
        
        # 如果進入監視模式，啟用人臉追蹤
        # If entering surveillance mode, enable face tracking
        if mode == RobotMode.SURVEILLANCE:
            self.face_tracking_enabled = True
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] 啟用人臉追蹤{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] Face tracking enabled{COLORS['RESET']}")
        
        # 模式特定初始化
        if mode == RobotMode.MANUAL:
            # 手動模式下禁用所有自動運動，實現完全手動控制
            self.logger.info(f"{COLORS['BLUE']}[MANUAL] 禁用自動眨眼和手臂擺動，進入完全手動控制模式{COLORS['RESET']}")
            self.logger.info(f"{COLORS['BLUE']}[MANUAL] Disabling auto blinking and movement, entering full manual control{COLORS['RESET']}")
            # 停止任何可能正在運行的自動行為
            self.servo_controller.stop_natural_blinking()
            self.servo_controller.stop_arm_swinging()
            
        elif mode == RobotMode.PATROL:
            # 巡邏模式下啟動自動巡邏，設置眼睛為黃色且不眨眼
            self.patrol_last_move_time = time.time()
            self.logger.info(f"{COLORS['YELLOW']}[PATROL] 啟動巡邏模式{COLORS['RESET']}")
            self.logger.info(f"{COLORS['YELLOW']}[PATROL] Starting patrol mode{COLORS['RESET']}")
            
            # 停止所有眨眼功能
            self.logger.info(f"{COLORS['YELLOW']}[PATROL] 停止所有眨眼功能{COLORS['RESET']}")
            self.logger.info(f"{COLORS['YELLOW']}[PATROL] Stopping all blinking functions{COLORS['RESET']}")
            # self.servo_controller.stop_natural_blinking()
            # self.servo_controller.stop_led_blinking()
            # self.servo_controller.stop_eyelid_blinking()
            
            # 設置眼睛顏色為黃色
            self.logger.info(f"{COLORS['YELLOW']}[EYE COLOR] 設置眼睛顏色為黃色{COLORS['RESET']}")
            self.logger.info(f"{COLORS['YELLOW']}[EYE COLOR] Setting eye color to yellow{COLORS['RESET']}")
            self.servo_controller.set_eye_color("yellow")
            
            # 初始化手臂動作間隔
            self.patrol_last_arm_time = time.time()
            
            # 實用動作：從強調效果
            try:
                # 執行一次眨眼動作，確保進入模式後立即有反應
                self.servo_controller.close_eyelids()
                time.sleep(0.3)
                self.servo_controller.open_eyelids()
                
                self.servo_controller.start_natural_blinking()

                self.servo_controller.start_arm_swinging()

                # 設置眼睛為黃色，表示巡邏模式
                self.servo_controller.set_eye_color("yellow")
                self.logger.info(f"{COLORS['YELLOW']}[PATROL] 進入巡邏模式，設置眼睛為黃色{COLORS['RESET']}")
                self.logger.info(f"{COLORS['YELLOW']}[PATROL] Entering patrol mode, setting eyes to yellow{COLORS['RESET']}")
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] 初始化巡邏模式動作失敗: {str(e)}{COLORS['RESET']}")
            
        elif mode == RobotMode.SURVEILLANCE:
            # 監視模式特有的初始化
            self.face_tracking_enabled = True
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] 啟用人臂追蹤{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] Face tracking enabled{COLORS['RESET']}")
            self.servo_controller.set_eye_color("blue")
            self.logger.info(f"{COLORS['BLUE']}[SURVEILLANCE] 進入監視模式, 設置眼睛為藍色{COLORS['RESET']}")
            self.logger.info(f"{COLORS['BLUE']}[SURVEILLANCE] Entering surveillance mode, setting eyes to blue{COLORS['RESET']}")

    def _exit_mode(self, mode):
        """退出指定模式
        
        Args:
            mode (RobotMode): 要退出的模式
        """
        self.logger.info(f"退出{mode.name}模式")
        
        # 停止所有運動
        self.movement_controller.stop()
        
        # 模式特定清理
        if mode == RobotMode.PATROL:
            # 停止巡邏模式特有的行為
            self.patrol_active = False
            self.servo_controller.stop_natural_blinking()
            self.servo_controller.stop_arm_swinging()
            self.face_tracking_enabled = False
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] 停用人臉追蹤{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] Face tracking disabled{COLORS['RESET']}")
        elif mode == RobotMode.SURVEILLANCE:
            # 停止監視模式特有的行為
            self.face_tracking_enabled = False
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] 停用人臉追蹤{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[FACE TRACKING] Face tracking disabled{COLORS['RESET']}")
        elif mode == RobotMode.MANUAL:
            self.servo_controller.stop_natural_blinking()
            self.servo_controller.stop_arm_swinging()
    
    def update(self, vision_data):
        """更新當前模式的狀態
        
        Args:
            vision_data (dict): 視覺系統提供的最新數據
        """
        if not self.current_mode:
            return
            
        # 根據當前模式執行相應的更新邏輯
        if self.current_mode == RobotMode.MANUAL:
            self._update_manual_mode(vision_data)
        elif self.current_mode == RobotMode.PATROL:
            self._update_patrol_mode(vision_data)
        elif self.current_mode == RobotMode.SURVEILLANCE:
            self._update_surveillance_mode(vision_data)
    
    def _update_manual_mode(self, vision_data):
        """更新手動模式
        
        Args:
            vision_data (dict): 視覺系統提供的最新數據
        """
        # 手動模式下不需要特別處理
        pass
    
    def _update_patrol_mode(self, vision_data):
        """更新巡邏模式
        
        # --- Thinking sound on face detected ---
        face_detected = vision_data.get("face_detected", False)
        now = time.time()
        if face_detected and not self.last_face_detected:
            # Only play when face appears (not every frame)
            if now - self.last_thinking_sound_time > 10.0:
                self.sound_manager.play_thinking_sound()
                self.last_thinking_sound_time = now
        self.last_face_detected = face_detected
        
        Args:
            vision_data (dict): 視覺系統提供的最新數據
        """
        # 如果巡邏模式未啟動，則不執行任何操作
        if not self.patrol_active:
            return
            
        current_time = time.time()
        
        # 初始化 - 確保變量已正確初始化
        if getattr(self, "patrol_last_eye_blink_time", 0) == 0:
            # 初始化眼睛眨眼相關變量
            self.patrol_last_eye_blink_time = current_time
            self.patrol_eye_blink_interval = 3.0  # 很短的開始間隔以快速看到效果
            
            # 初始化 LED 眨眼相關變量
            self.patrol_last_led_blink_time = current_time
            self.patrol_led_blink_interval = 1.5  # 更频繁的 LED 眨眼間隔
            
            # 初始化手臂切換與移動變量
            self.patrol_last_arm_time = current_time - 10.0  # 設置為已經經過10秒，使手臂動作更快發生
            self.patrol_last_move_time = current_time
            self.logger.info(f"{COLORS['CYAN']}[PATROL] Initializing patrol mode action variables{COLORS['RESET']}")
            
            # 啟動直接的眨眼
            try:
                # 立即執行一次眨眼動作以確保功能正常
                self.logger.info(f"{COLORS['CYAN']}[PATROL] Patrol mode initial blink test{COLORS['RESET']}")
                self.servo_controller.close_eyelids()
                time.sleep(0.3)
                self.servo_controller.open_eyelids()
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] Initial blink test failed: {str(e)}{COLORS['RESET']}")
        
        # 1. 自動眼睛眨眼 (每10~30秒隨機眨眼一次) - 使用眼皮機構
        if current_time - self.patrol_last_eye_blink_time > self.patrol_eye_blink_interval:
            self.patrol_last_eye_blink_time = current_time
            self.patrol_eye_blink_interval = random.uniform(10.0, 30.0)  # 10-30秒間隔
            
            # 直接執行眨眼動作
            self.logger.info(f"{COLORS['CYAN']}[PATROL] Executing eyelid blink, next in {self.patrol_eye_blink_interval:.1f} seconds{COLORS['RESET']}")
            
            # 實現眼皮的眨眼動作
            try:
                # 關閉眼睛
                self.servo_controller.close_eyelids()
                time.sleep(0.3)  # 閉眼狀態保持短時間
                # 打開眼睛
                self.servo_controller.open_eyelids()
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] Eyelid blink failed: {str(e)}{COLORS['RESET']}")
                
        # 2. LED台燈眨眼 (更高頻率，每1.5-4秒) - 顯示更多的活力
        if current_time - self.patrol_last_led_blink_time > self.patrol_led_blink_interval:
            self.patrol_last_led_blink_time = current_time
            self.patrol_led_blink_interval = random.uniform(1.5, 4.0)  # 更短的間隔，增加活力感
            
            # 執行 LED 眨眼動作
            self.logger.info(f"{COLORS['CYAN']}[PATROL] Executing LED blink, next in {self.patrol_led_blink_interval:.1f} seconds{COLORS['RESET']}")
            
            try:
                # 保存現有顏色
                current_color = "yellow"  # 預設巡邏模式為黃色
                
                # 關閉 LED
                self.servo_controller.set_eye_color("off")
                time.sleep(0.1)  # 很短暫的關閉時間
                
                # 恢復原來顏色
                self.servo_controller.set_eye_color(current_color)
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] LED blink failed: {str(e)}{COLORS['RESET']}")
        
        # 2. 人臂追蹤功能（追蹤檢測到的人臂）
        if self.face_tracking_enabled and face_detected:
            face_x = vision_data.get("face_x", 0.5)  # 預設在畫面中心
            face_y = vision_data.get("face_y", 0.5)  # 預設在畫面中心
            
            # 紀錄臂部追蹤位置
            self.logger.debug(f"{COLORS['CYAN']}[PATROL][FACE TRACKING] 追蹤人臂位置: x={face_x:.2f}, y={face_y:.2f}{COLORS['RESET']}")
            self.logger.debug(f"{COLORS['CYAN']}[PATROL][FACE TRACKING] Tracking face position: x={face_x:.2f}, y={face_y:.2f}{COLORS['RESET']}")
            
            # 讓機器人追蹤人臂
            try:
                self.servo_controller.follow_face(face_x, face_y)
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] 人臂追蹤失敗: {str(e)}{COLORS['RESET']}")
            
            # 如果辨識出特定人員，變更眼睛顏色為綠色
            recognized_person = vision_data.get("recognized_person", None)
            if recognized_person and "sonia" in recognized_person.lower():
                try:
                    self.servo_controller.set_eye_color("green")
                    self.logger.info(f"{COLORS['GREEN']}[PATROL] 辨識出已知人員: {recognized_person}{COLORS['RESET']}")
                    self.logger.info(f"{COLORS['GREEN']}[PATROL] Recognized known person: {recognized_person}{COLORS['RESET']}")
                except Exception as e:
                    self.logger.error(f"{COLORS['RED']}[PATROL] 設置眼睛顏色失敗: {str(e)}{COLORS['RESET']}")
        
        # 3. 隨機手臂動作 (更頻繁，每8-15秒隨機移動手臂)
        # 即使在面部追蹤下也會進行手臂風格動作，增加活力感
        if current_time - self.patrol_last_arm_time > random.uniform(8.0, 15.0):
            self.patrol_last_arm_time = current_time
            
            # 擴展的手臂動作
            arm_actions = [
                "raise",              # 同時舉起兩面手臂
                "lower",              # 同時放下兩面手臂
                "raise_left",         # 只舉起左手
                "raise_right",        # 只舉起右手
                "wave_left",          # 左手揮手動作
                "wave_right",         # 右手揮手動作
                "alternate_raise"     # 交替舉起手臂
            ]
            
            # 如果正在追蹤人臂，僅做輕微的手臂動作
            if face_detected:
                arm_actions = ["wave_left", "wave_right", "lower"]  # 只做哈囉者放下手臂
            
            arm_action = random.choice(arm_actions)
            
            self.logger.info(f"{COLORS['MAGENTA']}[PATROL] Performing random arm movement: {arm_action}{COLORS['RESET']}")
            
            try:
                if arm_action == "raise":
                    self.servo_controller.raise_arms()
                elif arm_action == "lower":
                    self.servo_controller.lower_arms()
                elif arm_action == "raise_left":
                    # Partial arm movement - only move one arm
                    self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_ARM, 0, step_size=2, delay=0.02)
                elif arm_action == "raise_right":
                    # Partial arm movement - only move one arm
                    self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_ARM, 180, step_size=2, delay=0.02)
                elif arm_action == "wave_left":
                    # Left arm wave movement
                    current_pos = 90
                    # Wave motion - move back and forth 3 times
                    for _ in range(3):
                        self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_ARM, 60, step_size=5, delay=0.01)
                        time.sleep(0.1)
                        self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_ARM, 90, step_size=5, delay=0.01)
                        time.sleep(0.1)
                elif arm_action == "wave_right":
                    # Right arm wave movement
                    # Wave motion - move back and forth 3 times
                    for _ in range(3):
                        self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_ARM, 120, step_size=5, delay=0.01)
                        time.sleep(0.1)
                        self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_ARM, 90, step_size=5, delay=0.01)
                        time.sleep(0.1)
                elif arm_action == "alternate_raise":
                    # Alternate raising and lowering arms for a dynamic effect
                    self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_ARM, 0, step_size=5, delay=0.02)
                    time.sleep(0.3)
                    self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_ARM, 90, step_size=5, delay=0.02)
                    time.sleep(0.2)
                    self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_ARM, 180, step_size=5, delay=0.02)
                    time.sleep(0.3)
                    self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_ARM, 90, step_size=5, delay=0.02)
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] Arm movement failed: {str(e)}{COLORS['RESET']}")
        
        # 4. 檢查是否需要移動 - 只有在沒有追蹤人臂時才隨機移動
        # 每隔一段時間隨機選擇一個方向移動
        if not face_detected and current_time - self.patrol_last_move_time > 5.0:  # 每5秒移動一次
            self.patrol_last_move_time = current_time
            
            # 隨機選擇一個方向
            directions = ["forward", "backward", "left", "right"]
            direction = random.choice(directions)
            
            # 使用彩色日誌輸出移動信息
            self.logger.info(f"{COLORS['YELLOW']}[PATROL] 巡邏模式: 移動方向 {direction}{COLORS['RESET']}")
            self.logger.info(f"{COLORS['YELLOW']}[PATROL] Patrol mode: Moving {direction}{COLORS['RESET']}")
            
            try:
                self.movement_controller.move(direction)
                
                # 短暫移動後停止
                time.sleep(1.0)
                self.logger.info(f"{COLORS['YELLOW']}[PATROL] 停止移動{COLORS['RESET']}")
                self.logger.info(f"{COLORS['YELLOW']}[PATROL] Stopping movement{COLORS['RESET']}")
                self.movement_controller.stop()
            except Exception as e:
                self.logger.error(f"{COLORS['RED']}[PATROL] 移動失敗: {str(e)}{COLORS['RESET']}")
    
    def _update_surveillance_mode(self, vision_data):
        """更新監視模式
        
        # --- Thinking sound on face detected ---
        face_detected = vision_data.get("face_detected", False)
        now = time.time()
        if face_detected and not self.last_face_detected:
            # Only play when face appears (not every frame)
            if now - self.last_thinking_sound_time > 10.0:
                self.sound_manager.play_thinking_sound()
                self.last_thinking_sound_time = now
        self.last_face_detected = face_detected
        
        Args:
            vision_data (dict): 視覺系統提供的最新數據
        """
        # 獲取人臉檢測結果
        face_detected = vision_data.get("face_detected", False)
        recognized_person = vision_data.get("recognized_person", None)
        confidence = vision_data.get("confidence", 0.0)
        current_time = time.time()
        
        # 如果啟用了人臉追蹤且檢測到人臉，則追蹤人臉
        # If face tracking is enabled and a face is detected, track the face
        if self.face_tracking_enabled and face_detected and current_time >= self.detection_pause_until:
            face_x = vision_data.get("face_x", 0.5)  # 默認在中間
            face_y = vision_data.get("face_y", 0.5)  # 默認在中間
            self.logger.debug(f"{COLORS['CYAN']}[FACE TRACKING] 追蹤人臉位置: x={face_x:.2f}, y={face_y:.2f}{COLORS['RESET']}")
            self.logger.debug(f"{COLORS['CYAN']}[FACE TRACKING] Tracking face position: x={face_x:.2f}, y={face_y:.2f}{COLORS['RESET']}")
            self.servo_controller.follow_face(face_x, face_y)
        
        # 檢查是否需要暂停偵測
        if current_time < self.detection_pause_until:
            # 在暂停期間，不進行任何偵測處理
            remaining_seconds = int(self.detection_pause_until - current_time)
            if remaining_seconds % 5 == 0 and remaining_seconds > 0:  # 每5秒輸出一次日誌
                self.logger.info(f"{COLORS['CYAN']}[PAUSE] 暫停偵測中，剩餘 {remaining_seconds} 秒{COLORS['RESET']}")
                self.logger.info(f"{COLORS['CYAN']}[PAUSE] 暂停偵測中，剩餘 {remaining_seconds} 秒{COLORS['RESET']}")
                self.logger.info(f"{COLORS['CYAN']}[PAUSE] Detection paused, {remaining_seconds} seconds remaining{COLORS['RESET']}")
            return
            
        # 如果識別出的是Sonia，重置所有警報狀態並暂停偵測30秒
        if face_detected and recognized_person and "sonia" in recognized_person.lower():
            self.logger.info(f"{COLORS['GREEN']}[FACE] 識別出已知人員: {recognized_person}{COLORS['RESET']}")
            self.logger.info(f"{COLORS['GREEN']}[FACE] Recognized known person: {recognized_person}{COLORS['RESET']}")
            
            # 設置眼睛顏色為綠色
            self.logger.info(f"{COLORS['GREEN']}[EYE COLOR] 設置眼睛顏色為綠色{COLORS['RESET']}")
            self.logger.info(f"{COLORS['GREEN']}[EYE COLOR] Setting eye color to green{COLORS['RESET']}")
            self.servo_controller.set_eye_color("green")
            
            # 播放開心音效
            self.logger.info(f"{COLORS['GREEN']}[SOUND] 播放開心音效{COLORS['RESET']}")
            self.logger.info(f"{COLORS['GREEN']}[SOUND] Playing happy sound{COLORS['RESET']}")
            self.sound_manager.play_happy_sound()
            
            # 放下手臂
            self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] 放下手臂{COLORS['RESET']}")
            self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] Lowering arms{COLORS['RESET']}")
            self.servo_controller.lower_arms()
            
            # 關閉激光指示器
            self.logger.info(f"{COLORS['CYAN']}[LASER] 關閉激光指示器{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[LASER] Deactivating laser pointer{COLORS['RESET']}")
            self.servo_controller.deactivate_laser()
            
            # 重置所有警報狀態
            self.surveillance_yellow_warning = False
            self.surveillance_intruder_detected = False
            self.alarm_active = False
            self.surveillance_countdown = 0
            
            # 設置暂停偵測30秒
            self.detection_pause_until = current_time + 30
            self.logger.info(f"{COLORS['CYAN']}[PAUSE] 識別到Sonia，暂停偵測30秒{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[PAUSE] Recognized Sonia, pausing detection for 30 seconds{COLORS['RESET']}")
            
            # 廣播安全消息到前端
            message = {
                "type": "recognition_result",
                "data": {
                    "recognized": True,
                    "name": recognized_person,  # Add explicit name field
                    "message": f"識別出已知人員: {recognized_person}, 暂停偵測30秒",
                    "countdown": 30,  # 顯示30秒倒計時
                    "confidence": confidence,
                    "emoji": "😊",
                    "eye_color": "green"
                }
            }
            
            # 如果有WebSocket服務器實例，廣播識別結果
            if hasattr(self, "websocket_server") and self.websocket_server:
                self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播安全消息到前端{COLORS['RESET']}")
                self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting safety message to frontend{COLORS['RESET']}")
                self.websocket_server.broadcast_status(message)
        
        # 如果檢測到人臉但不是Sonia
        elif face_detected and (not recognized_person or "sonia" not in recognized_person.lower()):
            # 如果還沒有黃色警告狀態，則設置眼睛為黃色
            if not self.surveillance_yellow_warning and not self.surveillance_intruder_detected:
                self.logger.warning(f"{COLORS['BOLD']}{COLORS['YELLOW']}[WARNING] 監視模式: 檢測到不明人員{COLORS['RESET']}")
                self.logger.warning(f"{COLORS['BOLD']}{COLORS['YELLOW']}[WARNING] Surveillance mode: Unknown person detected{COLORS['RESET']}")
                
                # 設置眼睛顏色為黃色
                self.logger.info(f"{COLORS['YELLOW']}[EYE COLOR] 設置眼睛顏色為黃色{COLORS['RESET']}")
                self.logger.info(f"{COLORS['YELLOW']}[EYE COLOR] Setting eye color to yellow{COLORS['RESET']}")
                self.servo_controller.set_eye_color("yellow")
                
                # 設置黃色警告狀態和開始時間
                self.surveillance_yellow_warning = True
                self.surveillance_yellow_start_time = current_time
                
                # 廣播警告消息到前端
                intruder_name = recognized_person if recognized_person else "Unknown Intruder"
                message = {
                    "type": "recognition_result",
                    "data": {
                        "recognized": False,
                        "name": intruder_name,  # Add explicit name field for intruder
                        "message": f"檢測到不明人員: {intruder_name}",
                        "countdown": 5,  # 5秒黃色警告
                        "confidence": confidence,
                        "emoji": "⚠️",
                        "eye_color": "yellow"
                    }
                }
                
                # 如果有WebSocket服務器實例，廣播識別結果
                if hasattr(self, "websocket_server") and self.websocket_server:
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播警告消息到前端{COLORS['RESET']}")
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting warning message to frontend{COLORS['RESET']}")
                    self.websocket_server.broadcast_status(message)
            
            # 如果已經在黃色警告狀態且已經過了5秒，則升級為紅色警報
            elif self.surveillance_yellow_warning and not self.surveillance_intruder_detected and (current_time - self.surveillance_yellow_start_time >= 5):
                self.logger.warning(f"{COLORS['BOLD']}{COLORS['RED']}[ALARM] 監視模式: 檢測到入侵者{COLORS['RESET']}")
                self.logger.warning(f"{COLORS['BOLD']}{COLORS['RED']}[ALARM] Surveillance mode: Intruder detected{COLORS['RESET']}")
                
                # 設置眼睛顏色為紅色
                self.logger.info(f"{COLORS['RED']}[EYE COLOR] 設置眼睛顏色為紅色{COLORS['RESET']}")
                self.logger.info(f"{COLORS['RED']}[EYE COLOR] Setting eye color to red{COLORS['RESET']}")
                self.servo_controller.set_eye_color("red")
                
                # 舉起手臂
                self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] 舉起手臂{COLORS['RESET']}")
                self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] Raising arms{COLORS['RESET']}")
                self.servo_controller.raise_arms()
                
                # 啟動激光指示器
                self.logger.info(f"{COLORS['CYAN']}[LASER] 啟動激光指示器{COLORS['RESET']}")
                self.logger.info(f"{COLORS['CYAN']}[LASER] Activating laser pointer{COLORS['RESET']}")
                self.servo_controller.activate_laser()
                
                # 播放入侵者警報音效
                self.logger.info(f"{COLORS['RED']}[SOUND] 播放入侵者警報音效{COLORS['RESET']}")
                self.logger.info(f"{COLORS['RED']}[SOUND] Playing intruder alert sound{COLORS['RESET']}")
                self.sound_manager.play_intruder_sound()
                
                # 設置倒計時
                self.surveillance_countdown = 10  # 10秒倒計時
                self.surveillance_yellow_warning = False  # 重置黃色警告狀態
                self.surveillance_intruder_detected = True
                self.alarm_active = True
                
                # 廣播警報消息到前端
                intruder_name = recognized_person if recognized_person else "Unknown Intruder"
                message = {
                    "type": "recognition_result",
                    "data": {
                        "recognized": False,
                        "name": intruder_name,  # Add explicit name field for intruder
                        "message": f"檢測到入侵者: {intruder_name}",
                        "countdown": self.surveillance_countdown,
                        "confidence": confidence,
                        "emoji": "🚨",
                        "eye_color": "red"
                    }
                }
                
                # 廣播警報模式消息 (為ESP32客戶端準備)
                alarm_mode_message = {
                    "type": "status_update",
                    "data": {
                        "mode": "alarm"
                    },
                    "id": f"alarm_{int(time.time() * 1000)}"
                }
                
                # 如果有WebSocket服務器實例，廣播識別結果和警報模式
                if hasattr(self, "websocket_server") and self.websocket_server:
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播警報消息到前端{COLORS['RESET']}")
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting alarm message to frontend{COLORS['RESET']}")
                    self.websocket_server.broadcast_status(message)
                    
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播警報模式消息 (mode=alarm_mode){COLORS['RESET']}")
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting alarm mode message (mode=alarm_mode){COLORS['RESET']}")
                    self.websocket_server.broadcast_status(alarm_mode_message)
            elif self.surveillance_countdown > 0:
                # 如果已經檢測到入侵者且倒計時大於0，則倒計時減1
                self.surveillance_countdown -= 1
                self.logger.warning(f"{COLORS['YELLOW']}[COUNTDOWN] 警報倒計時: {self.surveillance_countdown}{COLORS['RESET']}")
                self.logger.warning(f"{COLORS['YELLOW']}[COUNTDOWN] Alarm countdown: {self.surveillance_countdown}{COLORS['RESET']}")
                
                # 廣播倒計時消息到前端
                message = {
                    "type": "recognition_result",
                    "data": {
                        "recognized": False,
                        "message": f"入侵者警報倒計時: {self.surveillance_countdown}",
                        "countdown": self.surveillance_countdown,
                        "confidence": confidence,
                        "emoji": "🚨",
                        "eye_color": "red"
                    }
                }
                
                # 如果有WebSocket服務器實例，廣播識別結果
                if hasattr(self, "websocket_server") and self.websocket_server:
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播倒計時消息到前端{COLORS['RESET']}")
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting countdown message to frontend{COLORS['RESET']}")
                    self.websocket_server.broadcast_status(message)
                    
                # 如果倒計時結束，執行額外操作
                if self.surveillance_countdown == 0:
                    self.logger.warning(f"{COLORS['BOLD']}{COLORS['RED']}[ALARM] 監視模式: 警報倒計時結束{COLORS['RESET']}")
                    self.logger.warning(f"{COLORS['BOLD']}{COLORS['RED']}[ALARM] Surveillance mode: Alarm countdown ended{COLORS['RESET']}")
                    
                    # 這裡可以添加額外的警報操作
                    # 例如發送通知、拍照等
    
        # 如果沒有檢測到人臉，但之前有檢測到入侵者
        elif not face_detected and self.surveillance_intruder_detected:
            # 入侵者離開了，但如果警報狀態仍然活躍，則保持紅色狀態
            if not self.alarm_active:
                self.logger.info(f"{COLORS['GREEN']}[SURVEILLANCE] 未檢測到人臉，恢復正常狀態{COLORS['RESET']}")
                self.logger.info(f"{COLORS['GREEN']}[SURVEILLANCE] No face detected, restoring normal state{COLORS['RESET']}")
                
                self.logger.info(f"{COLORS['GREEN']}[EYE COLOR] 設置眼睛顏色為綠色{COLORS['RESET']}")
                self.logger.info(f"{COLORS['GREEN']}[EYE COLOR] Setting eye color to green{COLORS['RESET']}")
                self.servo_controller.set_eye_color("green")
                
                # 播放開心音效
                self.logger.info(f"{COLORS['GREEN']}[SOUND] 播放開心音效{COLORS['RESET']}")
                self.logger.info(f"{COLORS['GREEN']}[SOUND] Playing happy sound{COLORS['RESET']}")
                self.sound_manager.play_happy_sound()
                
                self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] 放下手臂{COLORS['RESET']}")
                self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] Lowering arms{COLORS['RESET']}")
                self.servo_controller.lower_arms()
                
                self.logger.info(f"{COLORS['CYAN']}[LASER] 關閉激光指示器{COLORS['RESET']}")
                self.logger.info(f"{COLORS['CYAN']}[LASER] Deactivating laser pointer{COLORS['RESET']}")
                self.servo_controller.deactivate_laser()
                
                self.surveillance_intruder_detected = False
                self.surveillance_countdown = 0
                
                # 廣播安全消息到前端
                message = {
                    "type": "recognition_result",
                    "data": {
                        "recognized": False,
                        "message": "沒有人在畫面中",
                        "countdown": 0,
                        "confidence": 0.0,
                        "emoji": "😊",
                        "eye_color": "green"
                    }
                }
                
                # 如果有WebSocket服務器實例，廣播識別結果
                if hasattr(self, "websocket_server") and self.websocket_server:
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播安全消息到前端{COLORS['RESET']}")
                    self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting safety message to frontend{COLORS['RESET']}")
                    self.websocket_server.broadcast_status(message)
            else:
                # 警報狀態仍然活躍，保持紅色狀態
                self.logger.info(f"{COLORS['RED']}[ALARM] 警報狀態仍然活躍，保持紅色狀態{COLORS['RESET']}")
                self.logger.info(f"{COLORS['RED']}[ALARM] Alarm is still active, maintaining red state{COLORS['RESET']}")
                self.surveillance_intruder_detected = True  # 保持入侵者標誌
    
    def clear_alarm(self):
        """解除警報狀態
        
        將警報狀態設置為非活躍，並將眼睛顏色設置為綠色
        """
        self.logger.info(f"{COLORS['GREEN']}[ALARM] 解除警報狀態{COLORS['RESET']}")
        self.logger.info(f"{COLORS['GREEN']}[ALARM] Clearing alarm state{COLORS['RESET']}")
        
        # 設置警報狀態為非活躍
        self.alarm_active = False
        self.surveillance_intruder_detected = False
        self.surveillance_countdown = 0
        
        # 設置眼睛顏色為綠色
        self.logger.info(f"{COLORS['GREEN']}[EYE COLOR] 設置眼睛顏色為綠色{COLORS['RESET']}")
        self.logger.info(f"{COLORS['GREEN']}[EYE COLOR] Setting eye color to green{COLORS['RESET']}")
        self.servo_controller.set_eye_color("green")
        
        self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] 放下手臂{COLORS['RESET']}")
        self.logger.info(f"{COLORS['MAGENTA']}[ARM MOVEMENT] Lowering arms{COLORS['RESET']}")
        self.servo_controller.lower_arms()
        
        self.logger.info(f"{COLORS['CYAN']}[LASER] 關閉激光指示器{COLORS['RESET']}")
        self.logger.info(f"{COLORS['CYAN']}[LASER] Deactivating laser pointer{COLORS['RESET']}")
        self.servo_controller.deactivate_laser()
        
        # 廣播安全消息到前端
        message = {
            "type": "recognition_result",
            "data": {
                "recognized": False,
                "message": "警報已解除",
                "countdown": 0,
                "confidence": 0.0,
                "emoji": "😊",
                "eye_color": "green"
            }
        }
        
        # 廣播正常模式消息 (為ESP32客戶端準備)
        normal_mode_message = {
            "type": "set_status",
            "robot_mode": "normal",
            "robot_name": "maomao",
            "id": f"normal_{int(time.time() * 1000)}"
        }
        
        # 如果有WebSocket服務器實例，廣播識別結果和正常模式
        if hasattr(self, "websocket_server") and self.websocket_server:
            self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播解除警報消息到前端{COLORS['RESET']}")
            self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting alarm clear message to frontend{COLORS['RESET']}")
            self.websocket_server.broadcast_status(message)
            
            self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] 廣播正常模式消息 (mode=normal){COLORS['RESET']}")
            self.logger.info(f"{COLORS['BLUE']}[WEBSOCKET] Broadcasting normal mode message (mode=normal){COLORS['RESET']}")
            self.websocket_server.broadcast_status(normal_mode_message)
        
    
    def set_patrol_active(self, active):
        """設置巡邏模式活動狀態
        
        Args: ... }}
            active (bool): 巡邏是否活動
        """
        self.logger.info(f"{COLORS['YELLOW']}[PATROL] 設置巡邏模式活動狀態為: {active}{COLORS['RESET']}")
        self.logger.info(f"{COLORS['YELLOW']}[PATROL] Setting patrol active state to: {active}{COLORS['RESET']}")
        self.patrol_active = active
        
        # 初始化巡邏模式相關變量
        if active:
            self.patrol_last_eye_blink_time = time.time()
            self.patrol_eye_blink_interval = random.uniform(10.0, 30.0)
            self.logger.info(f"{COLORS['CYAN']}[PATROL] 初始化眼睛眨眼周期: {self.patrol_eye_blink_interval:.1f} 秒{COLORS['RESET']}")
            self.logger.info(f"{COLORS['CYAN']}[PATROL] Initialized eye blink interval: {self.patrol_eye_blink_interval:.1f} seconds{COLORS['RESET']}")
        
        # 如果啟動巡邏，確保模式設置為巡邏模式
        if active and self.current_mode != RobotMode.PATROL:
            self.set_mode(RobotMode.PATROL)
    
    def get_status(self):
        """獲取模式管理器狀態
        
        Returns:
            dict: 模式管理器狀態
        """
        mode_name = self.current_mode.name if self.current_mode else "NONE"
        current_time = time.time()
        detection_paused = current_time < self.detection_pause_until
        pause_remaining = max(0, int(self.detection_pause_until - current_time)) if detection_paused else 0
        
        return {
            "current_mode": mode_name,
            "mode_duration": current_time - self.mode_start_time,
            "alarm_active": self.alarm_active,
            "patrol_active": self.patrol_active,
            "detection_paused": detection_paused,
            "pause_remaining": pause_remaining,
            "face_tracking_enabled": self.face_tracking_enabled
        }
