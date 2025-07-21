#!/usr/bin/env python3
# -*- coding: utf-8 -*-
### AI GENERATED CODE ###

"""
伺服馬達控制器 - 管理機器人的9個伺服馬達
"""

import logging
import threading
import time
import random
import math
import os
import sys
import platform
import importlib.util
import subprocess

# 配置日誌
# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

# 有條件地導入GPIO庫
# Conditionally import GPIO library
GPIO_AVAILABLE = False
if platform.system() == 'Linux' and os.path.exists('/sys/firmware/devicetree/base/model'):
    try:
        import RPi.GPIO as GPIO
        # 嘗試初始化GPIO，測試是否能正確工作
        # Try to initialize GPIO to test if it works correctly
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)  # 使用物理引腳編號
        GPIO_AVAILABLE = True
        logging.info("RPi.GPIO 庫已成功初始化")
        logging.info("RPi.GPIO library successfully initialized")
    except ImportError:
        GPIO_AVAILABLE = False
        logging.warning("RPi.GPIO 庫導入失敗，將使用模擬模式")
        logging.warning("Failed to import RPi.GPIO library, will use simulation mode")
    except Exception as e:
        GPIO_AVAILABLE = False
        logging.warning(f"RPi.GPIO 初始化失敗: {e}，將使用模擬模式")
        logging.warning(f"RPi.GPIO initialization failed: {e}, will use simulation mode")
else:
    GPIO_AVAILABLE = False

# 檢測運行環境
IS_RASPBERRY_PI = platform.system() == 'Linux' and os.path.exists('/sys/firmware/devicetree/base/model')

# LED控制方式選項: 'neopixel', 'arduino', 'gpio'
# LED control methods: 'neopixel', 'arduino', 'gpio'
LED_CONTROL_METHOD = os.environ.get('LED_CONTROL_METHOD', 'arduino')  # 預設使用Arduino

# 伺服控制相關庫導入
USE_ADAFRUIT_SERVO_KIT = False
try:
    # 首先檢查ServoKit是否可用，而不直接導入
    if importlib.util.find_spec('adafruit_servokit') is not None:
        try:
            from adafruit_servokit import ServoKit
            USE_ADAFRUIT_SERVO_KIT = True
            logging.info("成功導入ServoKit庫")
        except Exception as e:
            logging.warning(f"ServoKit導入時發生錯誤: {e}")
            USE_ADAFRUIT_SERVO_KIT = False
    else:
        logging.warning("無法找到ServoKit庫，將使用模擬模式")
except ImportError:
    logging.warning("無法導入ServoKit庫，將使用模擬模式")
    USE_ADAFRUIT_SERVO_KIT = False
except Exception as e:
    logging.warning(f"ServoKit檢查時發生錯誤: {e}")
    USE_ADAFRUIT_SERVO_KIT = False

# NeoPixel相關庫導入
USE_NEOPIXEL = False
try:
    # 首先檢查board和neopixel庫是否可用
    if (importlib.util.find_spec('board') is not None and 
        importlib.util.find_spec('neopixel') is not None):
        try:
            import board
            import neopixel
            USE_NEOPIXEL = LED_CONTROL_METHOD == 'neopixel'
            logging.info("成功導入NeoPixel庫")
        except Exception as e:
            logging.warning(f"NeoPixel導入時發生錯誤: {e}")
            USE_NEOPIXEL = False
    else:
        logging.warning("無法找到board或neopixel庫")
except ImportError:
    logging.warning("無法導入NeoPixel庫")
    USE_NEOPIXEL = False
except Exception as e:
    logging.warning(f"NeoPixel檢查時發生錯誤: {e}")
    USE_NEOPIXEL = False

# 檢查是否使用Arduino控制LED
# Check if using Arduino for LED control
USE_ARDUINO = LED_CONTROL_METHOD == 'arduino'
if USE_ARDUINO:
    try:
        # 確認pyserial庫是否可用
        if importlib.util.find_spec('serial') is not None:
            try:
                import serial
                from .arduino_controller import ArduinoController
                logging.info("成功導入Arduino控制器")
            except ImportError as e:
                logging.warning(f"無法導入Arduino控制器: {e}")
                USE_ARDUINO = False
            except Exception as e:
                logging.warning(f"Arduino控制器導入時發生錯誤: {e}")
                USE_ARDUINO = False
        else:
            logging.warning("無法找到pyserial庫，無法使用Arduino控制")
            USE_ARDUINO = False
    except Exception as e:
        logging.warning(f"檢查pyserial時發生錯誤: {e}")
        USE_ARDUINO = False

# 設置硬件可用性標誌
HARDWARE_AVAILABLE = USE_ADAFRUIT_SERVO_KIT or USE_NEOPIXEL or USE_ARDUINO or GPIO_AVAILABLE
if not HARDWARE_AVAILABLE:
    logging.warning("沒有可用的硬件控制庫，將使用完全模擬模式")
    logging.warning("No hardware control libraries available, using complete simulation mode")
else:
    logging.info(f"硬件支持狀態 - GPIO: {GPIO_AVAILABLE}, ServoKit: {USE_ADAFRUIT_SERVO_KIT}, NeoPixel: {USE_NEOPIXEL}, Arduino: {USE_ARDUINO}")
    logging.info(f"當前LED控制方式: {LED_CONTROL_METHOD}")

# 中心追蹤區域定義
# Central tracking zone definition
CENTER_ZONE_MIN = 0.25  # 中心區域左邊界
CENTER_ZONE_MAX = 0.75  # 中心區域右邊界

