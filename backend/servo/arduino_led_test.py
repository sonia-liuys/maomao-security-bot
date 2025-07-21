#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arduino LED控制測試腳本
此腳本用於測試通過Arduino控制LED，不依賴於ServoController或其他Adafruit庫
"""

import os
import sys
import time
import logging
import glob
import serial

# 配置日誌
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ArduinoLEDTest")

class ArduinoLEDTester:
    """簡單的Arduino LED測試類"""
    
    def __init__(self, baud_rate=115200, timeout=1.0):
        """初始化測試器
        
        Args:
            baud_rate (int): 串口波特率
            timeout (float): 串口超時秒數
        """
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial = None
        self.port = None
        self.connected = False
    
    def find_arduino_port(self):
        """搜尋Arduino的串口
        
        Returns:
            str: 如果找到則返回串口名稱，否則返回None
        """
        logger.info("搜尋Arduino...")
        
        # 根據不同平台的常見Arduino串口模式
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # Linux或Cygwin
            ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
        elif sys.platform.startswith('darwin'):
            # MacOS
            ports = glob.glob('/dev/tty.usbmodem*') + glob.glob('/dev/tty.usbserial*')
        else:
            logger.error(f"不支持的平台: {sys.platform}")
            return None
        
        # 嘗試連接每個串口並檢查Arduino回應
        for port in ports:
            try:
                logger.info(f"嘗試連接串口: {port}")
                ser = serial.Serial(port, self.baud_rate, timeout=3)
                time.sleep(3)  # Arduino可能在連接時重置
                
                # 清除任何待處理的數據
                ser.flushInput()
                ser.flushOutput()
                
                # 發送狀態請求並等待回應
                logger.info(f"向 {port} 發送STATUS命令")
                ser.write(b"STATUS\n")
                
                # 讀取回應（最多5行）
                for _ in range(5):
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    logger.info(f"接收到回應: '{response}'")
                    
                    if response and ("Arduino" in response or "STATUS" in response):
                        logger.info(f"在串口 {port} 發現Arduino")
                        ser.close()
                        return port
                    
                    # 如果沒有收到回應，再等待一下
                    if not response:
                        time.sleep(0.5)
                
                ser.close()
                logger.info(f"串口 {port} 無有效回應")
            except (OSError, serial.SerialException) as e:
                logger.info(f"無法打開串口 {port}: {str(e)}")
        
        logger.warning("未找到Arduino")
        return None
    
    def connect(self):
        """連接到Arduino
        
        Returns:
            bool: 如果連接成功返回True，否則返回False
        """
        # 查找Arduino串口
        port = self.find_arduino_port()
        if not port:
            logger.error("找不到Arduino串口")
            return False
        
        try:
            logger.info(f"正在連接到Arduino ({port})...")
            self.serial = serial.Serial(port, self.baud_rate, timeout=self.timeout)
            time.sleep(2)  # 等待Arduino重置
            
            # 清除任何待處理的數據
            self.serial.flushInput()
            self.serial.flushOutput()
            
            # 確認連接
            logger.info("發送STATUS命令確認連接")
            self.serial.write(b"STATUS\n")
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            logger.info(f"接收到回應: '{response}'")
            
            if "Arduino" in response or "STATUS" in response:
                self.connected = True
                self.port = port
                logger.info(f"已成功連接到Arduino ({port})")
                return True
            else:
                logger.error(f"從Arduino收到意外回應: {response}")
                self.serial.close()
                self.serial = None
                return False
        except Exception as e:
            logger.error(f"連接Arduino時出錯: {str(e)}")
            if self.serial:
                self.serial.close()
                self.serial = None
            return False
    
    def disconnect(self):
        """斷開與Arduino的連接"""
        if self.serial:
            try:
                self.serial.close()
                logger.info("已斷開與Arduino的連接")
            except Exception as e:
                logger.error(f"斷開連接時出錯: {str(e)}")
            finally:
                self.serial = None
                self.connected = False
    
    def set_color(self, r, g, b):
        """設置LED顏色
        
        Args:
            r (int): 紅色分量 (0-255)
            g (int): 綠色分量 (0-255)
            b (int): 藍色分量 (0-255)
            
        Returns:
            bool: 如果命令發送成功返回True，否則返回False
        """
        if not self.serial:
            logger.error("無法設置顏色: Arduino未連接")
            return False
        
        try:
            # 確保值在有效範圍內
            r = max(0, min(255, int(r)))
            g = max(0, min(255, int(g)))
            b = max(0, min(255, int(b)))
            
            # 發送命令到Arduino
            command = f"SET_COLOR {r},{g},{b}\n"
            logger.info(f"發送命令: {command.strip()}")
            self.serial.write(command.encode('utf-8'))
            
            # 讀取回應
            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
            logger.info(f"接收到回應: '{response}'")
            
            if response.startswith("OK"):
                logger.info(f"成功設置顏色為RGB({r},{g},{b})")
                return True
            else:
                logger.error(f"設置顏色時出錯: {response}")
                return False
        except Exception as e:
            logger.error(f"發送命令到Arduino時出錯: {str(e)}")
            self.connected = False
            return False

def test_colors():
    """測試不同顏色"""
    tester = ArduinoLEDTester()
    
    if tester.connect():
        try:
            # 測試紅色
            logger.info("測試紅色...")
            tester.set_color(255, 0, 0)
            time.sleep(2)
            
            # 測試綠色
            logger.info("測試綠色...")
            tester.set_color(0, 255, 0)
            time.sleep(2)
            
            # 測試藍色
            logger.info("測試藍色...")
            tester.set_color(0, 0, 255)
            time.sleep(2)
            
            # 測試黃色
            logger.info("測試黃色...")
            tester.set_color(255, 255, 0)
            time.sleep(2)
            
            # 測試白色
            logger.info("測試白色...")
            tester.set_color(255, 255, 255)
            time.sleep(2)
            
            # 關閉
            logger.info("關閉LED...")
            tester.set_color(0, 0, 0)
        finally:
            tester.disconnect()
    else:
        logger.error("無法連接到Arduino，測試失敗")

if __name__ == "__main__":
    print("Arduino LED控制測試")
    print("===================")
    
    # 選項菜單
    while True:
        print("\n請選擇一個選項:")
        print("1. 測試Arduino連接")
        print("2. 測試所有顏色")
        print("3. 設置紅色")
        print("4. 設置綠色")
        print("5. 設置藍色")
        print("6. 關閉LED")
        print("0. 退出")
        
        choice = input("你的選擇 [0-6]: ")
        
        if choice == "0":
            break
        elif choice == "1":
            tester = ArduinoLEDTester()
            if tester.connect():
                print("Arduino連接成功!")
                tester.disconnect()
            else:
                print("Arduino連接失敗!")
        elif choice == "2":
            test_colors()
        elif choice == "3":
            tester = ArduinoLEDTester()
            if tester.connect():
                tester.set_color(255, 0, 0)
                tester.disconnect()
        elif choice == "4":
            tester = ArduinoLEDTester()
            if tester.connect():
                tester.set_color(0, 255, 0)
                tester.disconnect()
        elif choice == "5":
            tester = ArduinoLEDTester()
            if tester.connect():
                tester.set_color(0, 0, 255)
                tester.disconnect()
        elif choice == "6":
            tester = ArduinoLEDTester()
            if tester.connect():
                tester.set_color(0, 0, 0)
                tester.disconnect()
        else:
            print("無效選擇，請重試")
    
    print("程序已退出")
