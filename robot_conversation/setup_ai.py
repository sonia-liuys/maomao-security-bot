#!/usr/bin/env python3
"""
AI 語音助手設置腳本
用於配置不同的 AI 服務
"""

import os
import sys

def setup_environment():
    """設置環境變數"""
    print("=== AI 語音助手設置 ===\n")
    
    print("支援的 AI 服務:")
    print("1. OpenAI GPT (需要 API Key)")
    print("2. Anthropic Claude (需要 API Key)")  
    print("3. Google Gemini (需要 API Key)")
    print("4. 本地 Ollama (免費，需要安裝)")
    print("5. Groq API (免費，需要註冊)")
    print("6. 智能回應生成器 (完全免費)\n")
    
    choice = input("請選擇您要配置的服務 (1-6): ")
    
    if choice == "1":
        setup_openai()
    elif choice == "2":
        setup_anthropic()
    elif choice == "3":
        setup_gemini()
    elif choice == "4":
        setup_ollama()
    elif choice == "5":
        setup_groq()
    elif choice == "6":
        print("智能回應生成器無需額外配置，可直接使用！")
        print("它會根據您的問題提供相應的智能回應。")
    else:
        print("無效選擇，退出設置。")
        return
    
    print("\n設置完成！現在可以運行語音助手了。")

def setup_openai():
    """設置 OpenAI API"""
    print("\n=== OpenAI 設置 ===")
    print("1. 前往 https://platform.openai.com/api-keys")
    print("2. 登入並創建新的 API Key")
    print("3. 複製 API Key")
    
    api_key = input("\n請輸入您的 OpenAI API Key: ").strip()
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
        print(f"export OPENAI_API_KEY='{api_key}'")
        print("請將上述命令添加到您的 ~/.bashrc 或 ~/.zshrc 中")

def setup_anthropic():
    """設置 Anthropic Claude API"""
    print("\n=== Anthropic Claude 設置 ===")
    print("1. 前往 https://console.anthropic.com/")
    print("2. 註冊帳號並創建 API Key")
    print("3. 複製 API Key")
    
    api_key = input("\n請輸入您的 Anthropic API Key: ").strip()
    if api_key:
        os.environ['ANTHROPIC_API_KEY'] = api_key
        print(f"export ANTHROPIC_API_KEY='{api_key}'")
        print("請將上述命令添加到您的 ~/.bashrc 或 ~/.zshrc 中")

def setup_gemini():
    """設置 Google Gemini API"""
    print("\n=== Google Gemini 設置 ===")
    print("1. 前往 https://makersuite.google.com/app/apikey")
    print("2. 登入 Google 帳號並創建 API Key")
    print("3. 複製 API Key")
    
    api_key = input("\n請輸入您的 Gemini API Key: ").strip()
    if api_key:
        os.environ['GEMINI_API_KEY'] = api_key
        print(f"export GEMINI_API_KEY='{api_key}'")
        print("請將上述命令添加到您的 ~/.bashrc 或 ~/.zshrc 中")

def setup_groq():
    """設置 Groq API"""
    print("\n=== Groq 設置 ===")
    print("Groq 提供免費的高速 AI API！")
    print("1. 前往 https://console.groq.com/")
    print("2. 註冊免費帳號")
    print("3. 創建 API Key")
    
    api_key = input("\n請輸入您的 Groq API Key: ").strip()
    if api_key:
        os.environ['GROQ_API_KEY'] = api_key
        print(f"export GROQ_API_KEY='{api_key}'")
        print("請將上述命令添加到您的 ~/.bashrc 或 ~/.zshrc 中")

def setup_ollama():
    """設置 Ollama"""
    print("\n=== Ollama 設置 ===")
    print("Ollama 是本地運行的 AI 模型，完全免費！")
    print("\n安裝步驟:")
    print("1. 安裝 Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
    print("2. 啟動 Ollama: ollama serve")
    print("3. 下載中文模型: ollama pull llama2-chinese")
    print("   或: ollama pull qwen:7b")
    print("   或: ollama pull chatglm3:6b")
    
    print("\n注意: Ollama 需要較多記憶體 (建議至少 4GB)")

if __name__ == "__main__":
    setup_environment()