class ServoController:
    """伺服馬達控制器類，管理機器人的伺服馬達"""
    
    # 伺服馬達ID常量 (基於參考程式)
    SERVO_EYE = 1             # 眼睛伺服
    SERVO_NECK = 7            # 頸部伺服（水平移動）
    SERVO_LEFT_LID_LOWER  = 3  # 左眼皮下部
    SERVO_RIGHT_LID_LOWER = 4 # 右眼皮下部
    SERVO_LEFT_LID_UPPER  = 5  # 左眼皮上部
    SERVO_RIGHT_LID_UPPER = 6 # 右眼皮上部
    
    SERVO_RIGHT_ARM = 8
    SERVO_LEFT_ARM = 9
    
    # GPIO常量
    LASER_GPIO_PIN = 12      # 激光模塊GPIO引腳

    # 眼睛顏色映射 (根據GRB像素順序調整)
    # Eye color mapping (adjusted for GRB pixel order)
    EYE_COLORS = {
        "green": (0, 255, 0),     # GRB for Green (G=255)
        "red": (255, 0, 0),       # GRB for Red (R=255)
        "yellow": (255, 255, 0),  # GRB for Yellow (R=255, G=255)
        "blue": (0, 0, 255),      # GRB for Blue (B=255)
        "white": (255, 255, 255), # GRB for White (R=255, G=255, B=255)
        "off": (0, 0, 0)          # GRB for Off (all 0)
    }
    
    def __init__(self, config):
        """初始化伺服馬達控制器
        
        Args:
            config (dict): 設定字典
        """
        # 設置日誌
        self.logger = logging.getLogger("ServoController")
        
        # 初始化變數
        self.lock = threading.RLock()
        self.running = False
        self.update_thread = None
        self.servo_positions = {}
        self.eye_color = "green"  # 預設眼睛顏色
        self.natural_blinking = False
        self.led_blinking = False
        self.eyelid_blinking = False
        self.gpio_initialized = False  # GPIO初始化狀態
        
        # 讀取設定
        self.update_interval = config.get("update_interval", 0.05)  # 更新間隔（秒）
        self.blink_interval_min = config.get("blink_interval_min", 2.0)  # 最小眨眼間隔（秒）
        self.blink_interval_max = config.get("blink_interval_max", 6.0)  # 最大眨眼間隔（秒）
        self.led_blink_interval_min = config.get("led_blink_interval_min", 1.0)  # LED最小眨眼間隔（秒）
        self.led_blink_interval_max = config.get("led_blink_interval_max", 3.0)  # LED最大眨眼間隔（秒）
        self.eyelid_blink_interval_min = config.get("eyelid_blink_interval_min", 4.0)  # 眼皮最小眨眼間隔（秒）
        self.eyelid_blink_interval_max = config.get("eyelid_blink_interval_max", 8.0)  # 眼皮最大眨眼間隔（秒）
        
        self.next_led_blink_time = time.time() + random.uniform(self.led_blink_interval_min, self.led_blink_interval_max)
        self.next_eyelid_blink_time = time.time() + random.uniform(self.eyelid_blink_interval_min, self.eyelid_blink_interval_max)
        
        # 處理線程
        self.thread = None
        self.lock = threading.Lock()
        
        # 初始化狀態變數
        self.running = False
        self.servo_positions = {i: 90 for i in range(1, 16)}  # 1-16號伺服，初始位置90度
        self.eye_color = "green"
        self.laser_active = False
        
        # 動作控制標誌
        self.natural_blinking = False
        self.arm_swinging = False
        
        # 眨眼和顏色變化參數
        self.blink_interval_min = config.get("blink_interval_min", 2.0)  # 最小眨眼間隔（秒）
        self.blink_interval_max = config.get("blink_interval_max", 6.0)  # 最大眨眼間隔（秒）
        self.next_blink_time = time.time() + random.uniform(self.blink_interval_min, self.blink_interval_max)
        
        # 處理線程
        self.thread = None
        self.lock = threading.Lock()
        
        # 初始化硬體連接
        self._init_hardware()
        
        self.logger.info("伺服馬達控制器初始化完成")
    
    def _init_hardware(self):
        """初始化硬體連接
        
        根據環境初始化真實硬體或模擬硬體
        """
        with self.lock:
            self.logger.info("初始化硬體連接")
            self.logger.info("Initializing hardware connections")
            
            # 初始化伺服控制器
            if IS_RASPBERRY_PI and USE_ADAFRUIT_SERVO_KIT:
                try:
                    self.logger.info("初始化硬體伺服控制器")
                    self.logger.info("Initializing hardware servo controller")
                    self.kit = ServoKit(channels=16)
                    
                    # 設置初始位置
                    self.reset_all()
                    
                except Exception as e:
                    self.logger.error(f"初始化硬體伺服控制器失敗: {e}")
                    self.logger.error(f"Failed to initialize hardware servo controller: {e}")
                    self.kit = None
            else:
                self.logger.info("使用模擬伺服控制器")
                self.logger.info("Using simulated servo controller")
                self.kit = None

            # 初始化LED控制
            # Initialize LED control
            
            # 1. 嘗試使用Arduino控制NeoPixel
            # Try using Arduino to control NeoPixel
            self.arduino = None
            if IS_RASPBERRY_PI and USE_ARDUINO:
                try:
                    self.logger.info("嘗試初始化Arduino控制器用於LED控制")
                    self.logger.info("Trying to initialize Arduino controller for LED control")
                    self.arduino = ArduinoController()
                    if self.arduino.connect():
                        self.logger.info("Arduino連接成功，使用Arduino控制LED")
                        self.logger.info("Arduino connected successfully, using Arduino for LED control")
                        # 設置初始顏色
                        color = self.EYE_COLORS[self.eye_color]
                        self.arduino.set_color(color[0], color[1], color[2])
                    else:
                        self.logger.warning("Arduino連接失敗，將嘗試其他方法")
                        self.logger.warning("Arduino connection failed, will try other methods")
                        self.arduino = None
                except Exception as e:
                    self.logger.error(f"初始化Arduino控制器失敗: {e}")
                    self.logger.error(f"Failed to initialize Arduino controller: {e}")
                    self.arduino = None
            
            # 2. 嘗試使用NeoPixel直接控制
            # Try using NeoPixel directly
            self.pixels = None
            if IS_RASPBERRY_PI and USE_NEOPIXEL and self.arduino is None:
                try:
                    self.logger.info("初始化NeoPixel LED")
                    self.logger.info("Initializing NeoPixel LEDs")
                    # 使用D18引腳初始化7個RGB LED (眼睛)
                    # Initialize 7 RGB LEDs (eyes) with D18 pin
                    self.pixels = neopixel.NeoPixel(board.D18, 7, brightness=0.5, auto_write=False)
                    self._set_all_pixels(self.EYE_COLORS[self.eye_color])
                except Exception as e:
                    self.logger.error(f"初始化NeoPixel失敗: {e}")
                    self.logger.error(f"Failed to initialize NeoPixel: {e}")
                    self.pixels = None
            
            # 3. 如果上述方法都失敗，則使用GPIO控制RGB LED
            # If above methods fail, use GPIO to control RGB LED
            self.rgb_pins = None
            if IS_RASPBERRY_PI and GPIO_AVAILABLE and self.arduino is None and self.pixels is None:
                try:
                    self.logger.info("使用GPIO控制RGB LED")
                    self.logger.info("Using GPIO to control RGB LED")
                    # 定義RGB LED的GPIO引腳
                    R_PIN = 16  # GPIO引腳用於紅色
                    G_PIN = 20  # GPIO引腳用於綠色
                    B_PIN = 21  # GPIO引腳用於藍色
                    
                    self.rgb_pins = {"R": R_PIN, "G": G_PIN, "B": B_PIN}
                    
                    # 設置GPIO模式
                    GPIO.setup(R_PIN, GPIO.OUT)
                    GPIO.setup(G_PIN, GPIO.OUT)
                    GPIO.setup(B_PIN, GPIO.OUT)
                    
                    # 創建PWM實例
                    self.pwm_r = GPIO.PWM(R_PIN, 100)  # 頻率100Hz
                    self.pwm_g = GPIO.PWM(G_PIN, 100)
                    self.pwm_b = GPIO.PWM(B_PIN, 100)
                    
                    # 啟動PWM
                    self.pwm_r.start(0)  # 占空比0%
                    self.pwm_g.start(0)
                    self.pwm_b.start(0)
                    
                    # 設置初始顏色
                    color = self.EYE_COLORS[self.eye_color]
                    # 轉換0-255至0-100的PWM占空比
                    self.pwm_r.ChangeDutyCycle(color[0] / 2.55)
                    self.pwm_g.ChangeDutyCycle(color[1] / 2.55)
                    self.pwm_b.ChangeDutyCycle(color[2] / 2.55)
                except Exception as e:
                    self.logger.error(f"使用GPIO控制RGB LED失敗: {e}")
                    self.logger.error(f"Failed to use GPIO for RGB LED: {e}")
                    self.rgb_pins = None
            else:
                self.logger.info("使用模擬LED控制")
                self.logger.info("Using simulated LED control")
        
        # 模擬模式初始化
        time.sleep(0.5)
        self.logger.info("模擬伺服馬達初始化完成")
        return False
        
    def _set_all_pixels(self, color):
        """設置所有LED像素為相同顏色
        
        此方法僅用於直接使用NeoPixel控制時。如果使用Arduino或GPIO控制，
        應該直接在set_eye_color中調用相應的方法。
        
        Args:
            color (tuple): RGB顏色值 (r, g, b)
        """
        if self.pixels is not None:
            try:
                for i in range(len(self.pixels)):
                    self.pixels[i] = color
                self.pixels.show()
                return True
            except Exception as e:
                self.logger.error(f"NeoPixel設置像素失敗: {e}")
                self.logger.error(f"Failed to set NeoPixel pixels: {e}")
                return False
        return False
    
    def start(self):
        """啟動伺服馬達控制器"""
        if self.running:
            return
            
        self.logger.info("啟動伺服馬達控制器...")
        self.running = True
        
        # 重置所有伺服馬達到初始位置
        self.reset_all()
        
        # 啟動處理線程
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("伺服馬達控制器已啟動")
    
    def stop(self):
        """停止伺服馬達控制器"""
        if not self.running:
            return
            
        self.logger.info("停止伺服馬達控制器...")
        
        # 停止更新循環
        with self.lock:
            self.running = False
        
        # 等待線程結束
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=2.0)
        
        # 重置所有伺服馬達
        self.reset_all()
        
        # 清理GPIO資源
        if IS_RASPBERRY_PI and GPIO_AVAILABLE and self.gpio_initialized:
            try:
                GPIO.cleanup()
                self.logger.info("GPIO資源已清理")
                self.logger.info("GPIO resources cleaned up")
            except Exception as e:
                self.logger.error(f"GPIO清理失敗: {e}")
                self.logger.error(f"GPIO cleanup failed: {e}")
        
        self.logger.info("伺服馬達控制器已停止")
    
    def _update_loop(self):
        """伺服馬達更新循環"""
        last_arm_swing_time = 0
        last_idle_movement_time = 0
        idle_movement_interval = 5.0  # 閒置動作間隔（秒）
        
        while self.running:
            current_time = time.time()
            
            # 處理自然眨眼
            self._check_for_blink()
            
            # 處理手臂擺動
            if self.arm_swinging and current_time - last_arm_swing_time > random.uniform(3.0, 8.0):
                self._swing_arms()
                last_arm_swing_time = current_time
            
            # 閒置時的自然動作
            if current_time - last_idle_movement_time > idle_movement_interval:
                self._idle_movement()
                last_idle_movement_time = current_time
                idle_movement_interval = random.uniform(5.0, 15.0)  # 隨機閒置間隔
            
            # 控制更新頻率
            time.sleep(0.05)  # 20Hz
    
    def _idle_movement(self):
        """閒置時的自然動作"""
        if not self.running or random.random() > 0.3:  # 30%機率執行
            return
            
        # 隨機選擇一種閒置動作
        action = random.choice(['look_around', 'small_neck_movement'])
        
        if action == 'look_around':
            # 四處張望動作
            positions = [70, 110, 90]  # 左、右、中
            for pos in positions:
                self.move_servo_smooth(self.SERVO_NECK, pos, step_size=2, delay=0.02)
                self.move_servo_smooth(self.SERVO_EYE, pos, step_size=2, delay=0.01)
                time.sleep(random.uniform(0.3, 0.8))
        else:
            # 小幅度頸部移動
            current_pos = self.servo_positions[self.SERVO_NECK]
            new_pos = current_pos + random.uniform(-10, 10)
            new_pos = max(70, min(110, new_pos))  # 限制範圍
            self.move_servo_smooth(self.SERVO_NECK, new_pos, step_size=1, delay=0.02)
    
    def set_position(self, servo_id, position):
        """設置伺服馬達位置
        
        Args:
            servo_id (int): 伺服馬達ID (1-9)
            position (float): 位置角度 (0-180)
        
        Returns:
            bool: 操作是否成功
        """
        if not 1 <= servo_id <= 9:
            self.logger.error(f"無效的伺服馬達ID: {servo_id}")
            return False
            
        position = max(0, min(180, position))  # 限制在0-180範圍內
        
        self.logger.debug(f"設置伺服馬達 {servo_id} 位置為 {position}")
        
        with self.lock:
            self.servo_positions[servo_id] = position
            
        # 實際控制伺服馬達
        self._control_servo(servo_id, position)
        
        return True
    
    def move_servo_smooth(self, servo_id, target_angle, step_size=1, delay=0.02):
        """平滑地移動伺服馬達到目標角度
        
        Args:
            servo_id (int): 伺服馬達ID (1-16)
            target_angle (float): 目標角度 (0-180)
            step_size (int, optional): 每步的角度大小
            delay (float, optional): 每步之間的延遲（秒）
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 確保目標角度在有效範圍內
            target_angle = max(0, min(180, target_angle))
            
            # 檢查伺服馬達ID是否有效
            if servo_id < 0 or servo_id > 15:  # 大多數伺服控制器最多支持16個通道
                self.logger.error(f"無效的伺服馬達ID: {servo_id}，應在0-15範圍內")
                self.logger.error(f"Invalid servo ID: {servo_id}, should be in range 0-15")
                return False
            
            # 獲取當前位置
            with self.lock:
                current_angle = self.servo_positions.get(servo_id, 90)
            
            # 計算步數和方向
            steps = int(abs(target_angle - current_angle) / step_size)
            step_dir = 1 if target_angle > current_angle else -1
            
            # 逐步移動
            for i in range(steps):
                new_angle = current_angle + (i + 1) * step_size * step_dir
                new_angle = max(0, min(180, new_angle))  # 確保在範圍內
                
                # 如果控制失敗，立即返回
                if not self._control_servo(servo_id, new_angle):
                    self.logger.error(f"移動伺服馬達 {servo_id} 到 {new_angle} 度失敗")
                    self.logger.error(f"Failed to move servo {servo_id} to {new_angle} degrees")
                    return False
                
                # 更新保存的位置
                with self.lock:
                    self.servo_positions[servo_id] = new_angle
                
                time.sleep(delay)
            
            # 最後一步，確保到達目標位置
            if not self._control_servo(servo_id, target_angle):
                self.logger.error(f"移動伺服馬達 {servo_id} 到最終位置 {target_angle} 度失敗")
                self.logger.error(f"Failed to move servo {servo_id} to final position {target_angle} degrees")
                return False
            
            # 更新保存的位置
            with self.lock:
                self.servo_positions[servo_id] = target_angle
            
            return True
            
        except Exception as e:
            self.logger.error(f"平滑移動伺服馬達時發生錯誤: {e}")
            self.logger.error(f"Error during smooth servo movement: {e}")
            return False
    
    def _control_servo(self, servo_id, position):
        """實際控制伺服馬達
        
        Args:
            servo_id (int): 伺服馬達ID
            position (float): 位置角度
        """
        if self.kit is not None:
            try:
                # 檢查伺服馬達ID是否在有效範圍內
                if hasattr(self.kit, 'servo') and hasattr(self.kit.servo, '__len__'):
                    servo_count = len(self.kit.servo)
                    if servo_id >= servo_count:
                        self.logger.error(f"無效的伺服馬達ID: {servo_id}，最大ID為: {servo_count-1}")
                        self.logger.error(f"Invalid servo ID: {servo_id}, maximum ID is: {servo_count-1}")
                        return False
                
                # 控制伺服馬達
                self.kit.servo[servo_id].angle = position
                return True
            except IndexError:
                self.logger.error(f"伺服馬達ID超出範圍: {servo_id}")
                self.logger.error(f"Servo ID out of range: {servo_id}")
                return False
            except ValueError as e:
                self.logger.error(f"伺服馬達值錯誤: {e}")
                self.logger.error(f"Servo value error: {e}")
                return False
            except Exception as e:
                self.logger.error(f"控制伺服馬達失敗: {e}")
                self.logger.error(f"Failed to control servo: {e}")
                return False
        # 在模擬模式下，不需要實際控制硬體
        return True
    
    def reset_all(self):
        """重置所有伺服馬達到初始位置"""
        self.logger.info("重置所有伺服馬達")
        
        # 眼睛位置居中
        self.set_position(self.SERVO_EYE, 90)
        
        # 頸部居中
        self.set_position(self.SERVO_NECK, 90)
        
        # 手臂初始位置
        self.set_position(self.SERVO_RIGHT_ARM, 90)
        self.set_position(self.SERVO_LEFT_ARM, 90)
        
        
        # 設置眼睛顏色為綠色
        self.set_eye_color("green")
        
        # 關閉激光
        self.deactivate_laser()
    
    # 儲存上一次的頸部角度，用於平滑過渡
    # Store the last neck angle for smooth transitions
    _last_neck_angle = 90
    _last_eye_angle = 90
    
    def follow_face(self, face_x, face_y):
        """控制眼睛和頸部跟隨人臉
        
        Args:
            face_x (float): 人臉X座標 (0-1)
            face_y (float): 人臉Y座標 (0-1)
        """
        # 計算眼睛目標角度
        # Calculate eye target angle
        target_eye_angle = 60 + (1 - face_x) * 60  # 0->120, 0.5->90, 1->60
        
        # 定義中心跟蹤區域，在這個範圍內只移動眼睛不移動頸部
        # Define the central tracking zone where only eyes move, neck stays still
        CENTER_ZONE_MIN = 0.25  # 中心區域左邊界 (25%)
        CENTER_ZONE_MAX = 0.75  # 中心區域右邊界 (75%)
        
        # 確保眼睛角度在有效範圍內
        # Ensure eye angle is within valid range
        target_eye_angle = max(60, min(120, target_eye_angle))
        
        # 頸部角度處理
        # Handle neck angle
        
        # 如果人臉在中心區域內，保持頸部不動，只使用眼睛追蹤
        # If face is in the central zone, keep the neck still, only use eyes for tracking
        if CENTER_ZONE_MIN <= face_x <= CENTER_ZONE_MAX:
            # 保持頸部的現有位置
            # Maintain current neck position
            if hasattr(ServoController, '_last_neck_angle'):
                target_neck_angle = ServoController._last_neck_angle
            else:
                # 頸部的默認中心位置
                # Default center position for neck if not initialized
                target_neck_angle = 90
        else:
            # 如果人臉超出中心區域，計算頸部目標角度
            # If face is outside the central zone, calculate neck target angle
            target_neck_angle = 60 + (1 - face_x) * 60  # 0->120, 0.5->90, 1->60
            target_neck_angle = max(60, min(120, target_neck_angle))
        
        # 平滑移動參數初始化
        # Initialize smooth movement parameters
        if not hasattr(ServoController, '_last_neck_angle'):
            ServoController._last_neck_angle = 90
        if not hasattr(ServoController, '_last_eye_angle'):
            ServoController._last_eye_angle = 90
            
        # 計算目標與當前位置的差距
        # Calculate the distance between target and current position
        eye_distance = abs(target_eye_angle - ServoController._last_eye_angle)
        neck_distance = abs(target_neck_angle - ServoController._last_neck_angle)
        
        # 調整眼睛追蹤策略，特別是當在中心區域時增強眼睛反應
        # Adjust eye tracking strategy, especially enhance eye responsiveness in central zone
        
        # 如果在中心區域，眼睛要更活躍，因為頸部不參與追蹤
        if CENTER_ZONE_MIN <= face_x <= CENTER_ZONE_MAX:
            # 中心區域的眼睛參數：更高的適應性
            if eye_distance < 5:  # 小角度調整
                damping_factor_eye = 0.3  # 高於非中心區域的參數
            elif eye_distance < 15:  # 中等角度調整
                damping_factor_eye = 0.5  # 更快的反應
            else:  # 大角度調整
                damping_factor_eye = 0.7  # 非常快的眼睛反應
                
            # 中心區域內頸部完全不移動
            damping_factor_neck = 0.0  # 頸部保持不動
        else:
            # 在週邊區域，使用正常的眼睛參數
            if eye_distance < 5:  # 小角度調整
                damping_factor_eye = 0.2
            elif eye_distance < 15:  # 中等角度調整
                damping_factor_eye = 0.4
            else:  # 大角度調整
                damping_factor_eye = 0.6
            
            # 在週邊區域才啟動頸部移動
            # 頸部移動速度要根據人臉偏離中心的程度調整
            # 人臉越遠離中心，頸部移動越快
            edge_distance = 0
            if face_x < CENTER_ZONE_MIN:  # 左邊約束區域
                edge_distance = CENTER_ZONE_MIN - face_x  # 距離左端的距離(0~0.25)
            elif face_x > CENTER_ZONE_MAX:  # 右邊約束區域
                edge_distance = face_x - CENTER_ZONE_MAX  # 距離右端的距離(0~0.25)
            
            # 將偏離情況正規化到 0~1 範圍，作為加速係數
            normalized_edge_factor = min(edge_distance * 4, 1.0)  # 使用 x4 来正規化，因為最大偏移是 0.25
            
            # 偏離越大，頸部移動越快
            base_damping = 0.15  # 頸部基礎隔與係數
            max_extra_damping = 0.35  # 頸部最大額外隔與係數
            
            # 計算加速係數，偏離越大隔與越小（移動越快）
            damping_factor_neck = base_damping + normalized_edge_factor * max_extra_damping
        
        # 計算新的角度
        # Calculate new angles
        new_eye_angle = ServoController._last_eye_angle + (target_eye_angle - ServoController._last_eye_angle) * damping_factor_eye
        new_neck_angle = ServoController._last_neck_angle + (target_neck_angle - ServoController._last_neck_angle) * damping_factor_neck
        
        # 更新記錄的上一次角度
        # Update the stored last angles
        ServoController._last_eye_angle = new_eye_angle
        ServoController._last_neck_angle = new_neck_angle
        
        # 用於中心區域與週邊區域的不同移動策略
        # Different movement strategies for central zone and peripheral zone
        
        # 在中心區域內，加強眼睛反應，頸部不移動
        # Enhanced eye response in central zone, neck stays still
        if CENTER_ZONE_MIN <= face_x <= CENTER_ZONE_MAX:
            # 眼睛參數調整，提高反應速度
            if eye_distance < 5:
                eye_step_size = 2    # 較快的精細移動
                eye_delay = 0.008    # 較快週期時間
            elif eye_distance < 15:
                eye_step_size = 3    # 中快速移動
                eye_delay = 0.006    # 更快週期時間
            else:
                eye_step_size = 4    # 非常快速移動
                eye_delay = 0.004    # 極短週期時間
            
            # 執行眼睛伺服馬達移動
            self.move_servo_smooth(self.SERVO_EYE, new_eye_angle, step_size=eye_step_size, delay=eye_delay)
            
            # 中心區域內頸部完全不移動，直接跳過
            # Neck completely stays still in central zone
            pass
        
        # 在週邊區域，眼睛和頸部同時移動
        # In peripheral zone, both eyes and neck move
        else:
            # 週邊區域的眼睛參數，較慢但也要配合頸部移動
            if eye_distance < 5:
                eye_step_size = 2    # 精細移動
                eye_delay = 0.008    # 適當速度
            else:
                eye_step_size = 3    # 快速移動
                eye_delay = 0.006    # 較高速度
            
            # 週邊區域的頸部參數，根據偏離程度調整
            # 人臉越偏離中心，頸部移動越快
            edge_distance = 0
            if face_x < CENTER_ZONE_MIN:  # 左邊偏離
                edge_distance = CENTER_ZONE_MIN - face_x
            else:  # 右邊偏離
                edge_distance = face_x - CENTER_ZONE_MAX
            
            # 偏離越大，頸部移動越急
            if edge_distance < 0.1:  # 較小偏離
                neck_step_size = 2
                neck_delay = 0.01
            else:  # 較大偏離
                neck_step_size = 3
                neck_delay = 0.005
            
            # 依次執行眼睛和頸部移動
            # Execute eye movement first, then neck movement
            self.move_servo_smooth(self.SERVO_EYE, new_eye_angle, step_size=eye_step_size, delay=eye_delay)
            self.move_servo_smooth(self.SERVO_NECK, new_neck_angle, step_size=neck_step_size, delay=neck_delay)
        
        self.logger.debug(f"跟隨人臉: 位置({face_x:.2f}, {face_y:.2f}) -> 眼睛角度: {new_eye_angle:.1f}, 頸部角度: {new_neck_angle:.1f}")
        self.logger.debug(f"Following face: position({face_x:.2f}, {face_y:.2f}) -> eye angle: {new_eye_angle:.1f}, neck angle: {new_neck_angle:.1f}")
    

    
    def _swing_arms(self):
        """執行手臂擺動動作"""
        # 隨機選擇一個手臂 (左或右)
        arm_side = random.choice(['left', 'right'])
        
        if arm_side == 'right':
            # 右手臂小幅度擺動
            current_upper = self.servo_positions[self.SERVO_RIGHT_ARM]
            current_lower = self.servo_positions[self.SERVO_RIGHT_ARM]
            
            # 計算新位置 (小幅度擺動)
            new_upper = current_upper + random.uniform(-10, 10)
            new_upper = max(120, min(170, new_upper))  # 限制範圍
            
            new_lower = current_lower + random.uniform(-10, 10)
            new_lower = max(10, min(60, new_lower))  # 限制範圍
            
            # 設置新位置
            self.move_servo_smooth(self.SERVO_RIGHT_ARM, new_upper, step_size=2, delay=0.02)
            self.move_servo_smooth(self.SERVO_RIGHT_ARM, new_lower, step_size=2, delay=0.02)
        else:
            # 左手臂小幅度擺動
            current_upper = self.servo_positions[self.SERVO_LEFT_ARM]
            current_lower = self.servo_positions[self.SERVO_LEFT_ARM]
            
            # 計算新位置 (小幅度擺動)
            new_upper = current_upper + random.uniform(-10, 10)
            new_upper = max(10, min(60, new_upper))  # 限制範圍
            
            new_lower = current_lower + random.uniform(-10, 10)
            new_lower = max(120, min(170, new_lower))  # 限制範圍
            
            # 設置新位置
            self.move_servo_smooth(self.SERVO_LEFT_ARM, new_upper, step_size=2, delay=0.02)
            self.move_servo_smooth(self.SERVO_LEFT_ARM, new_lower, step_size=2, delay=0.02)
    
    def start_natural_blinking(self):
        """開始自然眨眼（兼容舊版本）"""
        self.natural_blinking = True
        self.start_led_blinking()
        self.start_eyelid_blinking()
    
    def start_led_blinking(self):
        """開始 LED 眨眼"""
        self.logger.info("開始 LED 眨眼")
        self.led_blinking = True
        # 重設下次 LED 眨眼時間
        self.next_led_blink_time = time.time() + random.uniform(self.led_blink_interval_min, self.led_blink_interval_max)
    
    def start_eyelid_blinking(self):
        """開始眼皮眨眼"""
        self.logger.info("開始眼皮眨眼")
        self.eyelid_blinking = True
        # 重設下次眼皮眨眼時間
        self.next_eyelid_blink_time = time.time() + random.uniform(self.eyelid_blink_interval_min, self.eyelid_blink_interval_max)
    
    def stop_natural_blinking(self):
        """停止自然眨眼（兼容舊版本）"""
        self.natural_blinking = False
        self.stop_led_blinking()
        self.stop_eyelid_blinking()
    
    def stop_led_blinking(self):
        """停止 LED 眨眼"""
        self.logger.info("停止 LED 眨眼")
        self.led_blinking = False
    
    def stop_eyelid_blinking(self):
        """停止眼皮眨眼"""
        self.logger.info("停止眼皮眨眼")
        self.eyelid_blinking = False
    
    def close_eyelids(self):
        """閉上眼皮"""
        self.logger.info("閉上眼皮")
        if IS_RASPBERRY_PI and HARDWARE_AVAILABLE and self.kit:
            try:
                self.kit.servo[self.SERVO_LEFT_LID_LOWER].angle = 0
                self.kit.servo[self.SERVO_RIGHT_LID_LOWER].angle = 180
                self.kit.servo[self.SERVO_LEFT_LID_UPPER].angle = 180
                self.kit.servo[self.SERVO_RIGHT_LID_UPPER].angle = 0
                
                # 更新伺服馬達位置記錄
                self.servo_positions[self.SERVO_LEFT_LID_LOWER] = 0
                self.servo_positions[self.SERVO_RIGHT_LID_LOWER] = 180
                self.servo_positions[self.SERVO_LEFT_LID_UPPER] = 180
                self.servo_positions[self.SERVO_RIGHT_LID_UPPER] = 0
                return True
            except Exception as e:
                self.logger.error(f"閉上眼皮時發生錯誤: {e}")
                return False
        else:
            # 模擬模式
            self.servo_positions[self.SERVO_LEFT_LID_LOWER] = 0
            self.servo_positions[self.SERVO_RIGHT_LID_LOWER] = 180
            self.servo_positions[self.SERVO_LEFT_LID_UPPER] = 180
            self.servo_positions[self.SERVO_RIGHT_LID_UPPER] = 0
            return True
    
    def open_eyelids(self):
        """打開眼皮"""
        self.logger.info("打開眼皮")
        if IS_RASPBERRY_PI and HARDWARE_AVAILABLE and self.kit:
            try:
                self.kit.servo[self.SERVO_LEFT_LID_LOWER].angle = 160
                self.kit.servo[self.SERVO_RIGHT_LID_LOWER].angle = 20
                self.kit.servo[self.SERVO_LEFT_LID_UPPER].angle = 20
                self.kit.servo[self.SERVO_RIGHT_LID_UPPER].angle = 160
                
                # 更新伺服馬達位置記錄
                self.servo_positions[self.SERVO_LEFT_LID_LOWER] = 160
                self.servo_positions[self.SERVO_RIGHT_LID_LOWER] = 20
                self.servo_positions[self.SERVO_LEFT_LID_UPPER] = 20
                self.servo_positions[self.SERVO_RIGHT_LID_UPPER] = 160
                return True
            except Exception as e:
                self.logger.error(f"打開眼皮時發生錯誤: {e}")
                return False
        else:
            # 模擬模式
            self.servo_positions[self.SERVO_LEFT_LID_LOWER] = 160
            self.servo_positions[self.SERVO_RIGHT_LID_LOWER] = 20
            self.servo_positions[self.SERVO_LEFT_LID_UPPER] = 20
            self.servo_positions[self.SERVO_RIGHT_LID_UPPER] = 160
            return True
    
    def start_arm_swinging(self):
        """開始手臂擺動"""
        self.arm_swinging = True
    
    def stop_arm_swinging(self):
        """停止手臂擺動"""
        self.arm_swinging = False
    
    def set_eye_color(self, color):
        """設置眼睛顏色
        
        Args:
            color (str): 顏色名稱，可以是 "green", "red", "yellow", "blue", "white", "off"
            
        Returns:
            bool: 操作是否成功
        """
        with self.lock:
            self.logger.info(f"設置眼睛顏色為: {color}")
            self.logger.info(f"Setting eye color to: {color}")
            
            # 驗證顏色
            if color not in self.EYE_COLORS:
                self.logger.error(f"不支持的眼睛顏色: {color}")
                self.logger.error(f"Unsupported eye color: {color}")
                return False
            
            # 存儲當前顏色
            self.eye_color = color
            rgb_color = self.EYE_COLORS[color]
            
            # 根據可用的控制方法設置LED顏色
            # Set LED color based on available control method
            
            # 1. 優先使用Arduino控制 (如果可用)
            # Use Arduino control if available
            if self.arduino is not None:
                try:
                    self.logger.debug(f"通過Arduino設置LED顏色: {rgb_color}")
                    success = self.arduino.set_color(rgb_color[0], rgb_color[1], rgb_color[2])
                    if success:
                        return True
                    else:
                        self.logger.error("通過Arduino設置顏色失敗，將嘗試其他方法")
                except Exception as e:
                    self.logger.error(f"Arduino設置眼睛顏色失敗: {e}")
                    self.logger.error(f"Failed to set eye color via Arduino: {e}")
                    # Arduino可能已斷開，重置為None以便下次重新連接
                    self.arduino = None
            
            # 2. 如果Arduino不可用，嘗試使用NeoPixel
            # If Arduino unavailable, try using NeoPixel
            if self.pixels is not None:
                try:
                    self.logger.debug(f"通過NeoPixel設置LED顏色: {rgb_color}")
                    self._set_all_pixels(rgb_color)
                    return True
                except Exception as e:
                    self.logger.error(f"NeoPixel設置眼睛顏色失敗: {e}")
                    self.logger.error(f"Failed to set eye color via NeoPixel: {e}")
                    # NeoPixel可能出錯，重置以便未來再次嘗試
                    self.pixels = None
            
            # 3. 如果前兩種方法都不可用，嘗試使用GPIO PWM控制RGB LED
            # If first two methods unavailable, try using GPIO PWM for RGB LED
            if self.rgb_pins is not None:
                try:
                    self.logger.debug(f"通過GPIO PWM設置RGB LED顏色: {rgb_color}")
                    # 將RGB值(0-255)轉換為PWM值(0-100)
                    r_pwm = rgb_color[0] / 2.55
                    g_pwm = rgb_color[1] / 2.55
                    b_pwm = rgb_color[2] / 2.55
                    
                    # 設置PWM值
                    self.pwm_r.ChangeDutyCycle(r_pwm)
                    self.pwm_g.ChangeDutyCycle(g_pwm)
                    self.pwm_b.ChangeDutyCycle(b_pwm)
                    return True
                except Exception as e:
                    self.logger.error(f"GPIO PWM設置RGB LED顏色失敗: {e}")
                    self.logger.error(f"Failed to set eye color via GPIO PWM: {e}")
                    self.rgb_pins = None
            
            # 4. 如果所有方法都失敗，只記錄顏色變化（模擬模式）
            # If all methods fail, just log the color change (simulation mode)
            self.logger.info(f"模擬模式：眼睛顏色已設為 {color}")
            self.logger.info(f"Simulation mode: eye color set to {color}")
            return True
    
    def _check_for_blink(self):
        """檢查是否應該眨眼"""
        current_time = time.time()
        
        # 檢查LED眨眼
        if current_time > self.next_led_blink_time and self.led_blinking:
            self.logger.debug("LED眨眼")
            self._blink_leds()
            self.next_led_blink_time = current_time + random.uniform(self.led_blink_interval_min, self.led_blink_interval_max)
        
        # 檢查眼皮眨眼
        if current_time > self.next_eyelid_blink_time and self.eyelid_blinking:
            self.logger.debug("眼皮眨眼")
            self._blink_eyelids()
            self.next_eyelid_blink_time = current_time + random.uniform(self.eyelid_blink_interval_min, self.eyelid_blink_interval_max)
        if current_time > self.next_blink_time and self.natural_blinking:
            self.logger.debug("自然眨眼")
            self._blink()
            self.next_blink_time = current_time + random.uniform(self.blink_interval_min, self.blink_interval_max)
    
    def _blink(self):
        """執行綜合眨眼動作（兼容舊版本）"""
        # 同時執行 LED 和眼皮眨眼
        self._blink_leds()
        self._blink_eyelids()
    
    def _blink_leds(self):
        """執行 LED 眨眼動作"""
        # 保存當前顏色
        with self.lock:
            saved_color = self.eye_color
        
        # 關閉LED（眨眼）
        self.set_eye_color("off")
        time.sleep(0.1)  # 眼睛關閉時間
        
        # 恢復原來顏色
        self.set_eye_color(saved_color)
    
    def _blink_eyelids(self):
        """執行眼皮眨眼動作"""
        # 關閉眼皮
        self.close_eyelids()
        
        # 短暫停頓
        time.sleep(1)
        
        # 打開眼皮
        self.open_eyelids()
    
    def raise_right_arm(self):
        """舉起右手臂"""
        self.move_servo_smooth(self.SERVO_RIGHT_ARM, 180, step_size=2, delay=0.02)
      
    def raise_arms(self):
        """舉起雙手"""
        # 右手臂
        self.move_servo_smooth(self.SERVO_RIGHT_ARM, 180, step_size=2, delay=0.02)
        
        # 左手臂
        self.move_servo_smooth(self.SERVO_LEFT_ARM, 0, step_size=2, delay=0.02)
    
    def lower_arms(self):
        """放下雙手"""
        # 右手臂
        self.move_servo_smooth(self.SERVO_RIGHT_ARM, 90, step_size=2, delay=0.02)
        
        # 左手臂
        self.move_servo_smooth(self.SERVO_LEFT_ARM, 90, step_size=2, delay=0.02)
    
    def activate_laser(self):
        """啟動激光指示器
        
        使用GPIO第12腳控制激光模塊
        Activate the laser module using GPIO pin 12
        """
        self.logger.info("啟動激光指示器")
        self.logger.info("Activating laser module")
        self.laser_active = True
        
        # 嘗試使用pinctrl命令（適用於Pi 5）
        try:
            self.logger.info("嘗試使用pinctrl命令啟動激光器 (Pi 5)")
            import subprocess
            
            # 設置 GPIO 12 為輸出模式
            subprocess.call(["sudo", "pinctrl", "set", "12", "op"])
            # 設置為高電平
            subprocess.call(["sudo", "pinctrl", "set", "12", "dh"])
            
            self.logger.info("激光模塊已啟動 (pinctrl GPIO 12)")
            self.logger.info("Laser module activated (pinctrl GPIO 12)")
            return True
        except Exception as e:
            self.logger.error(f"pinctrl方式啟動激光模塊失敗: {e}")
            self.logger.error(f"Failed to activate laser module using pinctrl: {e}")
        
        # 嘗試直接使用gpiod（新的GPIO控制方法）
        try:
            self.logger.info("嘗試使用gpiod命令啟動激光器")
            import subprocess
            
            # 設置 GPIO 12 為高電平
            subprocess.call(["sudo", "gpioset", "gpiochip0", "12=1"])
            
            self.logger.info("激光模塊已啟動 (gpiod GPIO 12)")
            self.logger.info("Laser module activated (gpiod GPIO 12)")
            return True
        except Exception as e:
            self.logger.error(f"gpiod方式啟動激光模塊失敗: {e}")
            self.logger.error(f"Failed to activate laser module using gpiod: {e}")
        
        # 嘗試直接使用sysfs控制GPIO
        try:
            # 使用BCM編號，對應GPIO 12
            GPIO_PIN = self.LASER_GPIO_PIN
            self.logger.info(f"嘗試使用sysfs控制GPIO {GPIO_PIN}")
            
            # 嘗試使用sudo寫入檔案
            subprocess.call(["sudo", "sh", "-c", f"echo {GPIO_PIN} > /sys/class/gpio/export"])
            subprocess.call(["sudo", "sh", "-c", f"echo out > /sys/class/gpio/gpio{GPIO_PIN}/direction"])
            subprocess.call(["sudo", "sh", "-c", f"echo 1 > /sys/class/gpio/gpio{GPIO_PIN}/value"])
            
            self.logger.info(f"激光模塊已啟動 (sysfs GPIO {GPIO_PIN})")
            self.logger.info(f"Laser module activated (sysfs GPIO {GPIO_PIN})")
            return True
        except Exception as e:
            self.logger.error(f"sysfs方式啟動激光模塊失敗: {e}")
            self.logger.error(f"Failed to activate laser module using sysfs: {e}")
        
        # 如果所有方法都失敗，嘗試直接使用Python執行命令
        try:
            self.logger.info("嘗試使用Python執行命令方式啟動激光器...")
            # 嘗試使用gpio命令
            subprocess.call(["sudo", "gpio", "-g", "mode", "12", "out"])
            subprocess.call(["sudo", "gpio", "-g", "write", "12", "1"])
            self.logger.info("已嘗試使用gpio命令啟動激光器")
            return True
        except Exception as e2:
            self.logger.error(f"所有方法都失敗: {e2}")
            self.logger.error(f"All methods failed: {e2}")
            
        self.logger.info("模擬模式: 激光模塊已啟動")
        self.logger.info("Simulation mode: Laser module activated")
        return False
    
    def deactivate_laser(self):
        """關閉激光指示器
        
        關閉GPIO第12腳上的激光模塊
        Deactivate the laser module using GPIO pin 12
        """
        self.logger.info("關閉激光指示器")
        self.logger.info("Deactivating laser module")
        self.laser_active = False
        
        # 嘗試使用pinctrl命令（適用於Pi 5）
        try:
            self.logger.info("嘗試使用pinctrl命令關閉激光器 (Pi 5)")
            import subprocess
            
            # 設置 GPIO 12 為輸出模式
            subprocess.call(["sudo", "pinctrl", "set", "12", "op"])
            # 設置為低電平
            subprocess.call(["sudo", "pinctrl", "set", "12", "dl"])
            
            self.logger.info("激光模塊已關閉 (pinctrl GPIO 12)")
            self.logger.info("Laser module deactivated (pinctrl GPIO 12)")
            return True
        except Exception as e:
            self.logger.error(f"pinctrl方式關閉激光模塊失敗: {e}")
            self.logger.error(f"Failed to deactivate laser module using pinctrl: {e}")
        
        # 嘗試直接使用gpiod（新的GPIO控制方法）
        try:
            self.logger.info("嘗試使用gpiod命令關閉激光器")
            import subprocess
            
            # 設置 GPIO 12 為低電平
            subprocess.call(["sudo", "gpioset", "gpiochip0", "12=0"])
            
            self.logger.info("激光模塊已關閉 (gpiod GPIO 12)")
            self.logger.info("Laser module deactivated (gpiod GPIO 12)")
            return True
        except Exception as e:
            self.logger.error(f"gpiod方式關閉激光模塊失敗: {e}")
            self.logger.error(f"Failed to deactivate laser module using gpiod: {e}")
        
        # 嘗試直接使用sysfs控制GPIO
        try:
            # 使用BCM編號，對應GPIO 12
            GPIO_PIN = self.LASER_GPIO_PIN
            self.logger.info(f"嘗試使用sysfs關閉GPIO {GPIO_PIN}")
            
            # 嘗試使用sudo寫入檔案
            subprocess.call(["sudo", "sh", "-c", f"echo {GPIO_PIN} > /sys/class/gpio/export"])
            subprocess.call(["sudo", "sh", "-c", f"echo out > /sys/class/gpio/gpio{GPIO_PIN}/direction"])
            subprocess.call(["sudo", "sh", "-c", f"echo 0 > /sys/class/gpio/gpio{GPIO_PIN}/value"])
            
            self.logger.info(f"激光模塊已關閉 (sysfs GPIO {GPIO_PIN})")
            self.logger.info(f"Laser module deactivated (sysfs GPIO {GPIO_PIN})")
            return True
        except Exception as e:
            self.logger.error(f"sysfs方式關閉激光模塊失敗: {e}")
            self.logger.error(f"Failed to deactivate laser module using sysfs: {e}")
        
        # 如果所有方法都失敗，嘗試直接使用Python執行命令
        try:
            self.logger.info("嘗試使用Python執行命令方式關閉激光器...")
            # 嘗試使用gpio命令
            subprocess.call(["sudo", "gpio", "-g", "write", "12", "0"])
            self.logger.info("已嘗試使用gpio命令關閉激光器")
            return True
        except Exception as e2:
            self.logger.error(f"所有方法都失敗: {e2}")
            self.logger.error(f"All methods failed: {e2}")
            
        self.logger.info("模擬模式: 激光模塊已關閉")
        self.logger.info("Simulation mode: Laser module deactivated")
        return False
    
    def toggle_laser(self):
        """切換激光指示器狀態
        
        如果激光器關閉，則開啟它；如果已開啟，則關閉它
        
        Returns:
            bool: 新的激光器狀態，True 表示已開啟，False 表示已關閉
        """
        self.logger.info(f"切換激光指示器狀態，當前狀態: {self.laser_active}")
        self.logger.info(f"Toggling laser state, current state: {self.laser_active}")
        
        if self.laser_active:
            self.deactivate_laser()
        else:
            self.activate_laser()
            
        return self.laser_active
    
    def laser_demo(self, duration=5, blink_count=3):
        """激光指示器演示
        
        執行一個簡單的激光指示器演示，包括開啟、閃爍和關閉
        
        Args:
            duration (int): 演示持續時間（秒）
            blink_count (int): 閃爍次數
        """
        self.logger.info(f"開始激光指示器演示，持續{duration}秒，閃爍{blink_count}次")
        self.logger.info(f"Starting laser demo for {duration} seconds with {blink_count} blinks")
        
        # 確保激光器開始時是關閉的
        if self.laser_active:
            self.deactivate_laser()
            time.sleep(0.5)
        
        # 開啟激光器
        self.activate_laser()
        time.sleep(1)
        
        # 閃爍激光器
        blink_interval = (duration - 2) / (blink_count * 2)  # 計算閃爍間隔
        for i in range(blink_count):
            self.deactivate_laser()
            time.sleep(blink_interval)
            self.activate_laser()
            time.sleep(blink_interval)
            self.logger.info(f"閃爍 {i+1}/{blink_count}")
        
        # 最後關閉激光器
        time.sleep(1)
        self.deactivate_laser()
        self.logger.info("激光指示器演示完成")
        self.logger.info("Laser demo completed")
    
    def get_status(self):
        """獲取伺服馬達狀態
        
        Returns:
            dict: 伺服馬達狀態
        """
        with self.lock:
            return {
                "positions": self.servo_positions.copy(),
                "eye_color": self.eye_color,
                "laser_active": self.laser_active,
                "natural_blinking": self.natural_blinking,
                "arm_swinging": self.arm_swinging
            }
