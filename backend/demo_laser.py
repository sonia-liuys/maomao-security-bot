#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
機器人激光模組演示程式
專注於控制激光指示器
"""

import os
import sys
import time
import logging
import argparse
from colorama import Fore, Back, Style, init

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入必要的模組
from backend.servo.servo_controller import ServoController
from backend.utils.config_loader import ConfigLoader

# 初始化 colorama
init(autoreset=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LaserDemo")

def main():
    """主函數"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description='機器人激光模組演示')
    parser.add_argument('--mode', type=str, default='demo', choices=['demo', 'toggle', 'on', 'off'],
                        help='演示模式: demo(演示), toggle(切換), on(開啟), off(關閉)')
    parser.add_argument('--duration', type=int, default=5,
                        help='演示持續時間（秒）')
    parser.add_argument('--blinks', type=int, default=3,
                        help='閃爍次數')
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("啟動機器人激光模組演示程式")
    logger.info("Starting robot laser module demo program")
    logger.info("=" * 50)
    
    # 載入配置
    config_loader = ConfigLoader()
    config = config_loader.load_config()
    logger.info(f"已載入配置: {config['robot']['name']}")
    
    # 初始化伺服控制器
    servo_controller = ServoController(config)
    
    try:
        # 根據模式執行不同操作
        if args.mode == 'demo':
            logger.info(f"執行激光演示，持續 {args.duration} 秒，閃爍 {args.blinks} 次")
            logger.info(f"Running laser demo for {args.duration} seconds with {args.blinks} blinks")
            servo_controller.laser_demo(duration=args.duration, blink_count=args.blinks)
            
        elif args.mode == 'toggle':
            logger.info("切換激光狀態")
            logger.info("Toggling laser state")
            new_state = servo_controller.toggle_laser()
            logger.info(f"激光新狀態: {'開啟' if new_state else '關閉'}")
            logger.info(f"New laser state: {'ON' if new_state else 'OFF'}")
            
        elif args.mode == 'on':
            logger.info("開啟激光")
            logger.info("Turning laser ON")
            servo_controller.activate_laser()
            
        elif args.mode == 'off':
            logger.info("關閉激光")
            logger.info("Turning laser OFF")
            servo_controller.deactivate_laser()
        
        # 如果不是演示模式，等待用戶按下 Ctrl+C
        if args.mode != 'demo':
            logger.info("按下 Ctrl+C 退出程式")
            logger.info("Press Ctrl+C to exit")
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("使用者中斷，停止演示")
        logger.info("User interrupt, stopping demo")
        # 確保激光關閉
        servo_controller.deactivate_laser()
    except Exception as e:
        logger.error(f"發生錯誤: {e}")
        logger.error(f"Error occurred: {e}")
        # 確保激光關閉
        servo_controller.deactivate_laser()
    finally:
        logger.info("演示程式已結束")
        logger.info("Demo program ended")

if __name__ == "__main__":
    main()
