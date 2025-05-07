#!/bin/bash

# 啟動腳本 - 同時啟動前端和後端

# 確保腳本在出錯時停止
set -e

# 顯示啟動信息
echo "正在啟動毛毛安全機器人系統..."

# 創建日誌目錄
mkdir -p backend/logs

# 安裝後端依賴
echo "安裝後端依賴..."
cd backend
pip install -r requirements.txt 2>/dev/null || echo "無法安裝後端依賴，可能已經安裝或缺少requirements.txt"
cd ..

# 安裝前端依賴
echo "安裝前端依賴..."
cd frontend
npm install 2>/dev/null || echo "無法安裝前端依賴，可能已經安裝"
cd ..

# 啟動後端 (後台運行)
echo "啟動後端服務..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# 等待後端啟動
sleep 2

# 啟動前端
echo "啟動前端服務..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "系統已啟動!"
echo "前端運行在: http://localhost:3000"
echo "後端WebSocket運行在: ws://localhost:8765"
echo ""
echo "按 Ctrl+C 停止服務"

# 等待用戶中斷
trap "kill $BACKEND_PID $FRONTEND_PID; echo '系統已停止'; exit" INT
wait
