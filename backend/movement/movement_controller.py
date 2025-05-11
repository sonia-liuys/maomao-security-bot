#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Movement Controller - Manages the robot's movement functions
移動控制器 - 管理機器人的移動功能
"""

import logging
import threading
import time
import serial
import json

class MovementController:
    """Movement Controller class, manages the robot's movement functions
    移動控制器類，管理機器人的移動功能"""
    
    # Movement direction constants
    # 移動方向常量
    DIRECTION_FORWARD = "forward"
    DIRECTION_BACKWARD = "backward"
    DIRECTION_LEFT = "left"
    DIRECTION_RIGHT = "right"
    DIRECTION_STOP = "stop"
    DIRECTION_CONTINUOUS_FORWARD = "continuous_forward"
    DIRECTION_CONTINUOUS_BACKWARD = "continuous_backward"
    DIRECTION_SQUARE_PATH = "square_path"
    
    def __init__(self, config):
        """Initialize movement controller
        
        Args:
            config (dict): Movement controller configuration
            
        初始化移動控制器
        
        Args:
            config (dict): 移動控制器配置
        """
        self.logger = logging.getLogger("Movement")
        self.config = config
        
        # Serial port configuration
        # 串口配置
        self.serial_port = config.get("serial_port", "/dev/ttyUSB0")
        self.baud_rate = config.get("baud_rate", 115200)
        
        # Initialize status variables
        # 初始化狀態變數
        self.running = False
        self.serial_conn = None
        self.current_direction = self.DIRECTION_STOP
        self.obstacle_detected = False
        self.square_path_active = False
        self.square_path_step = 0
        
        # Processing thread
        # 處理線程
        self.thread = None
        self.lock = threading.Lock()
        
        # 初始化硬體連接
        self._init_hardware()
        
        self.logger.info("移動控制器初始化完成")
    
    def _init_hardware(self):
        """初始化硬體連接
        
        嘗試連接到Arduino的串口
        """
        self.logger.info("初始化移動控制器硬體連接...")
        
        try:
            # 打開與Arduino的串口連接
            self.serial_conn = serial.Serial(self.serial_port, self.baud_rate, timeout=1.0)
            time.sleep(0.5)  # 等待串口初始化
            self.logger.info(f"移動控制器硬體連接已就緒，串口: {self.serial_port}, 波特率: {self.baud_rate}")
            self.logger.info(f"Movement controller hardware connection ready, serial port: {self.serial_port}, baud rate: {self.baud_rate}")
        except Exception as e:
            self.logger.error(f"無法初始化移動控制器硬體: {e}")
            self.logger.error(f"Failed to initialize movement controller hardware: {e}")
            # 如果無法連接到串口，則使用模擬模式
            self.serial_conn = None
            self.logger.warning("使用模擬模式運行移動控制器")
            self.logger.warning("Running movement controller in simulation mode")
    
    def start(self):
        """啟動移動控制器
        Start movement controller
        """
        if self.running:
            return
            
        self.logger.info("啟動移動控制器...")
        self.logger.info("Starting movement controller...")
        self.running = True
        
        # 確保方形路徑模式關閉
        # Ensure square path mode is disabled
        with self.lock:
            self.square_path_active = False
            self.square_path_step = 0
        
        # 停止所有移動
        # Stop all movements
        self.stop()
        
        # 啟動處理線程
        # Start processing thread
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("移動控制器已啟動")
        self.logger.info("Movement controller started")
    
    def stop(self):
        """停止所有移動"""
        self.logger.info("停止所有移動")
        
        with self.lock:
            self.current_direction = self.DIRECTION_STOP
            self.square_path_active = False
            
        # 發送停止命令
        self._send_command("stop")
    
    def _stop_thread(self):
        """停止移動控制器線程"""
        if not self.running:
            return
            
        self.logger.info("停止移動控制器...")
        self.running = False
        
        # 停止所有移動
        self.stop()
        
        if self.thread:
            self.thread.join(timeout=1.0)
        
        # 關閉串口連接
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None
            
        self.logger.info("移動控制器已停止")
    
    def _update_loop(self):
        """移動控制器更新循環"""
        last_ultrasonic_check = 0
        
        while self.running:
            current_time = time.time()
            
            # 檢查超聲波感測器 (每100ms)
            if current_time - last_ultrasonic_check > 0.1:
                self._check_obstacles()
                last_ultrasonic_check = current_time
            
            # 處理方形路徑移動
            if self.square_path_active:
                self._update_square_path()
            
            # 控制更新頻率
            time.sleep(0.05)  # 20Hz
    
    def _check_obstacles(self):
        """檢查障礙物
        
        注意：這是一個模擬實現，實際部署時需要讀取真實的超聲波感測器數據
        """
        # 模擬檢測障礙物 (5%的概率)
        # 實際部署時，這裡會讀取超聲波感測器數據
        
        # 隨機模擬障礙物檢測
        # import random
        # obstacle_detected = random.random() < 0.05
        obstacle_detected = False
        
        # 如果檢測到障礙物且正在移動，則停止
        if obstacle_detected and self.current_direction != self.DIRECTION_STOP:
            self.logger.warning("檢測到障礙物，停止移動")
            self.stop()
            
        with self.lock:
            self.obstacle_detected = obstacle_detected
    
    def move(self, direction):
        """控制機器人移動
        
        Args:
            direction (str): 移動方向
            
        Returns:
            bool: 操作是否成功
        """
        valid_directions = [
            self.DIRECTION_FORWARD,
            self.DIRECTION_BACKWARD,
            self.DIRECTION_LEFT,
            self.DIRECTION_RIGHT,
            self.DIRECTION_STOP,
            self.DIRECTION_CONTINUOUS_FORWARD,
            self.DIRECTION_CONTINUOUS_BACKWARD,
            self.DIRECTION_SQUARE_PATH
        ]
        
        if direction not in valid_directions:
            self.logger.error(f"無效的移動方向: {direction}")
            return False
            
        self.logger.debug(f"移動方向: {direction}")
        
        with self.lock:
            self.current_direction = direction
            
            # 如果是方形路徑，啟動方形路徑移動
            if direction == self.DIRECTION_SQUARE_PATH:
                self.square_path_active = True
                self.square_path_step = 0
            else:
                self.square_path_active = False
        
        # 發送移動命令
        if direction != self.DIRECTION_SQUARE_PATH:
            self._send_command(direction)
            
        return True
    
    def _send_command(self, command, params=None):
        """發送命令到Arduino
        
        Args:
            command (str): 命令名稱
            params (dict, optional): 命令參數
            
        Returns:
            bool: 命令發送是否成功
        """
        if not params:
            params = {}
        
        # 根據指定的命令格式轉換命令
        arduino_command = command
        
        # 將命令轉換為 Arduino 可以識別的格式
        # Convert commands to Arduino-recognizable format
        if command == self.DIRECTION_FORWARD:
            arduino_command = "move_forward"
        elif command == self.DIRECTION_BACKWARD:
            arduino_command = "move_backward"
        elif command == self.DIRECTION_LEFT:
            arduino_command = "move_left"
        elif command == self.DIRECTION_RIGHT:
            arduino_command = "move_right"
        elif command == self.DIRECTION_STOP:
            arduino_command = "stop"
        elif command == "start_patrol":
            arduino_command = "start_patrol"
            # 設置方形路徑模式為啟動狀態
            # Set square path mode to active state
            with self.lock:
                self.square_path_active = True
                self.square_path_step = 0
        
        # 將命令直接發送到 Arduino
        self.logger.info(f"發送命令到Arduino: {arduino_command}")
        self.logger.info(f"Sending command to Arduino: {arduino_command}")
        
        # 實際發送命令
        try:
            if self.serial_conn and self.serial_conn.is_open:
                # 發送命令到Arduino
                self.serial_conn.write(f"{arduino_command}\n".encode())
                self.logger.info(f"命令 '{arduino_command}' 已發送到Arduino")
                self.logger.info(f"Command '{arduino_command}' sent to Arduino")
                return True
            else:
                # 如果在測試模式下，模擬發送成功
                self.logger.warning("串口未開啟，模擬發送命令")
                self.logger.warning("Serial port not open, simulating command send")
                self.logger.info(f"模擬發送 '{arduino_command}' 命令到Arduino")
                self.logger.info(f"Simulating sending '{arduino_command}' command to Arduino")
                return True  # 模擬模式下返回成功
                
        except Exception as e:
            self.logger.error(f"發送命令失敗: {e}")
            self.logger.error(f"Failed to send command: {e}")
            return False
    
    def _update_square_path(self):
        """更新方形路徑移動"""
        if not self.square_path_active:
            return
            
        # 方形路徑的四個步驟：前進、右轉、前進、右轉、前進、右轉、前進、右轉
        steps = [
            (self.DIRECTION_FORWARD, 1.0),    # 前進1秒
            (self.DIRECTION_RIGHT, 0.5),      # 右轉0.5秒 (90度)
            (self.DIRECTION_FORWARD, 1.0),    # 前進1秒
            (self.DIRECTION_RIGHT, 0.5),      # 右轉0.5秒 (90度)
            (self.DIRECTION_FORWARD, 1.0),    # 前進1秒
            (self.DIRECTION_RIGHT, 0.5),      # 右轉0.5秒 (90度)
            (self.DIRECTION_FORWARD, 1.0),    # 前進1秒
            (self.DIRECTION_RIGHT, 0.5),      # 右轉0.5秒 (90度)
        ]
        
        # 獲取當前步驟
        current_step = self.square_path_step % len(steps)
        direction, duration = steps[current_step]
        
        # 執行當前步驟
        self._send_command(direction)
        time.sleep(duration)
        self._send_command(self.DIRECTION_STOP)
        
        # 更新步驟
        self.square_path_step += 1
        
        # 完成一個完整的方形路徑後停止
        if self.square_path_step >= len(steps):
            with self.lock:
                self.square_path_active = False
                self.current_direction = self.DIRECTION_STOP
    
    def move_square_path(self):
        """執行方形路徑移動"""
        self.move(self.DIRECTION_SQUARE_PATH)
        
    def start_patrol(self):
        """啟動巡邏模式下的小車移動
        
        向 Arduino 發送巡邏命令，啟動小車的巡邏行為
        
        Returns:
            bool: 啟動巡邏是否成功
        """
        self.logger.info("啟動巡邏模式下的小車移動")
        self.logger.info("Starting car movement in patrol mode")
        
        # 發送巡邏命令到 Arduino
        success = self._send_command("start_patrol")
        
        if success:
            self.logger.info("已成功啟動巡邏模式")
            self.logger.info("Successfully started patrol mode")
        else:
            self.logger.error("啟動巡邏模式失敗")
            self.logger.error("Failed to start patrol mode")
            
        return success
        
    def start_continuous_movement(self, direction):
        """開始連續移動
        
        Args:
            direction (str): 移動方向 ("forward", "backward", "left", "right")
            
        Returns:
            bool: 操作是否成功
        """
        valid_directions = [
            self.DIRECTION_FORWARD,
            self.DIRECTION_BACKWARD,
            self.DIRECTION_LEFT,
            self.DIRECTION_RIGHT
        ]
        
        if direction not in valid_directions:
            self.logger.error(f"無效的移動方向: {direction}")
            self.logger.error(f"Invalid movement direction: {direction}")
            return False
            
        self.logger.info(f"開始連續移動: {direction}")
        self.logger.info(f"Starting continuous movement: {direction}")
        
        with self.lock:
            self.current_direction = direction
            
        # 發送移動命令到Arduino
        return self._send_command(direction)
    
    def get_status(self):
        """獲取移動控制器狀態
        
        Returns:
            dict: 移動控制器狀態
        """
        with self.lock:
            return {
                "current_direction": self.current_direction,
                "obstacle_detected": self.obstacle_detected,
                "square_path_active": self.square_path_active
            }
