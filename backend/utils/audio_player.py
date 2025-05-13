#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音頻播放器模塊
Audio player module

這個模塊提供了跨平台（OSX和Raspberry Pi）的音頻播放功能
This module provides cross-platform (OSX and Raspberry Pi) audio playback functionality
"""

import os
import threading
import logging
import platform
import subprocess

# 設置日誌
# Set up logging
logger = logging.getLogger(__name__)

class AudioPlayer:
    """音頻播放器類，提供跨平台的音頻播放功能
    Audio player class, providing cross-platform audio playback functionality
    """
    
    def __init__(self):
        """初始化音頻播放器
        Initialize audio player
        """
        self.logger = logging.getLogger(__name__)
        self.system = platform.system()
        self.logger.info(f"音頻播放器初始化於 {self.system} 系統")
        self.logger.info(f"Audio player initialized on {self.system} system")
        
        # 檢查是否在樹莓派上運行
        # Check if running on Raspberry Pi
        self.is_raspberry_pi = self._is_raspberry_pi()
        if self.is_raspberry_pi:
            self.logger.info("檢測到樹莓派環境")
            self.logger.info("Raspberry Pi environment detected")
    
    def _is_raspberry_pi(self):
        """檢查是否在樹莓派上運行
        Check if running on Raspberry Pi
        
        Returns:
            bool: 是否在樹莓派上運行 (Whether running on Raspberry Pi)
        """
        try:
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                return 'Raspberry Pi' in model
        except:
            # 如果文件不存在或無法讀取，則不是樹莓派
            # If the file doesn't exist or can't be read, it's not Raspberry Pi
            return False
    
    def play_sound(self, sound_file, blocking=False):
        """播放音頻文件
        Play audio file
        
        Args:
            sound_file (str): 音頻文件路徑 (Path to audio file)
            blocking (bool, optional): 是否阻塞等待播放完成 (Whether to block waiting for playback to complete).
                                      默認為 False (Defaults to False)
        
        Returns:
            bool: 是否成功啟動播放 (Whether playback was successfully started)
        """
        # 確保文件存在
        # Ensure file exists
        if not os.path.exists(sound_file):
            self.logger.error(f"音頻文件不存在: {sound_file}")
            self.logger.error(f"Audio file does not exist: {sound_file}")
            return False
        
        # 根據平台選擇播放方式
        # Choose playback method based on platform
        if blocking:
            return self._play_blocking(sound_file)
        else:
            # 使用線程非阻塞播放
            # Use thread for non-blocking playback
            thread = threading.Thread(target=self._play_blocking, args=(sound_file,))
            thread.daemon = True  # 設為守護線程，主程序退出時自動結束
            thread.start()
            return True
    
    def _play_blocking(self, sound_file):
        """以阻塞方式播放音頻
        Play audio in blocking mode
        
        Args:
            sound_file (str): 音頻文件路徑 (Path to audio file)
            
        Returns:
            bool: 是否成功播放 (Whether playback was successful)
        """
        try:
            if self.system == "Darwin":  # macOS
                # 使用afplay (macOS內建命令)
                # Use afplay (built-in macOS command)
                self.logger.info(f"使用 afplay 播放: {sound_file}")
                self.logger.info(f"Playing with afplay: {sound_file}")
                subprocess.call(["afplay", sound_file])
                return True
            elif self.is_raspberry_pi or self.system == "Linux":
                # 在樹莓派或Linux上使用aplay
                # Use aplay on Raspberry Pi or Linux
                self.logger.info(f"使用 aplay 播放: {sound_file}")
                self.logger.info(f"Playing with aplay: {sound_file}")
                subprocess.call(["aplay", sound_file])
                return True
            else:
                self.logger.error(f"不支持的平台: {self.system}")
                self.logger.error(f"Unsupported platform: {self.system}")
                return False
        except Exception as e:
            self.logger.error(f"播放音頻時出錯: {e}")
            self.logger.error(f"Error playing audio: {e}")
            return False

# 創建一個單例實例
# Create a singleton instance
player = AudioPlayer()

def play_sound(sound_file, blocking=False):
    """播放音頻文件的便捷函數
    Convenience function to play audio file
    
    Args:
        sound_file (str): 音頻文件路徑 (Path to audio file)
        blocking (bool, optional): 是否阻塞等待播放完成 (Whether to block waiting for playback to complete).
                                  默認為 False (Defaults to False)
    
    Returns:
        bool: 是否成功啟動播放 (Whether playback was successfully started)
    """
    return player.play_sound(sound_file, blocking)
