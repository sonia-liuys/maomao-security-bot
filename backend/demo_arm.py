#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
機器人手臂演示程式
專注於讓機器人手臂自由揮動
"""

import os
import sys
import time
import random
import logging
import threading
import pygame
from colorama import Fore, Back, Style, init

# 添加父目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入必要的模組
from backend.core.robot_controller import RobotController
from backend.vision.vision_system import VisionSystem
from backend.servo.servo_controller import ServoController
from backend.utils.config_loader import ConfigLoader

# 初始化 colorama
init(autoreset=True)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ArmDemo")

class RobotArmDemo:
    """機器人手臂演示類，專注於手臂動作"""
    
    def __init__(self):
        """初始化機器人手臂演示"""
        logger.info("初始化機器人手臂演示程式...")
        logger.info("Initializing robot arm demo program...")
        
        # 載入配置
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config()
        logger.info(f"已載入配置: {self.config['robot']['name']}")
        logger.info(f"Loaded configuration: {self.config['robot']['name']}")
        
        # 初始化視覺系統
        vision_config = self.config.get("vision", {}).copy()
        vision_config["skip_model_loading"] = True  # 跳過模型載入
        self.vision_system = VisionSystem(vision_config)
        
        # 初始化機器人控制器
        self.robot_controller = RobotController(self.config)
        
        # 獲取伺服馬達控制器引用
        self.servo_controller = self.robot_controller.servo_controller
        
        # 初始化音效播放器
        pygame.mixer.init()
        self.sound_files = self._load_sound_files()
        logger.info(f"找到 {len(self.sound_files)} 個音效文件")
        logger.info(f"Found {len(self.sound_files)} sound files")
        
        # 控制標誌
        self.running = False
        self.demo_thread = None
        
        # 間隔設定
        self.arm_movement_interval_min = 1.0  # 最小間隔（秒）
        self.arm_movement_interval_max = 3.0  # 最大間隔（秒）
        self.sound_interval = (10, 30)  # 音效播放間隔範圍（秒）
        
        # 上次動作時間
        self.last_arm_movement_time = 0
        self.last_sound_time = 0
        
        logger.info("機器人手臂演示程式初始化完成")
        logger.info("Robot arm demo initialization complete")
    
    def _load_sound_files(self):
        """載入聲音文件"""
        sound_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sound")
        sound_files = []
        
        if os.path.exists(sound_dir):
            for file in os.listdir(sound_dir):
                if file.endswith(".wav"):
                    sound_files.append(os.path.join(sound_dir, file))
        
        return sound_files
    
    def start(self):
        """啟動手臂演示程式"""
        logger.info("啟動機器人手臂演示程式...")
        logger.info("Starting robot arm demo program...")
        
        # 設置初始狀態
        self.servo_controller.set_eye_color("green")
        self.servo_controller.start_led_blinking()
        
        # 啟動主循環
        self.running = True
        self.demo_thread = threading.Thread(target=self._demo_loop)
        self.demo_thread.daemon = True
        self.demo_thread.start()
        
        logger.info("機器人手臂演示程式已啟動")
        logger.info("Robot arm demo started")
    
    def stop(self):
        """停止手臂演示程式"""
        logger.info("停止機器人手臂演示程式...")
        logger.info("Stopping robot arm demo program...")
        
        self.running = False
        
        if self.demo_thread:
            self.demo_thread.join(timeout=1.0)
        
        # 停止 LED 眨眼
        self.servo_controller.stop_led_blinking()
        
        # 停止視覺系統
        self.vision_system.stop()
        
        # 重置機器人位置
        self.servo_controller.reset_all()
        
        logger.info("機器人手臂演示程式已停止")
        logger.info("Robot arm demo stopped")
    
    def _demo_loop(self):
        """主演示循環"""
        logger.info("開始手臂演示循環")
        logger.info("Starting arm demo loop")
        
        try:
            while self.running:
                current_time = time.time()
                
                # 檢查是否應該執行手臂動作
                if current_time - self.last_arm_movement_time > random.uniform(
                    self.arm_movement_interval_min, self.arm_movement_interval_max
                ):
                    self._perform_arm_movement()
                    self.last_arm_movement_time = current_time
                
                # 檢查是否應該播放聲音
                if current_time - self.last_sound_time > random.uniform(
                    self.sound_interval[0], self.sound_interval[1]
                ):
                    self._play_random_sound()
                    self.last_sound_time = current_time
                
                # 短暫休息，減少 CPU 使用率
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"演示循環中發生錯誤: {e}")
            logger.error(f"Error in demo loop: {e}")
        finally:
            logger.info("演示循環結束")
            logger.info("Demo loop ended")
    
    def _perform_arm_movement(self):
        """執行手臂動作"""
        # 隨機選擇一種手臂動作
        action = random.choice([
            'wave',             # 揮手
            'random_movement',  # 隨機移動
            'dance',            # 舞蹈動作
            'exercise'          # 運動動作
        ])
        
        logger.info(f"{Fore.CYAN}[ACTION] 執行手臂動作: {action}")
        logger.info(f"{Fore.CYAN}[ACTION] Performing arm movement: {action}")
        
        if action == 'wave':
            # 揮手動作
            self._wave_arms()
        
        elif action == 'random_movement':
            # 隨機移動手臂
            self._random_arm_movement()
        
        elif action == 'dance':
            # 舞蹈動作
            self._dance_movement()
        
        elif action == 'exercise':
            # 運動動作
            self._exercise_movement()
    
    def _wave_arms(self):
        """揮手動作"""
        logger.info("執行揮手動作")
        logger.info("Performing wave motion")
        
        # 右手揮動
        for _ in range(3):
            # 右手臂上揮
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_RIGHT_ARM,
                30,
                step_size=5,
                delay=0.02
            )
            time.sleep(0.2)
            
            # 右手臂下揮
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_RIGHT_ARM,
                150,
                step_size=5,
                delay=0.02
            )
            time.sleep(0.2)
        
        # 恢復中間位置
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_RIGHT_ARM,
            90,
            step_size=3,
            delay=0.02
        )
        
        # 左手揮動
        for _ in range(3):
            # 左手臂上揮
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_LEFT_ARM,
                30,
                step_size=5,
                delay=0.02
            )
            time.sleep(0.2)
            
            # 左手臂下揮
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_LEFT_ARM,
                150,
                step_size=5,
                delay=0.02
            )
            time.sleep(0.2)
        
        # 恢復中間位置
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_LEFT_ARM,
            90,
            step_size=3,
            delay=0.02
        )
    
    def _random_arm_movement(self):
        """隨機移動手臂"""
        logger.info("執行隨機手臂移動")
        logger.info("Performing random arm movement")
        
        # 右手臂
        right_arm_angle = random.uniform(20, 160)
        logger.info(f"移動右手臂: 角度={right_arm_angle:.1f}度")
        logger.info(f"Moving right arm: Angle={right_arm_angle:.1f}°")
        
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_RIGHT_ARM,
            int(right_arm_angle),
            step_size=3,
            delay=0.02
        )
        
        # 左手臂
        left_arm_angle = random.uniform(20, 160)
        logger.info(f"移動左手臂: 角度={left_arm_angle:.1f}度")
        logger.info(f"Moving left arm: Angle={left_arm_angle:.1f}°")
        
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_LEFT_ARM,
            int(left_arm_angle),
            step_size=3,
            delay=0.02
        )
    
    def _dance_movement(self):
        """舞蹈動作"""
        logger.info("執行舞蹈動作")
        logger.info("Performing dance movement")
        
        # 雙臂舞蹈序列
        dance_sequence = [
            (150, 30),  # 右手上，左手下
            (30, 150),  # 右手下，左手上
            (150, 150), # 雙手上
            (30, 30),   # 雙手下
            (90, 90)    # 回到中間
        ]
        
        for right_angle, left_angle in dance_sequence:
            # 同時移動雙臂
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_RIGHT_ARM,
                right_angle,
                step_size=5,
                delay=0.01
            )
            
            self.servo_controller.move_servo_smooth(
                self.servo_controller.SERVO_LEFT_ARM,
                left_angle,
                step_size=5,
                delay=0.01
            )
            
            time.sleep(0.3)
    
    def _exercise_movement(self):
        """運動動作"""
        logger.info("執行運動動作")
        logger.info("Performing exercise movement")
        
        # 模擬伸展運動
        # 1. 雙臂向前伸展
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_RIGHT_ARM,
            90,
            step_size=3,
            delay=0.02
        )
        
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_LEFT_ARM,
            90,
            step_size=3,
            delay=0.02
        )
        
        time.sleep(0.5)
        
        # 2. 雙臂向上伸展
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_RIGHT_ARM,
            160,
            step_size=3,
            delay=0.02
        )
        
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_LEFT_ARM,
            160,
            step_size=3,
            delay=0.02
        )
        
        time.sleep(0.5)
        
        # 3. 雙臂向下伸展
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_RIGHT_ARM,
            20,
            step_size=3,
            delay=0.02
        )
        
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_LEFT_ARM,
            20,
            step_size=3,
            delay=0.02
        )
        
        time.sleep(0.5)
        
        # 4. 回到中間位置
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_RIGHT_ARM,
            90,
            step_size=3,
            delay=0.02
        )
        
        self.servo_controller.move_servo_smooth(
            self.servo_controller.SERVO_LEFT_ARM,
            90,
            step_size=3,
            delay=0.02
        )
    
    def _play_random_sound(self):
        """播放隨機聲音"""
        if not self.sound_files:
            return
        
        # 隨機選擇一個聲音檔案
        sound_file = random.choice(self.sound_files)
        sound_name = os.path.basename(sound_file)
        
        logger.info(f"{Fore.YELLOW}[SOUND] 播放聲音: {sound_name}")
        logger.info(f"{Fore.YELLOW}[SOUND] Playing sound: {sound_name}")
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        except Exception as e:
            logger.error(f"播放聲音時發生錯誤: {e}")
            logger.error(f"Error playing sound: {e}")

def main():
    """主函數"""
    logger.info("=" * 50)
    logger.info("啟動機器人手臂演示程式")
    logger.info("Starting robot arm demo program")
    logger.info("=" * 50)
    
    # 創建並啟動演示
    demo = RobotArmDemo()
    
    try:
        demo.start()
        
        # 等待使用者按下 Ctrl+C
        logger.info("按下 Ctrl+C 停止演示")
        logger.info("Press Ctrl+C to stop the demo")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("使用者中斷，停止演示")
        logger.info("User interrupt, stopping demo")
    except Exception as e:
        logger.error(f"發生錯誤: {e}")
        logger.error(f"Error occurred: {e}")
    finally:
        demo.stop()
        logger.info("演示程式已結束")
        logger.info("Demo program ended")

if __name__ == "__main__":
    main()
