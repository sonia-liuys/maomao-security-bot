#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模式管理器 - 控制機器人的不同運行模式
"""

import logging
import time
from enum import Enum, auto
import random
import os
from utils.audio_player import play_sound

class RobotMode(Enum):
    """機器人運行模式枚舉"""
    MANUAL = auto()       # 手動模式
    PATROL = auto()       # 巡邏模式
    SURVEILLANCE = auto() # 監視模式

class ModeManager:
    """機器人模式管理器，處理不同模式的邏輯和轉換"""
    
    def __init__(self, vision_system, servo_controller, movement_controller, config):
        """初始化模式管理器
        
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
        
        self.current_mode = None
        self.mode_start_time = 0
        
        # 模式特定狀態
        self.patrol_last_move_time = 0
        self.patrol_active = False  # 添加巡邏模式活動狀態
        self.surveillance_countdown = 0
        self.surveillance_intruder_detected = False
        self.student_id_detection_pause_until = 0
        self.alarm_active = False  # 添加警報狀態屬性
        self.websocket_server = None  # 將在RobotController中設置
        
        # 設置警報音效路徑
        # Set alarm sound file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.alarm_sound_path = os.path.join(script_dir, "../assets/sounds/alarm.wav")
        
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
        # 模式特定初始化
        if mode == RobotMode.MANUAL:
            # 手動模式下啟動自然眨眼和手臂擺動
            self.servo_controller.start_natural_blinking()
            self.servo_controller.start_arm_swinging()
            
        elif mode == RobotMode.PATROL:
            # 巡邏模式下啟動自動巡邏
            self.patrol_last_move_time = time.time()
            
        elif mode == RobotMode.SURVEILLANCE:
            # 監視模式下準備監控
            pass
    
    def _exit_mode(self, mode):
        """退出指定模式時的處理
        
        Args:
            mode (RobotMode): 要退出的模式
        """
        # 停止所有運動
        self.movement_controller.stop()
        
        # 模式特定清理
        if mode == RobotMode.MANUAL:
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
        # 手動模式下，大部分操作由用戶控制
        # 這裡可以添加一些自動響應邏輯
        pass
    
    def _update_patrol_mode(self, vision_data):
        """更新巡邏模式
        
        Args:
            vision_data (dict): 視覺系統提供的最新數據
        """
        # 如果巡邏模式未啟動，則不執行任何操作
        if not self.patrol_active:
            return
            
        current_time = time.time()
        
        # 檢查是否需要移動
        # 每隔一段時間隨機選擇一個方向移動
        if current_time - self.patrol_last_move_time > 5.0:  # 每5秒移動一次
            self.patrol_last_move_time = current_time
            
            # 隨機選擇一個方向
            directions = ["forward", "backward", "left", "right"]
            direction = random.choice(directions)
            
            self.logger.info(f"巡邏模式: 移動方向 {direction}")
            self.movement_controller.move(direction)
            
            # 短暫移動後停止
            time.sleep(1.0)
            self.movement_controller.stop()
    
    def _update_surveillance_mode(self, vision_data):
        """更新監視模式
        
        Args:
            vision_data (dict): 視覺系統提供的最新數據
        """
        # 檢查是否檢測到人臉
        face_detected = vision_data.get("face_detected", False)
        recognized_person = vision_data.get("recognized_person", "")
        confidence = vision_data.get("confidence", 0.0)
        
        # 檢查是否需要暫停學生證檢測
        current_time = time.time()
        if current_time < self.student_id_detection_pause_until:
            # 暫停學生證檢測
            return
            
        # 如果檢測到人臉但不是已知人員
        if face_detected and (not recognized_person or recognized_person == "unknown"):
            if not self.surveillance_intruder_detected:
                self.logger.warning("監視模式: 檢測到未知人員")
                
                # 設置眼睛顏色為紅色
                self.servo_controller.set_eye_color("red")
                
                # 啟動警報
                self.alarm_active = True
                
                # 舉起手臂
                self.servo_controller.raise_arms()
                
                # 啟動激光
                self.servo_controller.activate_laser()
                
                # 播放警報聲
                play_sound(self.alarm_sound_path)
                
                # 設置倒計時
                self.surveillance_countdown = 10  # 10秒倒計時
                self.surveillance_intruder_detected = True
                
                # 廣播警報消息到前端
                message = {
                    "type": "recognition_result",
                    "data": {
                        "recognized": False,
                        "message": "檢測到未知人員",
                        "countdown": self.surveillance_countdown,
                        "confidence": confidence,
                        "emoji": "🚨",
                        "eye_color": "red"
                    }
                }
                
                # 如果有WebSocket服務器實例，廣播識別結果
                if hasattr(self, "websocket_server") and self.websocket_server:
                    self.logger.info(f"廣播警報消息到前端: {message}")
                    self.logger.info(f"Broadcasting alarm message to frontend: {message}")
                    self.websocket_server.broadcast_status(message)
                    self.logger.info("已廣播警報消息到前端")
            
            # 更新倒計時
            if self.surveillance_countdown > 0:
                self.surveillance_countdown -= 1
                
                # 廣播倒計時消息到前端
                message = {
                    "type": "recognition_result",
                    "data": {
                        "recognized": False,
                        "message": f"警報倒計時: {self.surveillance_countdown}",
                        "countdown": self.surveillance_countdown,
                        "confidence": confidence,
                        "emoji": "🚨",
                        "eye_color": "red"
                    }
                }
                
                # 如果有WebSocket服務器實例，廣播識別結果
                if hasattr(self, "websocket_server") and self.websocket_server:
                    self.logger.info(f"廣播倒計時消息到前端: {message}")
                    self.logger.info(f"Broadcasting countdown message to frontend: {message}")
                    self.websocket_server.broadcast_status(message)
                    self.logger.info("已廣播倒計時消息到前端")
                    
                # 如果倒計時結束，執行額外操作
                if self.surveillance_countdown == 0:
                    self.logger.warning("監視模式: 警報倒計時結束")
                    
                    # 這裡可以添加額外的警報操作
                    # 例如發送通知、拍照等
        
        # 如果沒有檢測到人臉，但之前有檢測到入侵者
        elif not face_detected and self.surveillance_intruder_detected:
            # 入侵者離開了，但如果警報狀態仍然活躍，則保持紅色狀態
            if not self.alarm_active:
                self.servo_controller.set_eye_color("green")
                self.servo_controller.lower_arms()
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
                    self.logger.info(f"廣播安全消息到前端: {message}")
                    self.logger.info(f"Broadcasting safety message to frontend: {message}")
                    self.websocket_server.broadcast_status(message)
                    self.logger.info("已廣播安全消息到前端")
            else:
                # 警報狀態仍然活躍，保持紅色狀態
                self.logger.info("警報狀態仍然活躍，保持紅色狀態")
                self.logger.info("Alarm is still active, maintaining red state")
                self.surveillance_intruder_detected = True  # 保持入侵者標誌
    
    def clear_alarm(self):
        """解除警報狀態
        
        將警報狀態設置為非活躍，並將眼睛顏色設置為綠色
        """
        self.logger.info("解除警報狀態")
        self.logger.info("Clearing alarm state")
        
        # 設置警報狀態為非活躍
        self.alarm_active = False
        self.surveillance_intruder_detected = False
        self.surveillance_countdown = 0
        
        # 設置眼睛顏色為綠色
        self.servo_controller.set_eye_color("green")
        self.servo_controller.lower_arms()
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
        
        # 如果有WebSocket服務器實例，廣播識別結果
        if hasattr(self, "websocket_server") and self.websocket_server:
            self.logger.info(f"廣播解除警報消息到前端: {message}")
            self.logger.info(f"Broadcasting alarm clear message to frontend: {message}")
            self.websocket_server.broadcast_status(message)
            self.logger.info("已廣播解除警報消息到前端")
    
    def set_patrol_active(self, active):
        """設置巡邏模式活動狀態
        
        Args:
            active (bool): 巡邏是否活動
        """
        self.logger.info(f"設置巡邏模式活動狀態為: {active}")
        self.logger.info(f"Setting patrol active state to: {active}")
        self.patrol_active = active
        
        # 如果啟動巡邏，確保模式設置為巡邏模式
        if active and self.current_mode != RobotMode.PATROL:
            self.set_mode(RobotMode.PATROL)
    
    def get_status(self):
        """獲取模式管理器狀態
        
        Returns:
            dict: 模式管理器狀態
        """
        mode_name = self.current_mode.name if self.current_mode else "NONE"
        
        return {
            "current_mode": mode_name,
            "mode_duration": time.time() - self.mode_start_time,
            "alarm_active": self.alarm_active,
            "patrol_active": self.patrol_active
        }
