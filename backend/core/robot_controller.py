#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robot Main Controller - Coordinates the operation of all subsystems
機器人主控制器 - 協調所有子系統的運作
"""

import logging
import threading
from enum import Enum

# Import subsystems
# 導入子系統
from vision.vision_system import VisionSystem
from servo.servo_controller import ServoController
from movement.movement_controller import MovementController
from communication.websocket_server import WebSocketServer
from modes.mode_manager import ModeManager, RobotMode
from safety.watchdog import Watchdog

from utils.sound_manager import SoundManager

class RobotController:
    """Robot Main Controller class, responsible for coordinating all subsystems
    機器人主控制器類，負責協調所有子系統"""
    
    def __init__(self, config):
        """Initialize robot controller
        Args:
            config (dict): Robot configuration
        初始化機器人控制器
        Args:
            config (dict): 機器人配置
        """
        self.sound_manager = SoundManager()
        print("[RobotController] sound_manager initialized")
        self.logger = logging.getLogger("Robot")
        self.config = config
        self.running = False
        
        # Initialize subsystems
        # 初始化子系統
        self.logger.info("Initializing vision system...")
        self.logger.info("初始化視覺系統...")
        self.vision_system = VisionSystem(config["vision"])
        
        self.logger.info("Initializing servo controller...")
        self.logger.info("初始化伺服馬達控制器...")
        self.servo_controller = ServoController(config["servo"])
        
        self.logger.info("Initializing movement controller...")
        self.logger.info("初始化移動控制器...")
        self.movement_controller = MovementController(config["movement"])
        
        self.logger.info("Initializing mode manager...")
        self.logger.info("初始化模式管理器...")
        self.mode_manager = ModeManager(
            self.vision_system,
            self.servo_controller,
            self.movement_controller,
            config["modes"]
        )
        
        self.logger.info("Initializing communication server...")
        self.logger.info("初始化通訊服務器...")
        self.websocket_server = WebSocketServer(
            config["communication"]["websocket_port"],
            self.handle_command,
            self.get_status
        )
        
        self.logger.info("Initializing safety monitoring system...")
        self.logger.info("初始化安全監控系統...")
        self.watchdog = Watchdog(self, config["safety"])
        
        # 將WebSocket服務器實例傳遞給模式管理器
        # Pass WebSocket server instance to mode manager
        self.mode_manager.websocket_server = self.websocket_server
        
        # 將視覺系統實例傳遞給WebSocket服務器
        # Pass vision system instance to WebSocket server
        self.websocket_server.set_vision_system(self.vision_system)
        self.logger.info("將視覺系統實例傳遞給WebSocket服務器")
        self.logger.info("Passed vision system instance to WebSocket server")
        
        self.logger.info("Robot controller initialization complete")
        self.logger.info("機器人控制器初始化完成")
    
    def start(self):
        """Start all robot subsystems
        啟動機器人所有子系統"""
        self.logger.info("Starting robot...")
        self.logger.info("啟動機器人...")

        # 開機音效
        self.sound_manager.play_happy_sound()
        
        # Start each subsystem
        # 啟動各子系統
        self.vision_system.start()
        self.servo_controller.start()
        self.movement_controller.start()
        self.websocket_server.start()
        self.watchdog.start()
        
        # Set initial mode (default is surveillance mode)
        # 設置初始模式 (預設為監視模式)
        self.mode_manager.set_mode(RobotMode.SURVEILLANCE)
        
        self.running = True
        self.logger.info("Robot started")
        self.logger.info("機器人已啟動")
    
    def update(self):
        """Update robot status, called by the main loop
        更新機器人狀態，由主循環調用"""
        if not self.running:
            return
            
        # Update each subsystem
        # 更新各子系統
        vision_data = self.vision_system.get_latest_data()
        self.mode_manager.update(vision_data)
        
        # Update status for sending via WebSocket
        # 更新狀態以便通過WebSocket發送
        status = self.get_status()
        self.websocket_server.broadcast_status(status)
    
    def handle_command(self, command):
        """Handle commands received from the frontend
        
        Args:
            command (dict): Command data
            
        Returns:
            dict: Command processing result
            
        處理從前端接收的命令
        
        Args:
            command (dict): 命令數據
            
        Returns:
            dict: 命令處理結果
        """
        self.logger.info(f"RobotController 收到命令: {command}")
        self.logger.info(f"RobotController received command: {command}")
        
        cmd_type = command.get("type")
        cmd_data = command.get("data", {})
        
        self.logger.info(f"Command type: {cmd_type}")
        self.logger.info(f"Command data: {cmd_data}")
        
        if cmd_type == "set_mode":
            mode_name = cmd_data.get("mode")
            self.logger.info(f"Attempting to set mode to: {mode_name}")
            
            try:
                self.logger.info(f"Converting {mode_name} to RobotMode enum")
                mode = RobotMode[mode_name.upper()]
                self.logger.info(f"Setting mode to: {mode}")
                self.mode_manager.set_mode(mode)
                self.logger.info(f"Successfully switched to {mode_name} mode")
                
                return {"success": True, "message": f"Switched to {mode_name} mode", "message_cht": f"已切換至{mode_name}模式"}
            except (KeyError, ValueError) as e:
                self.logger.error(f"Failed to set mode to {mode_name}: {e}")
                return {"success": False, "message": "Invalid mode", "message_cht": "無效的模式"}
                
        elif cmd_type == "move":
            direction = cmd_data.get("direction")
            continuous = cmd_data.get("continuous", False)
            
            if continuous:
                self.logger.info(f"連續移動指令: {direction}")
                self.logger.info(f"Continuous movement command: {direction}")
                self.movement_controller.start_continuous_movement(direction)
                return {"success": True, "message": f"連續移動指令: {direction}", "message_cht": f"連續移動指令: {direction}"}
            else:
                self.movement_controller.move(direction)
                return {"success": True, "message": f"移動指令: {direction}", "message_cht": f"移動指令: {direction}"}
            
        elif cmd_type == "servo":
            servo_id = cmd_data.get("id")
            position = cmd_data.get("position")
            
            # 處理高級伺服馬達命令
            if servo_id == "arms" and position == "up":
                self.logger.info("舉起手臂命令")
                self.servo_controller.raise_arms()
                return {"success": True, "message": "手臂已舉起", "message_cht": "手臂已舉起"}
            elif servo_id == "arms" and position == "down":
                self.logger.info("放下手臂命令")
                self.servo_controller.lower_arms()
                return {"success": True, "message": "手臂已放下", "message_cht": "手臂已放下"}
            elif servo_id == "eyes" and position == "open":
                self.logger.info("睜開眼睛命令")
                self.servo_controller.open_eyelids()
                return {"success": True, "message": "眼睛已睜開", "message_cht": "眼睛已睜開"}
            elif servo_id == "eyes" and position == "closed":
                self.logger.info("閉上眼睛命令")
                self.servo_controller.close_eyelids()
                return {"success": True, "message": "眼睛已閉上", "message_cht": "眼睛已閉上"}
            else:
                # 直接設置伺服馬達位置
                self.servo_controller.set_position(servo_id, position)
                return {"success": True, "message": f"伺服馬達 {servo_id} 設置為 {position}", "message_cht": f"伺服馬達 {servo_id} 設置為 {position}"}
            
        elif cmd_type == "reset":
            self.reset()
            return {"success": True, "message": "機器人已重置"}
            
        elif cmd_type == "ping":
            # 處理ping命令，返回pong響應
            # Handle ping command, return pong response
            timestamp = cmd_data.get("timestamp", 0)
            return {"success": True, "message": "pong", "timestamp": timestamp}
            
        elif cmd_type == "clear_alarm":
            # 處理解除警報命令
            # Handle clear alarm command
            self.logger.info("收到解除警報命令")
            self.logger.info("Received clear alarm command")
            
            # 調用模式管理器的解除警報方法
            self.mode_manager.clear_alarm()
            
            return {"success": True, "message": "Alarm cleared", "message_cht": "警報已解除"}
        
        elif cmd_type == "patrol":
            # 處理巡邏命令
            # Handle patrol command
            patrol_action = cmd_data.get("action", "")
            self.logger.info(f"收到巡邏命令: {patrol_action}")
            self.logger.info(f"Received patrol command: {patrol_action}")
            
            if patrol_action == "start":
                # 發送開始巡邏命令到移動控制器
                # Send start patrol command to movement controller
                self.movement_controller._send_command("start_patrol")
                return {"success": True, "message": "Started patrol mode", "message_cht": "已開始巡邏模式"}
            elif patrol_action == "stop":
                # 停止所有移動
                # Stop all movements
                self.movement_controller.stop()
                return {"success": True, "message": "Stopped patrol mode", "message_cht": "已停止巡邏模式"}
            else:
                return {"success": False, "message": "Invalid patrol action", "message_cht": "無效的巡邏動作"}
                
        elif cmd_type == "start_video_stream":
            # 處理啟動視頻流命令
            # Handle start video stream command
            self.logger.info("收到啟動視頻流命令")
            self.logger.info("Received start video stream command")
            self.logger.info(f"命令數據: {cmd_data}")
            self.logger.info(f"Command data: {cmd_data}")
            
            try:
                # 調用WebSocket服務器的啟動視頻流方法
                self.logger.info("準備啟動視頻流...")
                self.websocket_server.start_video_streaming()
                self.logger.info("視頻流已啟動")
                
                return {"success": True, "message": "Video streaming started", "message_cht": "視頻流已啟動"}
            except Exception as e:
                self.logger.error(f"啟動視頻流時出錯: {e}")
                self.logger.error(f"Error starting video stream: {e}")
                import traceback
                self.logger.error(f"Error traceback: {traceback.format_exc()}")
                
                return {"success": False, "message": f"Error starting video stream: {e}", "message_cht": f"啟動視頻流時出錯: {e}"}
        
        elif cmd_type == "stop_video_stream":
            # 處理停止視頻流命令
            # Handle stop video stream command
            self.logger.info("收到停止視頻流命令")
            self.logger.info("Received stop video stream command")
            
            # 調用WebSocket服務器的停止視頻流方法
            self.websocket_server.stop_video_streaming()
            
            return {"success": True, "message": "Video streaming stopped", "message_cht": "視頻流已停止"}
        
        elif cmd_type == "start_patrol":
            # 處理開始巡邏命令
            # Handle start patrol command
            self.logger.info("收到開始巡邏命令")
            self.logger.info("Received start patrol command")
            
            # 確保機器人處於巡邏模式
            if self.mode_manager.current_mode != RobotMode.PATROL:
                self.mode_manager.set_mode(RobotMode.PATROL)
            
            # 設置巡邏模式為活動狀態
            self.mode_manager.set_patrol_active(True)
            
            # 使用移動控制器的 start_patrol 方法啟動巡邏
            self.logger.info("正在啟動巡邏模式下的小車移動...")
            self.logger.info("Starting car movement in patrol mode...")
            success = self.movement_controller.start_patrol() if hasattr(self.movement_controller, 'start_patrol') else True
            
            if success:
                self.logger.info("巡邏模式已成功啟動")
                self.logger.info("Patrol mode successfully started")
                
                # 廣播狀態更新
                self.websocket_server.broadcast_status()
                
                return {"success": True, "message": "Patrol started", "message_cht": "巡邏已開始"}
            else:
                self.logger.error("啟動巡邏模式失敗")
                self.logger.error("Failed to start patrol mode")
                return {"success": False, "message": "Failed to start patrol", "message_cht": "無法開始巡邏"}
            
        elif cmd_type == "stop":
            # 處理停止命令
            # Handle stop command
            self.logger.info("收到停止命令")
            self.logger.info("Received stop command")
            
            # 調用移動控制器的停止方法
            self.movement_controller.stop()
            
            return {"success": True, "message": "Movement stopped", "message_cht": "移動已停止"}
            
        elif cmd_type == "stop_patrol":
            # 處理停止巡邏命令
            # Handle stop patrol command
            self.logger.info("收到停止巡邏命令")
            self.logger.info("Received stop patrol command")
            
            # 調用移動控制器的停止方法來停止巡邏
            self.movement_controller.stop()
            
            # 更新巡邏狀態
            self.mode_manager.set_patrol_active(False)
            
            # 廣播狀態更新
            self.websocket_server.broadcast_status()
            
            return {"success": True, "message": "Patrol stopped", "message_cht": "巡邏已停止"}
            
        elif cmd_type == "set_eye_color":
            # 處理設置眼睛顏色命令
            # Handle set eye color command
            color = cmd_data.get("color")
            self.logger.info(f"收到設置眼睛顏色命令: {color}")
            self.logger.info(f"Received set eye color command: {color}")
            
            # 調用伺服馬達控制器的設置眼睛顏色方法
            success = self.servo_controller.set_eye_color(color)
            
            if success:
                return {"success": True, "message": f"Eye color set to {color}", "message_cht": f"眼睛顏色已設置為{color}"}
            else:
                return {"success": False, "message": f"Failed to set eye color to {color}", "message_cht": f"設置眼睛顏色為{color}失敗"}
                
        elif cmd_type == "activate_laser":
            # 處理啟動雷射命令
            # Handle activate laser command
            self.logger.info("收到啟動雷射命令")
            self.logger.info("Received activate laser command")
            
            # 調用伺服馬達控制器的啟動雷射方法
            success = self.servo_controller.activate_laser()
            
            if success:
                return {"success": True, "message": "Laser activated", "message_cht": "雷射已啟動"}
            else:
                return {"success": False, "message": "Failed to activate laser", "message_cht": "啟動雷射失敗"}
                
        elif cmd_type == "deactivate_laser":
            # 處理關閉雷射命令
            # Handle deactivate laser command
            self.logger.info("收到關閉雷射命令")
            self.logger.info("Received deactivate laser command")
            
            # 調用伺服馬達控制器的關閉雷射方法
            success = self.servo_controller.deactivate_laser()
            
            if success:
                return {"success": True, "message": "Laser deactivated", "message_cht": "雷射已關閉"}
            else:
                return {"success": False, "message": "Failed to deactivate laser", "message_cht": "關閉雷射失敗"}
        
        elif cmd_type == "raise_arms":
            # 處理舉起手臂命令
            # Handle raise arms command
            self.logger.info("收到舉起手臂命令")
            self.logger.info("Received raise arms command")
            
            # 調用伺服馬達控制器的舉起手臂方法
            self.servo_controller.raise_arms()
            
            return {"success": True, "message": "Arms raised", "message_cht": "手臂已舉起"}
            
        elif cmd_type == "lower_arms":
            # 處理放下手臂命令
            # Handle lower arms command
            self.logger.info("收到放下手臂命令")
            self.logger.info("Received lower arms command")
            
            # 調用伺服馬達控制器的放下手臂方法
            self.servo_controller.lower_arms()
            
            return {"success": True, "message": "Arms lowered", "message_cht": "手臂已放下"}
            
        elif cmd_type == "open_eyelids":
            # 處理睜開眼睛命令
            # Handle open eyelids command
            self.logger.info("收到睜開眼睛命令")
            self.logger.info("Received open eyelids command")
            
            # 調用伺服馬達控制器的睜開眼睛方法
            self.servo_controller.open_eyelids()
            
            return {"success": True, "message": "Eyelids opened", "message_cht": "眼睛已睜開"}
            
        elif cmd_type == "close_eyelids":
            # 處理閉上眼睛命令
            # Handle close eyelids command
            self.logger.info("收到閉上眼睛命令")
            self.logger.info("Received close eyelids command")
            
            # 調用伺服馬達控制器的閉上眼睛方法
            self.servo_controller.close_eyelids()
            
            return {"success": True, "message": "Eyelids closed", "message_cht": "眼睛已閉上"}
        
        else:
            return {"success": False, "message": "未知命令", "message_cht": "未知命令"}
    
    def get_status(self):
        """獲取機器人當前狀態
        
        Returns:
            dict: 機器人狀態數據
        """
        # 收集各子系統狀態
        vision_status = self.vision_system.get_status()
        servo_status = self.servo_controller.get_status()
        movement_status = self.movement_controller.get_status()
        mode_status = self.mode_manager.get_status()
        
        return {
            "timestamp": self.vision_system.get_timestamp(),
            "mode": mode_status["current_mode"],
            "patrol_active": mode_status.get("patrol_active", False),  # 添加巡邏模式活動狀態
            "vision": {
                "face_detected": vision_status["face_detected"],
                "recognized_person": vision_status["recognized_person"],
                "student_id_detected": vision_status["student_id_detected"],
                "confidence": vision_status["confidence"]
            },
            "servos": servo_status,
            "movement": {
                "current_direction": movement_status["current_direction"],
                "obstacle_detected": movement_status["obstacle_detected"]
            },
            "battery": {
                "level": 85,  # 模擬電池電量
                "charging": False
            },
            "system": {
                "cpu_temp": 45.2,  # 模擬CPU溫度
                "uptime": self.watchdog.get_uptime()
            }
        }
    
    def reset(self):
        """重置機器人到初始狀態"""
        self.logger.info("重置機器人...")
        self.servo_controller.reset_all()
        self.movement_controller.stop()
        self.mode_manager.set_mode(RobotMode.SURVEILLANCE)
    
    def shutdown(self):
        """關閉機器人所有子系統"""
        self.logger.info("關閉機器人...")
        # 關機音效
        self.sound_manager.play_sound("angry")
        self.running = False
        
        # 關閉各子系統
        self.watchdog.stop()
        self.websocket_server.stop()
        self.movement_controller.stop()
        self.servo_controller.stop()
        self.vision_system.stop()
        
        self.logger.info("機器人已關閉")
