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
        self.face_detection_enabled = False  # 人臉識別功能狀態 (Face detection status)
        
        self.logger.info(f"WebSocket服務器初始化完成 (端口: {port})")
        self.logger.info(f"WebSocket server initialization complete (port: {port})")
        
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
        """運行WebSocket服務器的主循環"""
        self.logger.info(f"啟動WebSocket服務器在端口 {self.port}")
        self.logger.info(f"Starting WebSocket server on port {self.port}")
        
        # 創建新的事件循環
        # Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 存儲事件循環供其他網絡操作使用
        # Store event loop for other network operations
        self.loop = loop
        
        async def start_server_async():
            return await websockets.serve(self._handle_client, "0.0.0.0", self.port)
        
        # 啟動服務器
        # Start server
        self.server = loop.run_until_complete(start_server_async())
        self.logger.info("WebSocket服務器已啟動，等待連接...")
        self.logger.info("WebSocket server started, waiting for connections...")
        
        # 運行事件循環
        # Run event loop
        loop.run_forever()
    
    def _stop_server(self):
        """停止WebSocket服務器"""
        if self.server:
            self.server.close()
            return asyncio.ensure_future(self.server.wait_closed())
    
    async def _handle_client(self, websocket):
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
        
        elif command_type in ["toggle_face_detection", "start_face_detection", "stop_face_detection"]:
            # 處理開啟/關閉人臉識別命令
            # Handle face detection commands
            if command_type == "toggle_face_detection":
                enabled = command_data.get("enabled", False)
            elif command_type == "start_face_detection":
                enabled = True
            else:  # stop_face_detection
                enabled = False
                
            self.face_detection_enabled = enabled
            
            self.logger.info(f"人臉識別功能已{'開啟' if enabled else '關閉'}")
            self.logger.info(f"Face detection {'enabled' if enabled else 'disabled'}")
            
            response = {
                'type': 'command_response',
                'data': {
                    'status': 'success',
                    'message': f"Face detection {'enabled' if enabled else 'disabled'}"
                },
                'id': command_id
            }
        elif command_type == 'get_status':
            # 處理獲取狀態命令
            # Handle get status command
            await self._send_status(websocket)
            return
        elif command_type == 'start_video_stream':
            # 處理開始視頻流命令
            # Handle start video stream command
            with self.lock:
                if websocket not in self.video_clients:
                    self.video_clients.add(websocket)
                    self.logger.info(f"客戶端已添加到視頻流列表，當前視頻客戶端數量: {len(self.video_clients)}")
                    self.logger.info(f"Client added to video stream list, current video clients: {len(self.video_clients)}")
                
            # 如果視頻流尚未啟動，則啟動它
            # Start video stream if not already started
            if not self.video_streaming:
                self.start_video_streaming()
                
            response = {
                'type': 'command_response',
                'data': {
                    'status': 'success',
                    'message': 'Video streaming started'
                },
                'id': command_id
            }
        elif command_type == 'stop_video_stream':
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
        """向一組客戶端廣播消息
        Broadcast message to a group of clients
        
        Args:
            message (str): 要發送的消息 / Message to send
            clients (list): 客戶端列表 / List of clients
            
        Returns:
            int: 成功發送的消息數量 / Number of successfully sent messages
        """
        if not clients:
            return 0
            
        # 記錄廣播開始
        # Log broadcast start
        self.logger.debug(f"開始廣播消息到 {len(clients)} 個客戶端")
        self.logger.debug(f"Starting broadcast to {len(clients)} clients")
        
        # 分割長消息的日誌
        # Log long message in chunks
        message_length = len(message)
        if message_length > 200:
            self.logger.debug(f"消息長度: {message_length} 字符")
            self.logger.debug(f"消息開頭: {message[:50]}...")
            self.logger.debug(f"消息結尾: ...{message[-50:]}")
        
        # 對所有客戶端併發發送消息
        # Send message to all clients concurrently
        results = await asyncio.gather(*[
            self._safe_send(client, message) for client in clients
        ], return_exceptions=True)
        
        # 計算成功和失敗的發送數量
        # Calculate successful and failed sends
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False or isinstance(r, Exception))
        
        self.logger.debug(f"廣播完成: {successes} 成功, {failures} 失敗")
        self.logger.debug(f"Broadcast complete: {successes} success, {failures} failed")
        
        return successes
    
    async def _safe_send(self, websocket, message):
        """安全地發送消息到WebSocket客戶端
        Safely send message to WebSocket client
        
        Args:
            websocket: WebSocket客戶端對象 / WebSocket client object
            message (str): 要發送的消息 / Message to send
            
        Returns:
            bool: 是否成功發送 / Whether send was successful
        """
        try:
            if websocket.open:
                await websocket.send(message)
                return True
            else:
                # WebSocket已關閉
                # WebSocket already closed
                self.logger.debug(f"嘗試發送到已關閉的WebSocket")
                self.logger.debug(f"Attempted to send to closed WebSocket")
                
                # 移除非活動客戶端
                # Remove inactive client
                self._remove_client(websocket)
                return False
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.info(f"連接已關閉，無法發送消息: {e}")
            self.logger.info(f"Connection closed, cannot send message: {e}")
            # 移除非活動客戶端
            # Remove inactive client
            self._remove_client(websocket)
            return False
        except Exception as e:
            self.logger.error(f"發送消息時出錯: {type(e).__name__}: {e}")
            self.logger.error(f"Error sending message: {type(e).__name__}: {e}")
            return False
            
    def _video_streaming_loop(self):
        """視頁流主循環
        Video streaming main loop"""
{{ ... }}
                        self.logger.warning("使用預設尺寸: 640x480")
                        self.logger.warning("Using default dimensions: 640x480")
                
                try:
                    # 使用更高的圖像尺寸以提高清晰度
                # Use higher image resolution for better clarity
                self.logger.debug(f"調整前的圖像尺寸: {frame.shape}")
                small_frame = cv2.resize(frame, (480, 360))
                self.logger.debug(f"調整後的圖像尺寸: {small_frame.shape}")
                
                # 使用更高的圖像質量
                # Use higher image quality - 80% quality for better text readability
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                success, buffer = cv2.imencode('.jpg', small_frame, encode_param)
                
                if not success:
                    self.logger.error("將圖像編碼為JPEG失敗")
                    self.logger.error("Failed to encode image to JPEG")
                    continue
                    
                self.logger.debug(f"JPEG緩衝區大小: {len(buffer)} 字節")
                
                # 編碼為 Base64
                # Encode to Base64
                try:
                    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                    self.logger.debug(f"Base64編碼成功，長度: {len(jpg_as_text)} 字符")
                except Exception as e:
                    self.logger.error(f"Base64編碼失敗: {e}")
                    self.logger.error(f"Base64 encoding failed: {e}")
                    continue
                    
                    # 創建基本的視頁幀消息
                    # Create basic video frame message
                    video_message = {
                        "type": "video_frame",
{{ ... }}
                        log_message['data']['image'] = f'[BASE64 IMAGE DATA: {len(jpg_as_text)} bytes (reduced quality)]'
                    
                    # 在日誌中記錄消息（不包含圖像數據）
                    # Log the message (without image data)
                    self.logger.debug(f"發送視頁幀消息: {log_message}")
                    try:
                    # 序列化為 JSON
                    # Serialize to JSON
                    message_json = json.dumps(video_message)
                    
                    # 詳細記錄JSON內容（不包含圖像數據）
                    debug_message = video_message.copy()
                    if 'data' in debug_message and 'image' in debug_message['data']:
                        debug_message['data'] = debug_message['data'].copy()
                        image_length = len(debug_message['data']['image'])
                        debug_message['data']['image'] = f'[BASE64 IMAGE: {image_length} chars]'
                    
                    self.logger.debug(f"視頻幀JSON消息內容: {debug_message}")
                    self.logger.debug(f"Video frame JSON message content: {debug_message}")
                    
                    # 驗證JSON格式是否正確
                    # Validate JSON format
                    _ = json.loads(message_json)  # 測試能否被解析
                    self.logger.debug(f"JSON驗證成功, 長度: {len(message_json)} 字符")
                    self.logger.debug(f"JSON validation successful, length: {len(message_json)} chars")
                except Exception as e:
                    self.logger.error(f"JSON serialization error: {e}")
                    self.logger.error(f"Problematic message: {str(video_message)[:200]}...")
                    # 創建一個簡化的失敗消息
                    message_json = json.dumps({
{{ ... }}
                        "data": {
                            "message": "Video frame encoding failed",
                            "timestamp": current_time
                        }
                    })
                
                # 廣播到所有視頁客戶端
                # Broadcast to all video clients
                with self.lock:
                    video_clients = list(self.video_clients)
                
                # 添加時間戳到視頁幀消息
                # Add timestamp to video frame message
                video_message['data']['timestamp'] = int(current_time * 1000)  # 毫秒時間戳
                
                if video_clients:
                    try:
                        # 記錄客戶端數量
                        self.logger.debug(f"準備發送視頻幀到 {len(video_clients)} 個客戶端")
                        self.logger.debug(f"Preparing to send video frame to {len(video_clients)} clients")
                        
                        # 使用現有的事件循環而不是創建新的
                        # Use existing event loop instead of creating a new one
                        future = asyncio.run_coroutine_threadsafe(
                            self._broadcast(message_json, video_clients),
                            self.loop
                        )
                        
                        # 等待短時間，檢查是否成功發送
                        try:
                            # 只等待很短的時間，避免阻塞流
                            result = future.result(0.01)
                            self.logger.debug(f"視頻幀廣播結果: {result}")
                        except asyncio.TimeoutError:
                            # 正常，因為我們只等待很短時間
                            pass
                        except Exception as e:
                            self.logger.error(f"廣播視頻幀時出錯: {e}")
                            self.logger.error(f"Error broadcasting video frame: {e}")
                        
                        # 更新最後發送幀的時間
                        last_frame_time = current_time
                        error_count = 0  # 重置錯誤計數器
                        
                        # 記錄成功發送視頻幀
                        self.logger.debug(f"成功發送視頻幀，時間戳: {int(current_time * 1000)}")
                        self.logger.debug(f"Successfully sent video frame, timestamp: {int(current_time * 1000)}")
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
            # except Exception as e:
            #     self.logger.error(f"視頻流循環中出錯: {e}")
            #     self.logger.error(f"Error in video streaming loop: {e}")
            #     error_count += 1
            #     if error_count >= max_errors:
            #         self.logger.error(f"連續發生 {error_count} 個錯誤，重新檢查客戶端列表")
            #         self.logger.error(f"Consecutive {error_count} errors, rechecking client list")
            #         # 清理客戶端列表，移除已關閉的連接
            #         with self.lock:
            #             self.video_clients = {client for client in self.video_clients if not self._is_connection_closed(client)}
            #         error_count = 0  # 重置錯誤計數器
            #     time.sleep(0.5)  # 出錯時稍微長一點的休眠
        
        self.logger.info("視頻流循環已結束")
        self.logger.info("Video streaming loop ended")
