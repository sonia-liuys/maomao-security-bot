#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
眨眼皮測試程式 - 專門用於測試機器人的眨眼皮功能
Eyelid Blinking Test Program - Specifically for testing robot's eyelid blinking function
"""

import os
import sys
import time
import logging
import colorama
from colorama import Fore, Style

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入必要的模組
from backend.utils.config_loader import ConfigLoader
from backend.servo.servo_controller import ServoController

# 初始化 colorama
colorama.init(autoreset=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("BlinkTest")

class EyelidBlinkTest:
    """眨眼皮測試類"""
    
    def __init__(self):
        """初始化眨眼皮測試"""
        logger.info(f"{Fore.CYAN}初始化眨眼皮測試程式...")
        logger.info(f"{Fore.CYAN}Initializing eyelid blink test program...")
        
        # 載入配置
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        logger.info(f"已載入配置: {self.config['robot']['name']}")
        logger.info(f"Loaded configuration: {self.config['robot']['name']}")
        
        # 初始化伺服馬達控制器
        servo_config = self.config.get("servo", {})
        self.servo_controller = ServoController(servo_config)
        
        # 顯示硬體狀態
        from backend.servo.servo_controller import IS_RASPBERRY_PI, HARDWARE_AVAILABLE
        logger.info(f"{Fore.YELLOW}硬體狀態: IS_RASPBERRY_PI={IS_RASPBERRY_PI}, HARDWARE_AVAILABLE={HARDWARE_AVAILABLE}")
        logger.info(f"{Fore.YELLOW}Hardware status: IS_RASPBERRY_PI={IS_RASPBERRY_PI}, HARDWARE_AVAILABLE={HARDWARE_AVAILABLE}")
        
        logger.info("眨眼皮測試程式初始化完成")
        logger.info("Eyelid blink test initialization complete")
    
    def start(self):
        """啟動測試"""
        logger.info(f"{Fore.GREEN}啟動眨眼皮測試...")
        logger.info(f"{Fore.GREEN}Starting eyelid blink test...")
        
        # 啟動伺服馬達控制器
        self.servo_controller.start()
        
        # 設置眼睛顏色為綠色
        self.servo_controller.set_eye_color("green")
        logger.info("眼睛顏色設為綠色")
        logger.info("Eye color set to green")
        
        # 執行測試
        self._run_tests()
        
        logger.info("眨眼皮測試完成")
        logger.info("Eyelid blink test completed")
    
    def stop(self):
        """停止測試"""
        logger.info("停止眨眼皮測試...")
        logger.info("Stopping eyelid blink test...")
        
        # 停止伺服馬達控制器
        self.servo_controller.stop()
        
        logger.info("眨眼皮測試已停止")
        logger.info("Eyelid blink test stopped")
    
    def _run_tests(self):
        """執行一系列眨眼皮測試"""
        try:
            # 測試 1: 打開眼皮
            logger.info(f"{Fore.CYAN}[測試 1] 打開眼皮")
            logger.info(f"{Fore.CYAN}[Test 1] Opening eyelids")
            self.servo_controller.open_eyelids()
            time.sleep(2)
            
            # 測試 2: 閉上眼皮
            logger.info(f"{Fore.CYAN}[測試 2] 閉上眼皮")
            logger.info(f"{Fore.CYAN}[Test 2] Closing eyelids")
            self.servo_controller.close_eyelids()
            time.sleep(2)
            
            # 測試 3: 再次打開眼皮
            logger.info(f"{Fore.CYAN}[測試 3] 再次打開眼皮")
            logger.info(f"{Fore.CYAN}[Test 3] Opening eyelids again")
            self.servo_controller.open_eyelids()
            time.sleep(2)
            
            # 測試 4: 眨眼 3 次
            logger.info(f"{Fore.CYAN}[測試 4] 眨眼 3 次")
            logger.info(f"{Fore.CYAN}[Test 4] Blinking 3 times")
            for i in range(3):
                logger.info(f"眨眼 {i+1}/3")
                logger.info(f"Blink {i+1}/3")
                self.servo_controller._blink_eyelids()
                time.sleep(1)
            
            # 測試 5: 自然眨眼測試 (10 秒)
            logger.info(f"{Fore.CYAN}[測試 5] 自然眨眼測試 (10 秒)")
            logger.info(f"{Fore.CYAN}[Test 5] Natural blinking test (10 seconds)")
            
            # 設置較短的眨眼間隔，以便在測試中看到多次眨眼
            self.servo_controller.eyelid_blink_interval_min = 2.0
            self.servo_controller.eyelid_blink_interval_max = 4.0
            
            # 啟動自然眨眼
            self.servo_controller.start_eyelid_blinking()
            
            # 等待 10 秒
            for i in range(10):
                logger.info(f"自然眨眼測試: {i+1}/10 秒")
                logger.info(f"Natural blinking test: {i+1}/10 seconds")
                time.sleep(1)
            
            # 停止自然眨眼
            self.servo_controller.stop_eyelid_blinking()
            
            # 測試 6: 眼皮位置測試
            logger.info(f"{Fore.CYAN}[測試 6] 眼皮位置測試")
            logger.info(f"{Fore.CYAN}[Test 6] Eyelid position test")
            
            # 顯示眼皮伺服馬達 ID
            logger.info(f"左眼下眼皮 ID: {self.servo_controller.SERVO_LEFT_LID_LOWER}")
            logger.info(f"右眼下眼皮 ID: {self.servo_controller.SERVO_RIGHT_LID_LOWER}")
            logger.info(f"左眼上眼皮 ID: {self.servo_controller.SERVO_LEFT_LID_UPPER}")
            logger.info(f"右眼上眼皮 ID: {self.servo_controller.SERVO_RIGHT_LID_UPPER}")
            
            # 直接設置眼皮位置
            logger.info("設置左眼下眼皮位置: 160")
            self.servo_controller.set_position(self.servo_controller.SERVO_LEFT_LID_LOWER, 160)
            time.sleep(1)
            
            logger.info("設置右眼下眼皮位置: 20")
            self.servo_controller.set_position(self.servo_controller.SERVO_RIGHT_LID_LOWER, 20)
            time.sleep(1)
            
            logger.info("設置左眼上眼皮位置: 20")
            self.servo_controller.set_position(self.servo_controller.SERVO_LEFT_LID_UPPER, 20)
            time.sleep(1)
            
            logger.info("設置右眼上眼皮位置: 160")
            self.servo_controller.set_position(self.servo_controller.SERVO_RIGHT_LID_UPPER, 160)
            time.sleep(1)
            
            # 測試 7: 手動眨眼測試
            logger.info(f"{Fore.CYAN}[測試 7] 手動眨眼測試")
            logger.info(f"{Fore.CYAN}[Test 7] Manual blink test")
            
            # 手動設置閉眼位置
            logger.info("手動設置閉眼位置")
            self.servo_controller.set_position(self.servo_controller.SERVO_LEFT_LID_LOWER, 0)
            self.servo_controller.set_position(self.servo_controller.SERVO_RIGHT_LID_LOWER, 180)
            self.servo_controller.set_position(self.servo_controller.SERVO_LEFT_LID_UPPER, 180)
            self.servo_controller.set_position(self.servo_controller.SERVO_RIGHT_LID_UPPER, 0)
            time.sleep(2)
            
            # 手動設置開眼位置
            logger.info("手動設置開眼位置")
            self.servo_controller.set_position(self.servo_controller.SERVO_LEFT_LID_LOWER, 160)
            self.servo_controller.set_position(self.servo_controller.SERVO_RIGHT_LID_LOWER, 20)
            self.servo_controller.set_position(self.servo_controller.SERVO_LEFT_LID_UPPER, 20)
            self.servo_controller.set_position(self.servo_controller.SERVO_RIGHT_LID_UPPER, 160)
            time.sleep(2)
            
            # 測試 8: 眼皮緩慢移動測試
            logger.info(f"{Fore.CYAN}[測試 8] 眼皮緩慢移動測試")
            logger.info(f"{Fore.CYAN}[Test 8] Slow eyelid movement test")
            
            # 緩慢閉眼
            logger.info("緩慢閉眼")
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_LID_LOWER, 0, step_size=5, delay=0.05)
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_LID_LOWER, 180, step_size=5, delay=0.05)
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_LID_UPPER, 180, step_size=5, delay=0.05)
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_LID_UPPER, 0, step_size=5, delay=0.05)
            time.sleep(1)
            
            # 緩慢開眼
            logger.info("緩慢開眼")
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_LID_LOWER, 160, step_size=5, delay=0.05)
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_LID_LOWER, 20, step_size=5, delay=0.05)
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_LEFT_LID_UPPER, 20, step_size=5, delay=0.05)
            self.servo_controller.move_servo_smooth(self.servo_controller.SERVO_RIGHT_LID_UPPER, 160, step_size=5, delay=0.05)
            
        except Exception as e:
            logger.error(f"測試過程中發生錯誤: {e}")
            logger.error(f"Error during test: {e}")
        finally:
            # 確保眼皮處於打開狀態
            logger.info("測試結束，確保眼皮處於打開狀態")
            logger.info("Test ended, ensuring eyelids are open")
            self.servo_controller.open_eyelids()

def main():
    """主函數"""
    logger.info("=" * 50)
    logger.info("啟動眨眼皮測試程式")
    logger.info("Starting eyelid blink test program")
    logger.info("=" * 50)
    
    # 創建並啟動測試
    test = EyelidBlinkTest()
    
    try:
        test.start()
        
        logger.info("眨眼皮測試完成")
        logger.info("Eyelid blink test completed")
        
    except KeyboardInterrupt:
        logger.info("使用者中斷，停止測試")
        logger.info("User interrupt, stopping test")
    except Exception as e:
        logger.error(f"發生錯誤: {e}")
        logger.error(f"Error occurred: {e}")
    finally:
        test.stop()
        logger.info("測試程式已結束")
        logger.info("Test program ended")

if __name__ == "__main__":
    main()
