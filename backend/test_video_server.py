#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單的 WebSocket 測試服務器，用於測試視頻流功能
Simple WebSocket test server for testing video streaming functionality
"""

import asyncio
import websockets
import json
import time
import base64
import cv2
import numpy as np
import logging
import sys

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("TestVideoServer")

class TestVideoServer:
    def __init__(self, host="localhost", port=8766):
        self.host = host
        self.port = port
        self.clients = set()
        self.video_clients = set()
        self.running = False
        self.video_streaming = False
        self.video_thread = None
        self.logger = logger
        
    async def handler(self, websocket):
        """處理 WebSocket 連接
        Handle WebSocket connection"""
        self.logger.info(f"新的客戶端連接: {websocket.remote_address}")
        
        # 添加到客戶端集合
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    # 解析 JSON 消息
                    data = json.loads(message)
                    cmd_type = data.get("type", "")
                    cmd_data = data.get("data", {})
                    command_id = data.get("id", "")
                    
                    self.logger.info(f"收到命令: {cmd_type}")
                    
                    # 處理 ping 命令
                    if cmd_type == "ping":
                        timestamp = cmd_data.get("timestamp", time.time() * 1000)
                        response = {
                            "type": "pong",
                            "data": {"timestamp": timestamp},
                            "id": command_id
                        }
                        await websocket.send(json.dumps(response))
                        continue
                    
                    # 處理開始視頻流命令
                    elif cmd_type == "start_video_stream":
                        self.logger.info("收到開始視頻流命令")
                        
                        # 將客戶端添加到視頻客戶端集合
                        self.video_clients.add(websocket)
                        self.logger.info(f"視頻客戶端數量: {len(self.video_clients)}")
                        
                        # 如果視頻流尚未啟動，則啟動它
                        if not self.video_streaming:
                            self.start_video_streaming()
                        
                        response = {
                            "type": "command_response",
                            "id": command_id,
                            "result": {"success": True, "message": "視頻流已啟動"}
                        }
                        
                        await websocket.send(json.dumps(response))
                        continue
                    
                    # 處理停止視頻流命令
                    elif cmd_type == "stop_video_stream":
                        self.logger.info("收到停止視頻流命令")
                        
                        # 將客戶端從視頻客戶端集合中移除
                        if websocket in self.video_clients:
                            self.video_clients.remove(websocket)
                            self.logger.info(f"視頻客戶端數量: {len(self.video_clients)}")
                        
                        # 如果沒有視頻客戶端，則停止視頻流
                        if len(self.video_clients) == 0:
                            self.stop_video_streaming()
                        
                        response = {
                            "type": "command_response",
                            "id": command_id,
                            "result": {"success": True, "message": "視頻流已停止"}
                        }
                        
                        await websocket.send(json.dumps(response))
                        continue
                    
                    # 其他命令
                    response = {
                        "type": "command_response",
                        "id": command_id,
                        "result": {"success": False, "message": f"未知命令: {cmd_type}"}
                    }
                    
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    self.logger.error(f"無效的 JSON 消息: {message}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "data": {"message": "無效的 JSON 消息"}
                    }))
                except Exception as e:
                    self.logger.error(f"處理消息時出錯: {e}")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "data": {"message": f"處理消息時出錯: {e}"}
                    }))
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"客戶端連接關閉: {websocket.remote_address}")
        finally:
            # 從客戶端集合中移除
            self.clients.remove(websocket)
            
            # 從視頻客戶端集合中移除
            if websocket in self.video_clients:
                self.video_clients.remove(websocket)
                self.logger.info(f"視頻客戶端數量: {len(self.video_clients)}")
                
                # 如果沒有視頻客戶端，則停止視頻流
                if len(self.video_clients) == 0:
                    self.stop_video_streaming()
    
    def start_video_streaming(self):
        """啟動視頻流
        Start video streaming"""
        if self.video_streaming:
            self.logger.info("視頻流已經啟動，跳過")
            return
            
        self.logger.info("啟動視頻流...")
        self.video_streaming = True
        
        # 啟動視頻流線程
        self.video_thread = asyncio.create_task(self._video_streaming_loop())
        self.logger.info("視頻流線程已啟動")
    
    def stop_video_streaming(self):
        """停止視頻流
        Stop video streaming"""
        if not self.video_streaming:
            return
            
        self.logger.info("停止視頻流...")
        self.video_streaming = False
        
        # 視頻線程將自動結束
        self.logger.info("視頻流已停止")
    
    async def _video_streaming_loop(self):
        """視頻流循環
        Video streaming loop"""
        self.logger.info("視頻流循環已啟動")
        
        # 視頻幀間隔（秒）
        frame_interval = 0.1
        
        # 創建一個測試圖像
        width, height = 640, 480
        
        # 上次發送幀的時間
        last_frame_time = 0
        frame_count = 0
        
        while self.video_streaming and self.running:
            try:
                # 檢查是否有視頻客戶端
                if not self.video_clients:
                    await asyncio.sleep(0.1)
                    continue
                
                # 獲取當前時間
                current_time = time.time()
                
                # 檢查是否應該發送新幀
                if current_time - last_frame_time < frame_interval:
                    await asyncio.sleep(0.01)
                    continue
                
                # 創建測試圖像
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # 添加時間戳
                timestamp = time.strftime("%H:%M:%S", time.localtime())
                cv2.putText(frame, f"Test Frame: {timestamp}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # 添加幀計數
                cv2.putText(frame, f"Frame: {frame_count}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # 添加彩色矩形
                color = ((frame_count * 5) % 255, (frame_count * 10) % 255, (frame_count * 15) % 255)
                cv2.rectangle(frame, (100, 150), (300, 350), color, -1)
                
                # 添加移動的圓形
                circle_x = int(width / 2 + 100 * np.sin(frame_count * 0.1))
                circle_y = int(height / 2 + 100 * np.cos(frame_count * 0.1))
                cv2.circle(frame, (circle_x, circle_y), 30, (0, 255, 0), -1)
                
                # 增加幀計數
                frame_count += 1
                
                # 降低 JPEG 品質以減少帶寬使用
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                
                # 將圖像編碼為 base64
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                # 構建視頻幀消息
                video_message = {
                    "type": "video_frame",
                    "data": {
                        "image": jpg_as_text,
                        "timestamp": current_time,
                        "width": width,
                        "height": height
                    }
                }
                
                # 序列化為 JSON
                message_json = json.dumps(video_message)
                
                # 廣播到所有視頻客戶端
                for websocket in list(self.video_clients):
                    try:
                        await websocket.send(message_json)
                    except websockets.exceptions.ConnectionClosed:
                        self.logger.info(f"視頻客戶端連接已關閉，將其移除")
                        self.video_clients.remove(websocket)
                    except Exception as e:
                        self.logger.error(f"發送視頻幀時出錯: {e}")
                
                # 更新最後發送幀的時間
                last_frame_time = current_time
                
                # 添加一些日誌，但不要太頻繁
                if frame_count % 10 == 0:
                    self.logger.info(f"已發送視頻幀 {frame_count}，客戶端數量: {len(self.video_clients)}")
                
            except Exception as e:
                self.logger.error(f"視頻流循環中出錯: {e}")
                await asyncio.sleep(0.5)
        
        self.logger.info("視頻流循環已結束")
    
    async def start_server(self):
        """啟動 WebSocket 服務器
        Start WebSocket server"""
        self.running = True
        self.logger.info(f"啟動 WebSocket 服務器: {self.host}:{self.port}")
        
        server = await websockets.serve(
            lambda websocket: self.handler(websocket),
            self.host, 
            self.port
        )
        
        self.logger.info(f"WebSocket 服務器已啟動: {self.host}:{self.port}")
        
        return server
    
    async def stop_server(self):
        """停止 WebSocket 服務器
        Stop WebSocket server"""
        self.running = False
        self.logger.info("停止 WebSocket 服務器...")
        
        # 停止視頻流
        self.stop_video_streaming()
        
        # 關閉所有客戶端連接
        for websocket in list(self.clients):
            await websocket.close()
        
        self.logger.info("WebSocket 服務器已停止")

async def main():
    # 創建服務器實例
    server = TestVideoServer()
    
    # 啟動服務器
    ws_server = await server.start_server()
    
    try:
        # 保持服務器運行
        await asyncio.Future()
    except KeyboardInterrupt:
        # 停止服務器
        await server.stop_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已被用戶中斷")
