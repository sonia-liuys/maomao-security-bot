#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Arduino Serial Controller
This module manages communication with Arduino over USB serial connection
"""

import serial
import logging
import time
import glob
import sys
import os
import threading

class ArduinoController:
    """Controls an Arduino connected via USB for LED control"""
    
    def __init__(self, baud_rate=115200, timeout=1.0):
        """Initialize Arduino controller
        
        Args:
            baud_rate (int): Serial baud rate
            timeout (float): Serial timeout in seconds
        """
        self.logger = logging.getLogger("ArduinoController")
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial = None
        self.lock = threading.RLock()
        self.connected = False
        self.port = None
    
    def find_arduino_port(self):
        """Find the Arduino's serial port
        
        Returns:
            str: Serial port if found, None otherwise
        """
        self.logger.info("Searching for Arduino...")
        
        # Common patterns for Arduino serial ports on different platforms
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # Linux or Cygwin
            ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
            # 顯示可用的端口
            self.logger.info(f"Available ports on Linux: {ports}")
            # 嘗試列出更多信息
            try:
                import subprocess
                ls_output = subprocess.check_output(['ls', '-l', '/dev/tty*']).decode('utf-8')
                self.logger.info(f"TTY devices: \n{ls_output}")
            except Exception as e:
                self.logger.warning(f"Failed to list TTY devices: {e}")
        elif sys.platform.startswith('darwin'):
            # MacOS
            ports = glob.glob('/dev/tty.usbmodem*') + glob.glob('/dev/tty.usbserial*')
        else:
            self.logger.error(f"Unsupported platform: {sys.platform}")
            return None
        
        if not ports:
            self.logger.warning("No potential Arduino ports found!")
            return None
            
        # Try to connect to each port and check for Arduino response
        for port in ports:
            try:
                self.logger.info(f"Trying to connect to port: {port}")
                ser = serial.Serial(port, self.baud_rate, timeout=5)  # 增加超時時間
                self.logger.info(f"Serial connection established to {port}, waiting for Arduino reset...")
                time.sleep(3)  # Arduino may reset on open - 增加等待時間
                
                # Clear any pending data
                ser.flushInput()
                ser.flushOutput()
                
                # Send status request and wait for response
                self.logger.info(f"Sending STATUS command to {port}")
                ser.write(b"STATUS\n")
                
                # Try multiple times to read response
                for i in range(5):  # 嘗試多次讀取回應
                    response = ser.readline().decode('utf-8', errors='ignore').strip()
                    self.logger.info(f"Response from {port} (attempt {i+1}): '{response}'")
                    
                    if response and ("Arduino" in response or "STATUS" in response):
                        self.logger.info(f"Found Arduino on port {port}")
                        ser.close()
                        return port
                    
                    # If no response, send command again
                    if not response and i < 4:
                        self.logger.info(f"No response, sending STATUS again to {port}")
                        ser.write(b"STATUS\n")
                        time.sleep(0.5)
                
                self.logger.warning(f"No valid response from {port}")
                ser.close()
            except (OSError, serial.SerialException) as e:
                self.logger.warning(f"Failed to open {port}: {str(e)}")
        
        self.logger.warning("Arduino not found after checking all ports")
        return None
    
    def connect(self, port=None):
        """Connect to Arduino
        
        Args:
            port (str, optional): Specific serial port to use. If None, will auto-detect.
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        with self.lock:
            # If already connected, disconnect first
            if self.connected:
                self.logger.info("Already connected to Arduino, disconnecting first")
                self.disconnect()
            
            # Find Arduino port if not specified
            if port is None:
                self.logger.info("No port specified, auto-detecting Arduino port")
                port = self.find_arduino_port()
                if port is None:
                    self.logger.error("Failed to find Arduino port")
                    # 增加診斷信息
                    self.logger.error("Please make sure Arduino is connected and has the correct sketch uploaded")
                    self.logger.error("Try running 'arduino_led_test.py' to diagnose connection issues")
                    return False
            else:
                self.logger.info(f"Using specified port: {port}")
            
            try:
                self.logger.info(f"Attempting to connect to {port} at {self.baud_rate} baud")
                self.serial = serial.Serial(port, self.baud_rate, timeout=self.timeout)
                self.logger.info(f"Serial connection established, waiting for Arduino reset...")
                time.sleep(3)  # Wait longer for Arduino to reset
                
                # Clear any pending data
                self.serial.flushInput()
                self.serial.flushOutput()
                
                # Send multiple status requests to improve connection reliability
                success = False
                for attempt in range(3):  # 嘗試3次
                    self.logger.info(f"Connection attempt {attempt+1}/3")
                    # Check for any pending response first
                    response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    self.logger.info(f"Initial response (may be empty): '{response}'")
                    
                    if response and ("READY" in response or "Arduino" in response):
                        success = True
                        break
                    
                    # Send status request
                    self.logger.info("Sending STATUS command")
                    self.serial.write(b"STATUS\n")
                    
                    # Wait for response with timeout
                    start_time = time.time()
                    while time.time() - start_time < 2:  # 2秒超時
                        if self.serial.in_waiting > 0:
                            response = self.serial.readline().decode('utf-8', errors='ignore').strip()
                            self.logger.info(f"Response: '{response}'")
                            
                            if "Arduino" in response or "STATUS" in response:
                                success = True
                                break
                        time.sleep(0.1)
                    
                    if success:
                        break
                    
                    # If not successful, wait before next attempt
                    if attempt < 2:
                        self.logger.info("Waiting before next attempt...")
                        time.sleep(1)
                
                if success:
                    self.connected = True
                    self.port = port
                    self.logger.info(f"Successfully connected to Arduino on {port}")
                    return True
                else:
                    self.logger.error("Failed to get valid response from Arduino")
                    self.serial.close()
                    self.serial = None
                    return False
                
            except (OSError, serial.SerialException) as e:
                self.logger.error(f"Failed to connect to Arduino: {str(e)}")
                if self.serial:
                    try:
                        self.serial.close()
                    except Exception:
                        pass
                self.serial = None
                return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        with self.lock:
            if self.serial:
                try:
                    self.serial.close()
                except Exception as e:
                    self.logger.error(f"Error closing serial connection: {str(e)}")
                finally:
                    self.serial = None
                    self.connected = False
    
    def is_connected(self):
        """Check if Arduino is connected
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self.connected and self.serial is not None
    
    def set_color(self, r, g, b):
        """Set NeoPixel LEDs to the specified RGB color
        
        Args:
            r (int): Red component (0-255)
            g (int): Green component (0-255)
            b (int): Blue component (0-255)
            
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        with self.lock:
            if not self.is_connected():
                self.logger.error("Cannot set color: Arduino not connected")
                return False
            
            try:
                # Ensure values are within valid range
                r = max(0, min(255, int(r)))
                g = max(0, min(255, int(g)))
                b = max(0, min(255, int(b)))
                
                # Send command to Arduino
                command = f"SET_COLOR {r},{g},{b}\n"
                self.serial.write(command.encode('utf-8'))
                
                # Read response
                response = self.serial.readline().decode('utf-8').strip()
                
                if response.startswith("OK"):
                    self.logger.debug(f"Set color to RGB({r},{g},{b})")
                    return True
                else:
                    self.logger.error(f"Error setting color: {response}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error sending command to Arduino: {str(e)}")
                self.connected = False
                return False
    
    def clear(self):
        """Clear all NeoPixel LEDs (turn off)
        
        Returns:
            bool: True if command sent successfully, False otherwise
        """
        with self.lock:
            if not self.is_connected():
                self.logger.error("Cannot clear LEDs: Arduino not connected")
                return False
            
            try:
                # Send command to Arduino
                self.serial.write(b"CLEAR\n")
                
                # Read response
                response = self.serial.readline().decode('utf-8').strip()
                
                if response == "OK CLEAR":
                    self.logger.debug("Cleared LEDs")
                    return True
                else:
                    self.logger.error(f"Error clearing LEDs: {response}")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Error sending command to Arduino: {str(e)}")
                self.connected = False
                return False


# For testing the module directly
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create controller
    arduino = ArduinoController()
    
    # Connect to Arduino
    if arduino.connect():
        print("Connected to Arduino!")
        
        # Test LED colors
        print("Setting LEDs to red...")
        arduino.set_color(255, 0, 0)
        time.sleep(1)
        
        print("Setting LEDs to green...")
        arduino.set_color(0, 255, 0)
        time.sleep(1)
        
        print("Setting LEDs to blue...")
        arduino.set_color(0, 0, 255)
        time.sleep(1)
        
        print("Clearing LEDs...")
        arduino.clear()
        
        # Disconnect
        arduino.disconnect()
        print("Disconnected from Arduino")
    else:
        print("Failed to connect to Arduino")
