#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arduino LED整合測試腳本
此腳本用於測試通過Arduino控制MaoMao機器人的眼睛LED
"""

import os
import sys
import time
import logging
import colorama
from colorama import Fore, Style

# 設置LED控制方法環境變量
os.environ['LED_CONTROL_METHOD'] = 'arduino'

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 初始化 colorama
colorama.init(autoreset=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ArduinoLEDTest")

# 現在導入伺服控制器
from backend.servo.servo_controller import ServoController
from backend.utils.config_loader import ConfigLoader

class ArduinoLEDTester:
    """Arduino LED測試類"""
    
    def __init__(self):
        """初始化Arduino LED測試"""
        logger.info(f"{Fore.CYAN}初始化Arduino LED測試...")
        
        # 確保環境變量設置正確
        logger.info(f"當前LED控制方法: {os.environ.get('LED_CONTROL_METHOD', '未設置')}")
        
        # 載入配置
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        logger.info(f"已載入配置: {self.config['robot']['name']}")
        
        # 初始化伺服馬達控制器
        servo_config = self.config.get("servo", {})
        self.servo_controller = ServoController(servo_config)
        
        # 顯示硬體狀態
        from backend.servo.servo_controller import IS_RASPBERRY_PI, HARDWARE_AVAILABLE, USE_ARDUINO, LED_CONTROL_METHOD
        logger.info(f"{Fore.YELLOW}硬體狀態: IS_RASPBERRY_PI={IS_RASPBERRY_PI}, HARDWARE_AVAILABLE={HARDWARE_AVAILABLE}")
        logger.info(f"{Fore.YELLOW}LED控制狀態: USE_ARDUINO={USE_ARDUINO}, LED_CONTROL_METHOD={LED_CONTROL_METHOD}")
        
        # 可用的眼睛顏色
        self.eye_colors = ["green", "red", "yellow", "blue", "white", "off"]
        
        logger.info("Arduino LED測試初始化完成")
    
    def start(self):
        """執行測試"""
        logger.info(f"{Fore.GREEN}啟動Arduino LED測試...")
        
        # 啟動伺服馬達控制器
        self.servo_controller.start()
        
        # 測試所有顏色
        self.test_all_colors()
        
        logger.info("Arduino LED測試完成")
    
    def stop(self):
        """停止測試"""
        logger.info("停止Arduino LED測試...")
        
        # 關閉LED
        self.servo_controller.set_eye_color("off")
        
        # 停止伺服馬達控制器
        self.servo_controller.stop()
        
        logger.info("Arduino LED測試已停止")
    
    def test_all_colors(self):
        """測試所有顏色"""
        try:
            for color in self.eye_colors:
                if color == "off":  # 跳過關閉，留到最後
                    continue
                    
                logger.info(f"{Fore.CYAN}測試顏色: {color}")
                self.servo_controller.set_eye_color(color)
                time.sleep(2)  # 顯示每種顏色2秒
            
            # 最後關閉LED
            logger.info(f"{Fore.CYAN}關閉LED")
            self.servo_controller.set_eye_color("off")
            
        except Exception as e:
            logger.error(f"{Fore.RED}測試顏色時發生錯誤: {e}")
            import traceback
            logger.error(traceback.format_exc())

def main():
    """主函數"""
    print("\n" + "=" * 50)
    print(f"{Fore.CYAN}MaoMao Arduino LED測試程序")
    print("=" * 50 + "\n")
    
    tester = ArduinoLEDTester()
    
    try:
        tester.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}使用者中斷測試")
    except Exception as e:
        print(f"\n{Fore.RED}發生錯誤: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        tester.stop()
        print(f"\n{Fore.GREEN}測試已完成")

if __name__ == "__main__":
    main()
