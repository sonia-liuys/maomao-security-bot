#!/usr/bin/env python3
# -*- coding: utf-8 -*-
### AI GENERATED CODE ###

"""
看門狗模組 - 監控系統狀態和處理異常情況
"""

import logging
import threading
import time
import os
import psutil

class Watchdog:
    """看門狗類，監控系統狀態和處理異常情況"""
    
    def __init__(self, robot_controller, config):
        """初始化看門狗
        
        Args:
            robot_controller: 機器人控制器實例
            config (dict): 看門狗配置
        """
        self.logger = logging.getLogger("Watchdog")
        self.robot_controller = robot_controller
        self.config = config
        
        # 配置參數
        self.check_interval = config.get("check_interval", 1.0)  # 檢查間隔，默認1秒
        self.max_cpu_temp = config.get("max_cpu_temp", 80.0)  # 最大CPU溫度，默認80°C
        self.max_cpu_usage = config.get("max_cpu_usage", 90.0)  # 最大CPU使用率，默認90%
        self.max_memory_usage = config.get("max_memory_usage", 90.0)  # 最大內存使用率，默認90%
        
        # 初始化狀態變數
        self.running = False
        self.start_time = 0
        self.thread = None
        
        self.logger.info("看門狗初始化完成")
    
    def start(self):
        """啟動看門狗"""
        if self.running:
            return
            
        self.logger.info("啟動看門狗...")
        self.running = True
        self.start_time = time.time()
        
        # 啟動監控線程
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("看門狗已啟動")
    
    def stop(self):
        """停止看門狗"""
        if not self.running:
            return
            
        self.logger.info("停止看門狗...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
            
        self.logger.info("看門狗已停止")
    
    def _monitor_loop(self):
        """監控循環"""
        while self.running:
            try:
                # 檢查系統狀態
                self._check_system_status()
                
                # 等待下一次檢查
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"監控循環出錯: {e}")
    
    def _check_system_status(self):
        """檢查系統狀態"""
        # 檢查CPU溫度
        cpu_temp = self._get_cpu_temperature()
        if cpu_temp > self.max_cpu_temp:
            self.logger.warning(f"CPU溫度過高: {cpu_temp}°C")
            self._handle_overheating()
        
        # 檢查CPU使用率
        cpu_usage = psutil.cpu_percent(interval=None)
        if cpu_usage > self.max_cpu_usage:
            self.logger.warning(f"CPU使用率過高: {cpu_usage}%")
        
        # 檢查內存使用率
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent
        if memory_usage > self.max_memory_usage:
            self.logger.warning(f"內存使用率過高: {memory_usage}%")
        
        # 檢查磁盤空間
        disk_usage = psutil.disk_usage('/').percent
        if disk_usage > 90:
            self.logger.warning(f"磁盤使用率過高: {disk_usage}%")
    
    def _get_cpu_temperature(self):
        """獲取CPU溫度
        
        Returns:
            float: CPU溫度 (°C)
        """
        # 這是樹莓派特定的溫度讀取方法
        # 實際部署時，根據硬體平台可能需要調整
        try:
            # 嘗試從樹莓派的溫度文件讀取
            temp_file = "/sys/class/thermal/thermal_zone0/temp"
            if os.path.exists(temp_file):
                with open(temp_file, "r") as f:
                    temp = float(f.read()) / 1000.0
                return temp
        except Exception as e:
            self.logger.error(f"讀取CPU溫度出錯: {e}")
        
        # 如果無法讀取，返回模擬值
        return 45.0  # 模擬溫度
    
    def _handle_overheating(self):
        """處理過熱情況"""
        self.logger.warning("檢測到過熱情況，採取措施...")
        
        # 通知機器人控制器
        # 實際部署時，可以採取措施如降低性能、暫停某些功能等
        pass
    
    def get_uptime(self):
        """獲取系統運行時間
        
        Returns:
            float: 運行時間 (秒)
        """
        return time.time() - self.start_time
