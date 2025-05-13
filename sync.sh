#!/bin/bash

# 毛毛安全機器人同步腳本
# 將本地代碼同步到 Raspberry Pi

# 顯示彩色輸出的函數
print_green() {
    echo -e "\033[0;32m$1\033[0m"
}

print_yellow() {
    echo -e "\033[0;33m$1\033[0m"
}

print_red() {
    echo -e "\033[0;31m$1\033[0m"
}

# 設置變數
PI_HOST="security-bot.local"
PI_USER="pi"
PI_DIR="/home/pi/robot/maomao-security"
LOCAL_DIR="/Users/jeffrey/sonia-projects/maomao-security"

# 檢查 rsync 是否已安裝
if ! command -v rsync &> /dev/null; then
    print_red "錯誤: rsync 未安裝，請先安裝 rsync"
    exit 1
fi

# 顯示同步信息
print_yellow "準備同步代碼到 Raspberry Pi..."
print_yellow "本地目錄: $LOCAL_DIR"
print_yellow "目標主機: $PI_HOST"
print_yellow "目標目錄: $PI_DIR"
echo ""

# 檢查 Raspberry Pi 是否可訪問
print_yellow "檢查 Raspberry Pi 是否可訪問..."
if ping -c 1 $PI_HOST &> /dev/null; then
    print_green "Raspberry Pi 可訪問!"
else
    print_red "錯誤: 無法訪問 Raspberry Pi ($PI_HOST)"
    print_yellow "請確保 Raspberry Pi 已開機並連接到網絡"
    exit 1
fi

# 創建目標目錄（如果不存在）
print_yellow "確保目標目錄存在..."
ssh $PI_USER@$PI_HOST "mkdir -p $PI_DIR"

# 使用 rsync 同步文件
print_yellow "開始同步文件..."
rsync -avz --delete \
    --exclude "node_modules" \
    --exclude ".git" \
    --exclude ".next" \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    --exclude ".DS_Store" \
    --exclude "venv" \
    --exclude "*.log" \
    $LOCAL_DIR/ $PI_USER@$PI_HOST:$PI_DIR/

# 檢查同步結果
if [ $? -eq 0 ]; then
    print_green "同步完成!"
    print_yellow "提示: 在 Raspberry Pi 上，你可能需要安裝依賴並重新啟動服務"
    print_yellow "後端: cd $PI_DIR/backend && pip install -r requirements.txt"
    print_yellow "前端: cd $PI_DIR/frontend && npm install"
else
    print_red "同步過程中發生錯誤"
    exit 1
fi

# 提供遠程啟動命令的提示
print_yellow "要在 Raspberry Pi 上啟動服務，可以使用以下命令:"
print_yellow "後端: ssh $PI_USER@$PI_HOST \"cd $PI_DIR/backend && python main.py\""
print_yellow "前端: ssh $PI_USER@$PI_HOST \"cd $PI_DIR/frontend && npm run dev\""

exit 0
