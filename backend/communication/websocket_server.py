#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WebSocket服務器 - 處理與前端的通訊
WebSocket Server - Handle communication with frontend
"""

import logging
import threading
import json
import asyncio
import websockets
import time
import base64
import cv2
import inspect
from datetime import datetime

class WebSocketServer:
    """WebSocket服務器類，處理與前端的通訊
    WebSocket server class, handles communication with frontend"""
    
    def __init__(self, port, command_handler, status_provider):
        """初始化WebSocket服務器
        Initialize WebSocket server
        
        Args:
            port (int): 服務器端口 (Server port)
            command_handler (callable): 處理命令的回調函數 (Command handler callback)
            status_provider (callable): 提供狀態的回調函數 (Status provider callback)
        """
        self.logger = logging.getLogger("WebSocket")
        self.port = port
        self.command_handler = command_handler
        self.status_provider = status_provider
        
        self.clients = set()
        self.video_clients = set()  # 專門接收視頻流的客戶端集合 (Clients receiving video stream)
        self.running = False
        self.server = None
        self.thread = None
        self.video_thread = None  # 視頻流線程 (Video streaming thread)
        self.lock = threading.Lock()
        self.video_streaming = False  # 視頻流狀態 (Video streaming status)
        self.video_interval = 0.1  # 視頻幀發送間隔，秒 (Video frame sending interval in seconds)
        self.vision_system = None  # 視覺系統實例 (Vision system instance)
        
        self.logger.info(f"WebSocket服務器初始化完成 (端口: {port})")
        self.logger.info(f"WebSocket server initialization complete (port: {port})")
        
    def set_vision_system(self, vision_system):
        """設置視覺系統實例
        Set vision system instance
        
        Args:
            vision_system: 視覺系統實例 (Vision system instance)
        """
        self.vision_system = vision_system
        self.logger.info("設置視覺系統實例成功")
        self.logger.info("Successfully set vision system instance")
        
    def _is_connection_closed(self, websocket):
        """安全地檢查WebSocket連接是否已關閉
        Safely check if a WebSocket connection is closed
        
        Args:
            websocket: WebSocket連接對象 (WebSocket connection object)
            
        Returns:
            bool: 如果連接已關閉或無效，返回 True (True if connection is closed or invalid)
        """
        try:
            # 嘗試創建一個 ping 任務，但不實際執行
            # 如果連接已關閉，這會失敗
            pong_waiter = asyncio.ensure_future(websocket.ping())
            # 立即取消任務，我們只是檢查是否能創建任務
            pong_waiter.cancel()
            return False  # 連接正常
        except Exception:
            return True  # 連接已關閉或無效
    
    def start(self):
        """啟動WebSocket服務器
        Start WebSocket server"""
        if self.running:
            return
            
        self.logger.info("啟動WebSocket服務器...")
        self.logger.info("Starting WebSocket server...")
        self.running = True
        
        # 啟動服務器線程
        # Start server thread
        self.thread = threading.Thread(target=self._run_server)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("WebSocket服務器已啟動")
        self.logger.info("WebSocket server started")
    
    def stop(self):
        """停止WebSocket服務器
        Stop WebSocket server"""
        if not self.running:
            return
            
        self.logger.info("停止WebSocket服務器...")
        self.logger.info("Stopping WebSocket server...")
        self.running = False
        
        # 停止視頻流
        # Stop video streaming
        if hasattr(self, 'stop_video_streaming'):
            self.stop_video_streaming()
        
        # 停止事件循環
        # Stop event loop
        try:
            if self.server:
                # 使用新的事件循環來停止服務器
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._stop_server())
                loop.close()
        except Exception as e:
            self.logger.error(f"停止服務器時出錯: {e}")
            self.logger.error(f"Error stopping server: {e}")
        
        # 等待線程結束
        # Wait for thread to end
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=2.0)
            except Exception as e:
                self.logger.error(f"等待線程結束時出錯: {e}")
                self.logger.error(f"Error waiting for thread to end: {e}")
        
        self.logger.info("WebSocket服務器已停止")
        self.logger.info("WebSocket server stopped")
    
    def _run_server(self):
        """運行WebSocket服務器的主循環
        Run the main loop of the WebSocket server"""
        self.logger.info(f"啟動WebSocket服務器在端口 {self.port}")
        self.logger.info(f"Starting WebSocket server on port {self.port}")
        
        # 創建新的事件循環
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 定義啟動服務器的異步函數
        # Define async function to start server
        async def start_server_async():
            try:
                # 嘗試在指定端口啟動服務器
                # Try to start server on specified port
                return await websockets.serve(self._handle_client, "0.0.0.0", self.port)
            except OSError as e:
                # 端口可能被佔用，記錄錯誤並嘗試使用備用端口
                # Port might be in use, log error and try fallback port
                self.logger.error(f"無法在端口 {self.port} 啟動WebSocket服務器: {e}")
                self.logger.error(f"Failed to start WebSocket server on port {self.port}: {e}")
                
                # 嘗試使用備用端口 (原端口+1)
                # Try fallback port (original port + 1)
                fallback_port = self.port + 1
                self.logger.info(f"嘗試使用備用端口 {fallback_port}")
                self.logger.info(f"Trying fallback port {fallback_port}")
                self.port = fallback_port  # 更新端口號
                return await websockets.serve(self._handle_client, "0.0.0.0", fallback_port)
        
        try:
            # 啟動服務器
            # Start server
            self.server = loop.run_until_complete(start_server_async())
            self.logger.info(f"WebSocket服務器已啟動在端口 {self.port}，等待連接...")
            self.logger.info(f"WebSocket server started on port {self.port}, waiting for connections...")
            
            # 運行事件循環
            # Run event loop
            loop.run_forever()
        except Exception as e:
            self.logger.error(f"啟動WebSocket服務器時發生錯誤: {e}")
            self.logger.error(f"Error occurred while starting WebSocket server: {e}")
            # 設置運行標誌為False
            self.running = False
    
    def _stop_server(self):
        """停止WebSocket服務器"""
        if self.server:
            self.server.close()
            return asyncio.ensure_future(self.server.wait_closed())
    
    async def _handle_client(self, websocket, path=None):
        """處理客戶端連接
        
        Args:
            websocket: WebSocket連接
        """
        # 添加到客戶端集合
        # Add to client set
        with self.lock:
            self.clients.add(websocket)
        
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.logger.info(f"新客戶端連接: {client_info}")
        self.logger.info(f"New client connected: {client_info}")
        
        try:
            # 發送初始狀態
            # Send initial status
            await self._send_status(websocket)
            
            # 處理客戶端消息
            # Handle client messages
            async for message in websocket:
                try:
                    # 記錄原始消息
                    # Log raw message
                    self.logger.info(f"收到原始消息: {message}")
                    self.logger.info(f"Received raw message: {message}")
                    
                    # 解析JSON
                    # Parse JSON
                    data = None
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        self.logger.error("無法解析JSON消息")
                        self.logger.error("Could not parse JSON message")
                        continue
                    
                    # 記錄解析後的消息
                    # Log parsed message
                    self.logger.info(f"解析後的消息數據: {data}")
                    self.logger.info(f"Parsed message data: {data}")
                    
                    # 檢查消息類型
                    # Check message type
                    if isinstance(data, dict) and "type" in data:
                        self.logger.info("發現 type 字段，處理命令")
                        self.logger.info("Found type field, handling command")
                        await self._handle_command(websocket, data)
                    else:
                        self.logger.warning("未知消息格式，忽略")
                        self.logger.warning("Unknown message format, ignoring")
                except Exception as e:
                    self.logger.error(f"處理消息時出錯: {e}")
                    self.logger.error(f"Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(f"客戶端連接關閉: {client_info}, 代碼: {e.code}, 原因: {e.reason}")
            self.logger.info(f"Client connection closed: {client_info}, code: {e.code}, reason: {e.reason}")
        except Exception as e:
            self.logger.error(f"處理客戶端時出錯: {e}")
            self.logger.error(f"Error handling client: {e}")
        finally:
            # 從客戶端集合中移除
            # Remove from client set
            with self.lock:
                self.clients.discard(websocket)
                self.video_clients.discard(websocket)
            
            self.logger.info(f"客戶端斷開連接: {client_info}")
            self.logger.info(f"Client disconnected: {client_info}")
    
    async def _handle_command(self, websocket, data):
        """處理客戶端命令
        
        Args:
            websocket: WebSocket連接
            data (dict): 命令數據
        """
        command_type = data.get("type", "")
        command_data = data.get("data", {})
        command_id = data.get("id", "unknown")
        
        self.logger.info(f"處理命令: {command_type}, ID: {command_id}")
        self.logger.info(f"Processing command: {command_type}, ID: {command_id}")
        
        # 處理特殊命令
        # Handle special commands
        if command_type == "ping":
            # 處理 ping 命令
            # Handle ping command
            timestamp = command_data.get("timestamp", time.time() * 1000)
            response = {
                "type": "pong",
                "data": {
                    "timestamp": timestamp,
                    "server_time": time.time() * 1000
                },
                "id": command_id
            }
            
            try:
                await websocket.send(json.dumps(response))
                self.logger.info("已發送 pong 響應")
                self.logger.info("Sent pong response")
            except Exception as e:
                self.logger.error(f"發送 pong 響應時出錯: {e}")
                self.logger.error(f"Error sending pong response: {e}")
            
            return
        
        elif command_type == "get_status":
            # 處理獲取狀態命令
            # Handle get status command
            await self._send_status(websocket)
            return
        
        elif command_type == "start_video_stream":
            # 處理開始視頻流命令
            # Handle start video stream command
            with self.lock:
                self.video_clients.add(websocket)
            
            self.logger.info(f"客戶端已添加到視頻流列表，當前視頻客戶端數量: {len(self.video_clients)}")
            self.logger.info(f"Client added to video stream list, current video clients: {len(self.video_clients)}")
            
            # 如果視頻流尚未啟動，則啟動它
            # Start video streaming if not already started
            if not self.video_streaming:
                self.start_video_streaming()
            
            response = {
                "type": "command_response",
                "data": {
                    "success": True,
                    "message": "Video streaming started",
                    "message_cht": "視頻流已啟動"
                },
                "id": command_id
            }
            
            try:
                await websocket.send(json.dumps(response))
            except Exception as e:
                self.logger.error(f"發送視頻流啟動響應時出錯: {e}")
                self.logger.error(f"Error sending video stream start response: {e}")
            
            return
        
        elif command_type == "stop_video_stream":
            # 處理停止視頻流命令
            # Handle stop video stream command
            with self.lock:
                self.video_clients.discard(websocket)
            
            self.logger.info(f"客戶端已從視頻流列表中移除，當前視頻客戶端數量: {len(self.video_clients)}")
            self.logger.info(f"Client removed from video stream list, current video clients: {len(self.video_clients)}")
            
            # 如果沒有更多視頻客戶端，則停止視頻流
            # Stop video streaming if no more video clients
            if not self.video_clients and self.video_streaming:
                self.stop_video_streaming()
            
            response = {
                "type": "command_response",
                "data": {
                    "success": True,
                    "message": "Video streaming stopped",
                    "message_cht": "視頻流已停止"
                },
                "id": command_id
            }
            
            try:
                await websocket.send(json.dumps(response))
            except Exception as e:
                self.logger.error(f"發送視頻流停止響應時出錯: {e}")
                self.logger.error(f"Error sending video stream stop response: {e}")
            
            return
        
        # 將命令轉發到機器人控制器
        # Forward command to robot controller
        try:
            result = self.command_handler(data)
            
            # 添加命令ID到響應
            # Add command ID to response
            if isinstance(result, dict):
                result["id"] = command_id
            
            # 發送響應
            # Send response
            await websocket.send(json.dumps(result))
        except Exception as e:
            self.logger.error(f"處理命令時出錯: {e}")
            self.logger.error(f"Error handling command: {e}")
            
            # 發送錯誤響應
            # Send error response
            error_response = {
                "type": "error",
                "data": {
                    "message": f"Error: {str(e)}",
                    "message_cht": f"錯誤: {str(e)}"
                },
                "id": command_id
            }
            
            try:
                await websocket.send(json.dumps(error_response))
            except Exception as send_error:
                self.logger.error(f"發送錯誤響應時出錯: {send_error}")
                self.logger.error(f"Error sending error response: {send_error}")
    
    async def _send_status(self, websocket):
        """發送狀態到客戶端
        
        Args:
            websocket: WebSocket連接
        """
        try:
            # 獲取狀態
            # Get status
            status = self.status_provider()
            
            # 構建狀態消息
            # Build status message
            status_message = {
                "type": "status_update",
                "data": status,
                "id": f"status_{int(time.time() * 1000)}"
            }
            
            # 發送狀態
            # Send status
            await websocket.send(json.dumps(status_message))
        except Exception as e:
            self.logger.error(f"發送狀態時出錯: {e}")
            self.logger.error(f"Error sending status: {e}")
    
    def start_video_streaming(self):
        """啟動視頻流
        Start video streaming"""
        if self.video_streaming:
            self.logger.info("視頻流已經在運行中")
            self.logger.info("Video streaming is already running")
            return
            
        self.logger.info("啟動視頻流...")
        self.logger.info("Starting video streaming...")
        self.video_streaming = True
        
        # 啟動視頻流線程
        # Start video streaming thread
        self.video_thread = threading.Thread(target=self._video_streaming_loop)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        self.logger.info("視頻流已啟動")
        self.logger.info("Video streaming started")
    
    def stop_video_streaming(self):
        """停止視頻流
        Stop video streaming"""
        if not self.video_streaming:
            self.logger.info("視頻流已經停止")
            self.logger.info("Video streaming is already stopped")
            return
            
        self.logger.info("停止視頻流...")
        self.logger.info("Stopping video streaming...")
        self.video_streaming = False
        
        if self.video_thread:
            try:
                self.video_thread.join(timeout=1.0)
                self.video_thread = None
            except Exception as e:
                self.logger.error(f"等待視頻流線程結束時出錯: {e}")
                self.logger.error(f"Error waiting for video thread to end: {e}")
            
        self.logger.info("視頻流已停止")
        self.logger.info("Video streaming stopped")
            
    def broadcast_status(self, status=None):
        """廣播狀態到所有客戶端
        Broadcast status to all clients
        
        Args:
            status (dict or dict with type field, optional): 要廣播的狀態或完整消息，如果為None則獲取當前狀態
            (Status to broadcast or complete message, if None get current status)
        """
        if not self.running or not self.clients:
            return
        
        try:
            # 檢查是否已經是完整的消息
            # Check if already a complete message
            if status is not None and isinstance(status, dict) and "type" in status:
                # 已經是完整的消息，直接使用
                # Already a complete message, use directly
                message = status
            else:
                # 獲取狀態
                # Get status
                if status is None:
                    status = self.status_provider()
                
                # 新增調試日誌，檢查人臉座標是否存在
                # Add debug log, check if face coordinates exist
                if status:
                    self.logger.info(f"WebSocketServer.broadcast_status: 狀態数据包含客户端所需的人臉坐标数据: face_x={status.get('face_x', 'missing')}, face_y={status.get('face_y', 'missing')}")
                    self.logger.info(f"WebSocketServer.broadcast_status: Status data contains face coordinates needed by client: face_x={status.get('face_x', 'missing')}, face_y={status.get('face_y', 'missing')}")
                    
                    # 確保人臉座標以浮點數格式傳送
                    # Ensure face coordinates are transmitted as float
                    if 'face_x' in status and status['face_x'] is not None:
                        status['face_x'] = float(status['face_x'])
                    if 'face_y' in status and status['face_y'] is not None:
                        status['face_y'] = float(status['face_y'])
            
                # 構建狀態消息
                # Build status message
                message = {
                    "type": "status_update",
                    "data": status,
                    "id": f"status_{int(time.time() * 1000)}"
                }
            
            # 序列化為JSON
            # Serialize to JSON
            message_json = json.dumps(message)
            
            # 廣播到所有客戶端
            # Broadcast to all clients
            with self.lock:
                clients = list(self.clients)
            
            # 創建新的事件循環
            # Create new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 廣播消息
            # Broadcast message
            loop.run_until_complete(self._broadcast(message_json, clients))
            loop.close()
            
            self.logger.info(f"成功廣播消息到 {len(clients)} 個客戶端")
            self.logger.info(f"Successfully broadcast message to {len(clients)} clients")
        except Exception as e:
            self.logger.error(f"廣播狀態時出錯: {e}")
            self.logger.error(f"Error broadcasting status: {e}")
    
    async def _broadcast(self, message, clients):
        """向所有客戶端廣播消息
        Broadcast message to all clients
        
        Args:
            message (str): 要廣播的消息 (Message to broadcast)
            clients (list): 客戶端列表 (Client list)
        """
        if not clients:
            return
        
        # 創建所有發送任務
        # Create all send tasks
        send_tasks = []
        for client in clients:
            if self._is_connection_closed(client):
                continue
            
            # 創建發送任務
            # Create send task
            task = asyncio.ensure_future(self._send_to_client(client, message))
            send_tasks.append(task)
        
        # 等待所有任務完成
        # Wait for all tasks to complete
        if send_tasks:
            await asyncio.gather(*send_tasks, return_exceptions=True)
    
    async def _send_to_client(self, client, message):
        """發送消息到客戶端
        Send message to client
        
        Args:
            client: WebSocket客戶端
            message (str): 要發送的消息
        """
        try:
            await client.send(message)
            return True
        except websockets.exceptions.ConnectionClosed:
            # 連接已關閉，從客戶端集合中移除
            # Connection closed, remove from client set
            with self.lock:
                self.clients.discard(client)
                self.video_clients.discard(client)
            return False
        except Exception as e:
            self.logger.error(f"發送消息到客戶端時出錯: {e}")
            self.logger.error(f"Error sending message to client: {e}")
            return False
    
    def _video_streaming_loop(self):
        """視頻流主循環
        Video streaming main loop"""
        import numpy as np
        import cv2
        from datetime import datetime
        
        self.logger.info("啟動視頻流循環")
        self.logger.info("Starting video streaming loop")
        
        # 視頻流循環參數
        # Video streaming loop parameters
        last_frame_time = 0
        frame_count = 0    # 幀計數器，用於動畫效果
        error_count = 0    # 錯誤計數器
        max_errors = 5     # 最大連續錯誤數
        
        # 使用 VisionSystem 的攝像頭
        # Use VisionSystem's camera
        camera = None
        try:
            # 檢查是否有視覺系統實例
            # Check if vision system instance is available
            if self.vision_system is not None:
                self.logger.info("使用 VisionSystem 的攝像頭實例")
                self.logger.info("Using VisionSystem's camera instance")
                # 不需要打開新的攝像頭，我們將直接從 VisionSystem 獲取幀
                # No need to open a new camera, we will get frames directly from VisionSystem
            else:
                self.logger.warning("找不到視覺系統實例，將使用模擬視頻")
                self.logger.warning("Could not find vision system instance, will use simulated video")
        except Exception as e:
            self.logger.error(f"初始化攝像頭時出錯: {e}")
            self.logger.error(f"Error initializing camera: {e}")
            camera = None
        
        # 主視頻流循環
        # Main video streaming loop
        while self.video_streaming and self.running:
            try:
                # 檢查是否有視頻客戶端
                # Check if there are video clients
                with self.lock:
                    if not self.video_clients:
                        time.sleep(0.1)
                        continue
                
                # 獲取當前時間
                # Get current time
                current_time = time.time()
                
                # 檢查是否應該發送新幀
                # Check if should send new frame
                if current_time - last_frame_time < self.video_interval:
                    time.sleep(0.01)  # 短暫休眠以減少CPU使用率
                    continue
                
                try:
                    # 獲取當前時間戳
                    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    
                    # 從 VisionSystem 獲取幀
                    # Get frame from VisionSystem
                    if self.vision_system is not None:
                        vision_frame = self.vision_system.get_latest_frame()
                        if vision_frame is not None:
                            self.logger.debug("從 VisionSystem 獲取到幀")
                            self.logger.debug("Got frame from VisionSystem")
                            frame = vision_frame
                            height, width = frame.shape[:2]
                        else:
                            self.logger.warning("無法從 VisionSystem 獲取幀，將使用模擬視頻")
                            self.logger.warning("Cannot get frame from VisionSystem, will use simulated video")
                            # 創建一個模擬幀作為備用
                            # Create a simulated frame as fallback
                            height, width = 480, 640
                            frame = np.zeros((height, width, 3), dtype=np.uint8)
                            frame[:, :] = (30, 30, 50)  # 藍色背景 / Blue background
                            
                            # 添加動畫效果 / Add animation
                            center_x = int(width/2 + width/4 * np.sin(frame_count * 0.05))
                            center_y = int(height/2 + height/4 * np.cos(frame_count * 0.05))
                            cv2.circle(frame, (center_x, center_y), 30, (0, 165, 255), -1)
                            
                            # 添加文字說明這是模擬視頻
                            # Add text explaining this is simulated video
                            cv2.putText(frame, f'Vision System Error - Simulated Video', (width - 350, height - 20), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    else:
                        # 如果沒有 VisionSystem，創建一個模擬幀
                        # If no VisionSystem, create a simulated frame
                        height, width = 480, 640
                        frame = np.zeros((height, width, 3), dtype=np.uint8)
                        frame[:, :] = (30, 30, 50)  # 藍色背景 / Blue background
                        
                        # 添加動畫效果 / Add animation
                        center_x = int(width/2 + width/4 * np.sin(frame_count * 0.05))
                        center_y = int(height/2 + height/4 * np.cos(frame_count * 0.05))
                        cv2.circle(frame, (center_x, center_y), 30, (0, 165, 255), -1)
                    
                    # 增加幀計數器 / Increment frame counter
                    frame_count += 1
                    
                    # 添加文字 / Add text
                    cv2.putText(frame, f'MaoMao Robot Camera', (20, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 200, 255), 1)
                    cv2.putText(frame, f'Time: {current_timestamp}', (20, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                except Exception as e:
                    self.logger.error(f"創建模擬幀時出錯: {e}")
                    self.logger.error(f"Error creating simulated frame: {e}")
                    # 創建一個簡單的錯誤幀
                    height, width = 480, 640  # 確保在錯誤情況下也有定義 width 和 height
                    frame = np.zeros((height, width, 3), dtype=np.uint8)
                    cv2.putText(frame, f'Error: {str(e)[:30]}', (50, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                
                # 確保 width 和 height 在所有代碼路徑中都有定義
                # Ensure width and height are defined in all code paths
                if 'width' not in locals() or 'height' not in locals():
                    height, width = frame.shape[:2]  # 從幀中提取尺寸
                    self.logger.info(f"從幀中提取尺寸: {width}x{height}")
                    self.logger.info(f"Extracted dimensions from frame: {width}x{height}")
                
                # 降低JPEG品質以減少帶寬使用
                # Lower JPEG quality to reduce bandwidth usage
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # 將圖像編碼為base64
                # Encode image to base64
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                # 構建視頻幀消息
                # Build video frame message
                video_message = {
                    "type": "video_frame",
                    "data": {
                        "image": jpg_as_text,
                        "timestamp": current_time,
                        "width": width,
                        "height": height
                    }
                }
                
                # 序列化為JSON
                # Serialize to JSON
                message_json = json.dumps(video_message)
                
                # 廣播到所有視頻客戶端
                # Broadcast to all video clients
                with self.lock:
                    video_clients = list(self.video_clients)
                
                if video_clients:
                    try:
                        # 創建新的事件循環
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # 實際發送消息
                        loop.run_until_complete(self._broadcast(message_json, video_clients))
                        loop.close()
                        
                        # 更新最後發送幀的時間
                        last_frame_time = current_time
                        error_count = 0  # 重置錯誤計數器
                    except websockets.exceptions.ConnectionClosedOK as e:
                        self.logger.info(f"在發送視頻幀期間連接關閉: {e}")
                        self.logger.info(f"Connection closed during video frame send: {e}")
                        # 不計入錯誤計數，這是正常的連接關閉
                    except Exception as e:
                        self.logger.error(f"發送視頻幀時出錯: {e}")
                        self.logger.error(f"Error sending video frame: {e}")
                        error_count += 1
                        if error_count >= max_errors:
                            self.logger.error(f"連續發生 {error_count} 個錯誤，重新檢查客戶端列表")
                            self.logger.error(f"Consecutive {error_count} errors, rechecking client list")
                            # 清理客戶端列表，移除已關閉的連接
                            with self.lock:
                                self.video_clients = {client for client in self.video_clients if not self._is_connection_closed(client)}
                            error_count = 0  # 重置錯誤計數器
                        time.sleep(0.1)
                else:
                    # 沒有客戶端或發送失敗
                    self.logger.warning("沒有視頻客戶端或發送失敗")
                    self.logger.warning("No video clients or sending failed")
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"視頻流循環中出錯: {e}")
                self.logger.error(f"Error in video streaming loop: {e}")
                error_count += 1
                if error_count >= max_errors:
                    self.logger.error(f"連續發生 {error_count} 個錯誤，重新檢查客戶端列表")
                    self.logger.error(f"Consecutive {error_count} errors, rechecking client list")
                    # 清理客戶端列表，移除已關閉的連接
                    with self.lock:
                        self.video_clients = {client for client in self.video_clients if not self._is_connection_closed(client)}
                    error_count = 0  # 重置錯誤計數器
                time.sleep(0.5)  # 出錯時稍微長一點的休眠
        
        self.logger.info("視頻流循環已結束")
        self.logger.info("Video streaming loop ended")
