# 毛毛安全機器人系統說明

## 系統概述

毛毛安全機器人是一個多功能的安全巡邏機器人，結合了人工智能視覺識別、多種感應器和多個伺服馬達，能夠在不同的環境中執行安全監控任務。

### 硬體組成

- **控制系統**：樹莓派 5 和 Arduino
- **動作系統**：9個伺服馬達（控制眼睛、眼瞼、頸部和手臂）
- **視覺系統**：攝像頭，搭配 Google Teachable Machine 進行 AI 視覺識別
- **其他感應器**：距離等感應器

## 系統功能

毛毛安全機器人具有三種主要工作模式：

1. **手動模式 (Manual Mode)**：
   - 通過網頁界面直接控制機器人的移動和動作
   - 適合需要精確控制的場景

2. **巡邏模式 (Patrol Mode)**：
   - 機器人自動在指定區域內巡邏
   - 記錄並報告發現的異常情況

3. **監視模式 (Surveillance Mode)**：
   - 機器人固定在一個位置進行監控
   - 使用 AI 視覺識別特定人臉和學生證
   - 檢測到異常時發出警報

### 附加功能

4. **語音交互系統**：
   - 中文語音識別和回應
   - 多種 AI 服務支援 (OpenAI, Claude, Gemini, 本地 Ollama)
   - 智能心情分析系統
   - 實時情緒檢測和回應調整

5. **生物監測**：
   - 體溫監測
   - 心率監測
   - 健康狀態追蹤

## 系統架構

整個系統分為前端和後端兩大部分：

### 前端部分

前端使用 Next.js 框架開發，提供了一個直觀的用戶界面，讓用戶可以：

- 切換機器人的工作模式
- 查看機器人的視覺畫面
- 手動控制機器人的移動和動作
- 監控機器人的系統狀態（溫度、電池等）

### 後端部分

後端使用 Python 開發，負責控制機器人的所有功能：

- **核心控制**：協調各個子系統的工作
- **視覺處理**：處理攝像頭畫面和執行 AI 識別
- **動作控制**：控制機器人的移動和伺服馬達
- **通訊系統**：與前端進行數據交換
- **安全監控**：監控系統狀態，防止過熱等問題

## 程式碼架構

項目組織為幾個主要模塊：

### 後端程式碼結構

```
backend/
├── main.py                     # 主程序，啟動整個系統
├── config.json                 # 系統配置
├── core/                       # 核心控制
│   └── robot_controller.py     # 機器人主控制器
├── vision/                     # 視覺系統
│   └── vision_system.py        # 視覺處理和 AI 識別
├── movement/                   # 移動系統
│   ├── movement_controller.py  # 移動控制器
│   └── mobility_control/       # Arduino 移動控制
│       └── mobility_control.ino
├── servo/                      # 伺服馬達控制
│   ├── servo_controller.py     # 伺服馬達控制器
│   ├── arduino_controller.py   # Arduino 通訊
│   └── arduino_led_controller/ # LED 控制韌體
│       └── arduino_led_controller.ino
├── communication/              # 通訊系統
│   └── websocket_server.py     # WebSocket 服務器
├── safety/                     # 安全系統
│   └── watchdog.py             # 系統監控
├── modes/                      # 操作模式
│   └── mode_manager.py         # 模式管理
├── models/                     # AI 模型
│   ├── teachable_machine_model.tflite  # 主要 AI 模型
│   ├── labels.txt              # 模型標籤
│   └── pose-model/             # 姿態檢測模型
├── utils/                      # 工具程式
│   ├── logger.py               # 日誌系統
│   ├── config_loader.py        # 配置載入器
│   ├── audio_player.py         # 音頻播放
│   └── sound_manager.py        # 聲音管理
├── tools/                      # 開發工具
│   └── camera_viewer.py        # 攝像頭測試工具
└── logs/                       # 系統日誌
```

### 前端程式碼結構

```
frontend/
├── app/                        # Next.js app 目錄
│   ├── page.tsx                # 主頁面
│   ├── layout.tsx              # 應用佈局
│   ├── home/                   # 主頁（巡邏模式）
│   ├── remote/                 # 遠程控制頁（手動模式）
│   ├── safety/                 # 安全監控頁（監視模式）
│   ├── patrol/                 # 巡邏模式界面
│   ├── test/                   # 測試頁面
│   ├── video-test/             # 視頻測試
│   └── video-basic/            # 基本視頻顯示
├── components/                 # React 組件
│   ├── ui/                     # UI 組件 (shadcn/ui)
│   ├── navigation.tsx          # 導航組件
│   ├── battery-indicator.tsx   # 電池狀態
│   ├── emotion-display.tsx     # 情緒顯示
│   ├── radar-display.tsx       # 雷達可視化
│   └── face-coordinates-table.tsx # 人臉檢測顯示
├── hooks/                      # 自定義 React hooks
│   ├── useRobotConnection.js   # 機器人連接管理
│   └── use-toast.ts            # 吐司通知
├── lib/                        # 工具程式
│   └── utils.ts                # 輔助函數
└── public/                     # 靜態資源
```

### 附加模塊

```
robot_bio_monitor/              # 生物監測
├── __init__.py
├── body_temperature_monitor.py # 體溫監測
└── heartrate_monitor.py        # 心率監測

robot_conversation/             # 語音交互系統
├── voice_assistant.py          # 主要語音助手
├── setup_ai.py                 # AI 服務配置
├── mood_commands.py            # 情緒分析
├── requirements.txt            # Python 依賴
└── README.md                   # 語音系統文檔

robot_movement/                 # 移動控制韌體
├── __init__.py
├── mobility_control.ino        # 基本移動控制
└── mobility_control_R4.ino     # Arduino R4 移動控制

sound/                          # 音頻資源
├── robot.wav                   # 基本機器人聲音
├── robot-bass.wav
├── robot-compute.wav
├── robot-happy1.wav
├── robot-happy2.wav
└── robot-happy3.wav
```

## 數據流程

1. **用戶操作**：用戶通過前端界面發送指令
2. **前端處理**：前端將指令格式化並通過 WebSocket 發送到後端
3. **後端處理**：
   - WebSocket 服務器接收指令
   - 核心控制器解析指令並調用相應的子系統
   - 執行指令（如移動、拍照、切換模式等）
4. **狀態回傳**：後端將執行結果和機器人狀態通過 WebSocket 發送回前端
5. **前端顯示**：前端更新界面，顯示最新的機器人狀態和視頻畫面

## 啟動系統

1. **啟動後端**：
   ```
   cd backend
   python main.py
   ```

2. **啟動前端**：
   ```
   cd frontend
   npm run dev
   ```

3. **訪問界面**：打開瀏覽器，訪問 http://localhost:3000

## 注意事項

- 系統設計為可在 Mac 開發環境和樹莓派部署環境中運行
- 在樹莓派上運行時，請確保已安裝所有必要的依賴
- 溫度監控功能會防止系統過熱
- 移動控制有安全限制，防止機器人發生碰撞


開發人員:
   - 馬昀華 mamatthew12@gmail.com