#!/usr/bin/env python3
# -*- coding: utf-8 -*-
### AI GENERATED CODE ###

"""
毛毛安全機器人 - 主程序
"""

import time
import logging
import signal
import sys
from core.robot_controller import RobotController
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

# 設置日誌
logger = setup_logger()

def signal_handler(sig, frame):
    """處理程序終止信號"""
    logger.info("接收到終止信號，正在關閉機器人...")
    if robot_controller:
        robot_controller.shutdown()
    sys.exit(0)

def main():
    """主程序入口"""
    logger.info("啟動毛毛安全機器人...")
    
    # 載入配置
    config = ConfigLoader().load_config()
    logger.info(f"已載入配置: {config['robot']['name']}")
    
    # 初始化機器人控制器
    global robot_controller
    robot_controller = RobotController(config)
    
    # 註冊信號處理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 啟動機器人
        robot_controller.start()
        
        # 主循環
        while True:
            robot_controller.update()
            time.sleep(1.0)  # 1Hz更新頻率，每秒一次
            
    except Exception as e:
        logger.error(f"主程序發生錯誤: {e}")
        if robot_controller:
            robot_controller.shutdown()
        raise

if __name__ == "__main__":
    main()
