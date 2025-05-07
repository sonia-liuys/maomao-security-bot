#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration Loader - Load and manage configurations
配置加載器 - 加載和管理配置
"""

import os
import json
import logging

class ConfigLoader:
    """Configuration Loader class, responsible for loading and managing configurations
    配置加載器類，負責加載和管理配置"""
    
    def __init__(self, config_path=None):
        """Initialize configuration loader
        
        Args:
            config_path (str, optional): Configuration file path, defaults to None
            
        初始化配置加載器
        
        Args:
            config_path (str, optional): 配置文件路徑，默認為None
        """
        self.logger = logging.getLogger("Config")
        
        # Default configuration file path
        # 默認配置文件路徑
        if config_path is None:
            self.config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config.json"
            )
        else:
            self.config_path = config_path
            
        self.config = None
    
    def load_config(self):
        """Load configuration
        
        Returns:
            dict: Configuration data
            
        加載配置
        
        Returns:
            dict: 配置數據
        """
        # Check if configuration file exists
        # 檢查配置文件是否存在
        if not os.path.exists(self.config_path):
            self.logger.warning(f"Configuration file does not exist: {self.config_path}, using default configuration")
            self.logger.warning(f"配置文件不存在: {self.config_path}，使用默認配置")
            self.config = self._get_default_config()
            self._save_config()
        else:
            try:
                # 從文件加載配置
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self.logger.info(f"已加載配置: {self.config_path}")
            except Exception as e:
                self.logger.error(f"加載配置出錯: {e}，使用默認配置")
                self.config = self._get_default_config()
        
        return self.config
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"已保存配置: {self.config_path}")
        except Exception as e:
            self.logger.error(f"保存配置出錯: {e}")
    
    def _get_default_config(self):
        """獲取默認配置
        
        Returns:
            dict: 默認配置數據
        """
        return {
            "robot": {
                "name": "毛毛安全機器人",
                "version": "1.0.0"
            },
            "vision": {
                "camera_index": 0,
                "frame_width": 640,
                "frame_height": 480,
                "model_path": "models/teachable_machine_model.tflite",
                "confidence_threshold": 0.7
            },
            "servo": {
                "eye_blink_interval": [2.0, 5.0],
                "arm_swing_interval": [3.0, 8.0]
            },
            "movement": {
                "serial_port": "/dev/ttyUSB0",
                "baud_rate": 115200
            },
            "communication": {
                "websocket_port": 8765
            },
            "modes": {
                "patrol_interval": 30,
                "surveillance_countdown": 5
            },
            "safety": {
                "check_interval": 1.0,
                "max_cpu_temp": 80.0,
                "max_cpu_usage": 90.0,
                "max_memory_usage": 90.0
            }
        }
