#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
眼睛左右看測試程式 - 簡單測試機器人眼睛左右轉動
Eye Left-Right Test Program - Simple test for robot's eye left-right movement
"""

import os
import sys
import time
import logging
import random
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
logger = logging.getLogger("EyeDemo")

class RobotEyeDemo:
    """機器人眼睛左右看測試類"""
    
    def __init__(self):
        """初始化眼睛左右看測試"""
        logger.info(f"{Fore.CYAN}初始化眼睛左右看測試程式...")
        logger.info(f"{Fore.CYAN}Initializing eye left-right test program...")
        
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
        
        # 設置眼睛的角度範圍
        self.eye_left =  60# 眼睛左邊角度
        self.eye_right = 120  # 眼睛右邊角度
        self.eye_center = 90  # 眼睛中間位置
        
        # 可用的眼睛顏色
        self.eye_colors = ["green", "red", "yellow", "blue", "white"]
        
        logger.info("眼睛左右看測試程式初始化完成")
        logger.info("Eye left-right test initialization complete")
    
    def start(self):
        """啟動測試"""
        logger.info(f"{Fore.GREEN}啟動眼睛左右看測試...")
        logger.info(f"{Fore.GREEN}Starting eye left-right test...")
        
        # 啟動伺服馬達控制器
        self.servo_controller.start()
        
        # 設置眼睛顏色為藍色作為初始顏色
        self.servo_controller.set_eye_color("blue")
        logger.info("眼睛顏色設為藍色（初始顏色）")
        logger.info("Eye color set to blue (initial color)")
        
        # 確保眼皮打開
        self.servo_controller.open_eyelids()
        logger.info("確保眼皮打開")
        logger.info("Ensuring eyelids are open")
        
        # 執行測試
        self._look_left_right()
        
        logger.info("眼睛左右看測試完成")
        logger.info("Eye left-right test completed")
    
    def stop(self):
        """停止測試"""
        logger.info("停止眼睛左右看測試...")
        logger.info("Stopping eye left-right test...")
        
        # 將眼睛恢復到中間位置
        self._center_eye()
        
        # 停止伺服馬達控制器
        self.servo_controller.stop()
        
        logger.info("眼睛左右看測試已停止")
        logger.info("Eye left-right test stopped")
    
    def _center_eye(self):
        """將眼睛恢復到中間位置"""
        logger.info("將眼睛恢復到中間位置")
        logger.info("Centering eye position")
        
        # 眼睛回到中間
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_EYE,
            self.eye_center,
            step_size=5,
            delay=0.01
        )
    
    def _change_eye_color(self):
        """隨機改變眼睛顏色"""
        # 隨機選擇一個顏色
        new_color = random.choice(self.eye_colors)
        logger.info(f"眼睛顏色改變為 {new_color}")
        logger.info(f"Eye color changed to {new_color}")
        self.servo_controller.set_eye_color(new_color)
    
    def _look_left_right(self):
        """執行眼睛左右看測試"""
        try:
            # 重複測試5次
            for i in range(5):
                logger.info(f"第 {i+1} 次測試")
                logger.info(f"Test {i+1}")
                
                # 隨機改變眼睛顏色
                self._change_eye_color()
                
                # 眼睛向左看
                logger.info("眼睛向左看")
                logger.info("Eye looking left")
                self.servo_controller.move_servo_smooth(
                    self.servo_controller.SERVO_EYE,
                    self.eye_left,
                    step_size=5,
                    delay=0.01
                )
                time.sleep(2)
                
                # 隨機改變眼睛顏色
                self._change_eye_color()
                
                # 眼睛向右看
                logger.info("眼睛向右看")
                logger.info("Eye looking right")
                self.servo_controller.move_servo_smooth(
                    self.servo_controller.SERVO_EYE,
                    self.eye_right,
                    step_size=5,
                    delay=0.01
                )
                time.sleep(2)
                
                # 隨機改變眼睛顏色
                self._change_eye_color()
                
                # 眼睛回到中間
                logger.info("眼睛回到中間")
                logger.info("Eye back to center")
                self.servo_controller.move_servo_smooth(
                    self.servo_controller.SERVO_EYE,
                    self.eye_center,
                    step_size=5,
                    delay=0.01
                )
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"測試過程中發生錯誤: {e}")
            logger.error(f"Error during test: {e}")
        finally:
            # 確保眼睛回到中間位置
            self._center_eye()
    

def main():
    """主函數"""
    logger.info("=" * 50)
    logger.info("啟動眼睛左右看測試程式")
    logger.info("Starting eye left-right test program")
    logger.info("=" * 50)
    
    # 創建並啟動測試
    demo = RobotEyeDemo()
    
    try:
        demo.start()
        
        logger.info("眼睛視野測試完成")
        logger.info("Eye vision test completed")
        
    except KeyboardInterrupt:
        logger.info("使用者中斷，停止測試")
        logger.info("User interrupt, stopping test")
    except Exception as e:
        logger.error(f"發生錯誤: {e}")
        logger.error(f"Error occurred: {e}")
    finally:
        demo.stop()
        logger.info("左右看測試程式已結束")
        logger.info("Left-right test program ended")

if __name__ == "__main__":
    main()
