# 中文語音助手

這是一個專為 Raspberry Pi 3 設計的中文語音對話程式，支援多種線上 AI 服務。

## 功能特色

- 中文語音識別 (支援繁體中文)
- 多種 AI 服務支援:
  - OpenAI GPT (需要 API Key)
  - Anthropic Claude (需要 API Key)
  - Google Gemini (需要 API Key)
  - 本地 Ollama (免費)
  - Groq API (免費)
  - 智能回應生成器 (完全免費)
- 中文語音合成和播放
- **智能心情分析系統**:
  - 實時分析用戶心情 (0-10分)
  - 根據心情調整 AI 回應語調
  - 記錄對話和心情歷史
  - 提供心情統計報告
- 多線程音頻處理
- 自動服務可用性檢測

## 系統需求

- Raspberry Pi 3 或以上
- Python 3.6+
- 麥克風和揚聲器
- 網路連接

## 快速開始

1. 安裝系統依賴:
```bash
sudo apt update
sudo apt install portaudio19-dev python3-pyaudio
```

2. 建立 Python virtual environment(venv):
```bash
cd /home/[使用者資料夾]
python -m venv myenv
source myenv/bin/activate
```安裝需要的python模組(requirements.txt)
pip install SpeechRecognition
pip install pygame
pip install gtts
pip install pyaudio
pip install requests
```

3. 配置 AI 服務:
```bash
python3 setup_ai.py
```

## AI 服務配置

### 1. OpenAI (推薦)
```bash
export OPENAI_API_KEY="sk-your-api-key"
```

### 2. Anthropic Claude
```bash
export ANTHROPIC_API_KEY="sk-ant-your-api-key"
```

### 3. Google Gemini
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

### 4. 本地 Ollama (免費)
```bash
# 安裝 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 啟動服務
ollama serve

# 下載中文模型
ollama pull qwen:7b
```

### 5. Hugging Face (免費)
無需配置，程式會自動使用免費額度。

## 使用方法

```bash
cd /home/[使用者資料夾]
source myenv/bin/activate
python3 voice_assistant.py
```

## 語音命令

### 基本命令
- 程式啟動後會自動監聽語音
- 直接說話，系統會自動識別並回應
- 說「再見」or「結束」來結束程式
- 按 Ctrl+C 強制退出

### 心情分析命令
- 說「心情統計」or「心情報告」- 查看詳細心情分析
- 說「心情歷史」or「心情記錄」- 查看最近心情記錄
- 說「我的心情」- 查看當前心情分數
- 說「重設心情」- 清除心情記錄重新開始

## 服務優先級

程式會按以下順序檢測並使用可用服務:
1. 本地 Ollama (如果運行中)
2. OpenAI API (如果有 API Key)
3. Anthropic Claude (如果有 API Key)
4. Google Gemini (如果有 API Key)
5. Hugging Face API (預設備用選項)
6. 內建簡單回應 (最後備選)

## 故障排除

### 音頻問題
- 確保麥克風和揚聲器正確連接
- 檢查 ALSA 音頻設置
- 使用 `arecord -l` 檢查錄音設備

### AI 服務問題
- 檢查網路連接
- 驗證 API Key 是否正確
- 確認 API 配額未超限

### 語音識別問題
- 確保網路連接穩定 (使用 Google 語音識別)
- 在安靜環境中測試
- 調整麥克風音量

## 目錄結構

```
robot_conversation/
├── voice_assistant.py   # 主程式
├── setup_ai.py          # AI 服務設置工具
├── requirements.txt     # Python 依賴
├── mood_commands.py     # 情緒模組 
└── README.md            # 說明文件
```