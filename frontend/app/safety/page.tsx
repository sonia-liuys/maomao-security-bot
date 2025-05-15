"use client"

import { useState, useEffect, useRef } from "react"
import styles from './page.module.css'
import useRobotConnection from '@/hooks/useRobotConnection'
import { Card } from "@/components/ui/card"
import Navigation from "@/components/navigation"
import { Shield, Check, AlertTriangle, Play, Square } from "lucide-react"
import { Button } from "@/components/ui/button"

type Emotion = "happy" | "sad" | "neutral" | "excited" | "sleepy" | "suspicious" | "angry"

export default function SafetyMode() {
  // 狀態變量
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>("neutral")
  const [securityLevel, setSecurityLevel] = useState("Normal")
  const [threatDetected, setThreatDetected] = useState(false)
  const [statusMessage, setStatusMessage] = useState("Monitoring...")
  const [recognizedPerson, setRecognizedPerson] = useState<string | null>(null)
  const [eyeColor, setEyeColor] = useState<string>("green")
  const [currentEmoji, setCurrentEmoji] = useState<string>("😐")
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [emojiSize, setEmojiSize] = useState(350) // 默認 emoji 大小
  
  // 使用ref追蹤是否已經發送過命令
  const hasSentCommandRef = useRef(false)
  
  // 使用 useRobotConnection 鎖子
  const { isConnected: robotConnected, lastMessage: robotLastMessage, sendCommand: sendRobotCommand, robotStatus } = useRobotConnection('ws://localhost:8765');
  
  // 監聽機器人狀態變化
  useEffect(() => {
    if (robotConnected) {
      console.log('已連接到機器人');
      // 不再自動切換到監視模式，等待用戶點擊按鈕
    }
  }, [robotConnected]);
  
  // 啟動監視模式的函數
  const startSurveillanceMode = () => {
    if (!hasSentCommandRef.current) {
      console.log('切換到監視模式');
      sendRobotCommand({
        type: 'set_mode',
        data: { mode: 'surveillance' }
      });
      hasSentCommandRef.current = true;
      setStatusMessage("監視模式已啟動");
    }
  };
  
  // 結束監視模式的函數
  const stopSurveillanceMode = () => {
    console.log('結束監視模式');
    sendRobotCommand({
      type: 'set_mode',
      data: { mode: 'idle' }
    });
    hasSentCommandRef.current = false;
    setStatusMessage("監視模式已停止");
  };
  
  // 定義消息類型
  interface RobotMessage {
    type: string;
    data: {
      eye_color?: string;
      emoji?: string;
      recognized?: boolean;
      name?: string;
      message?: string;
      countdown?: number;
    };
  }

  // 監聽最後收到的消息
  useEffect(() => {
    try {
      if (!robotLastMessage) {
        console.log('沒有收到消息');
        return;
      }
      
      console.log('收到消息:', robotLastMessage);
      setLastMessage(robotLastMessage);
      
      // 特別處理識別結果消息
      const message = robotLastMessage as RobotMessage;
      console.log('消息類型:', message.type);
      
      if (message.type === 'recognition_result') {
        console.log('安全頁面收到識別結果消息:', message);
        
        const data = message.data;
        console.log('消息數據:', data);
        
        // 更新眼睛顏色
        if (data && data.eye_color) {
          console.log('設置眼睛顏色為:', data.eye_color);
          setEyeColor(data.eye_color);
        }
        
        // 更新表情符號
        if (data && data.emoji) {
          console.log('設置表情符號為:', data.emoji);
          setCurrentEmoji(data.emoji);
        }
        
        // 更新識別狀態
        if (data.recognized) {
          setCurrentEmotion('happy');
          setThreatDetected(false);
          setSecurityLevel('Normal');
          setRecognizedPerson(data.name || null);
          setStatusMessage(`Recognized: ${data.name || 'Unknown'}`);
        } else {
          setCurrentEmotion('suspicious');
          setThreatDetected(true);
          setSecurityLevel('Alert');
          setRecognizedPerson(null);
          setStatusMessage(data.message || 'Unknown Person Detected!');
        }
      }
    } catch (error) {
      console.error('處理消息時發生錯誤:', error);
    }
  }, [robotLastMessage]);
  
  // 更新連接狀態
  useEffect(() => {
    setIsConnected(robotConnected);
  }, [robotConnected]);
  
  // 處理窗口大小變化，調整 emoji 大小
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const handleResize = () => {
        const newSize = Math.min(window.innerWidth * 0.85, window.innerHeight * 0.7)
        setEmojiSize(newSize)
      }
      
      // 初始設置
      handleResize()
      
      // 添加窗口大小變化監聽
      window.addEventListener('resize', handleResize)
      
      return () => {
        window.removeEventListener('resize', handleResize)
      }
    }
  }, []);

  // 監聽眼睛顏色變化
  useEffect(() => {
    try {
      console.log('眼睛顏色狀態變化為:', eyeColor);
    } catch (error) {
      console.error('監聽眼睛顏色變化時發生錯誤:', error);
    }
  }, [eyeColor]);

  // 監聽 eyeColor 變化
  useEffect(() => {
    try {
      console.log('眼睛顏色狀態變化為:', eyeColor);
      
      // 強制刷新頁面
      const forceUpdate = setTimeout(() => {
        console.log('強制刷新頁面以更新光環顏色');
        // 使用空的 setState 來觸發重新渲染
        setCurrentEmotion(prev => prev);
      }, 100);
      
      return () => clearTimeout(forceUpdate);
    } catch (error) {
      console.error('監聽 eyeColor 變化時發生錯誤:', error);
    }
  }, [eyeColor]);
  
  // Emoji mapping for emotional states
  const emotionEmoji: Record<Emotion, string> = {
    happy: "😄",
    sad: "😢",
    neutral: "😐",
    excited: "😃",
    sleepy: "😴",
    suspicious: "😕",
    angry: "😡"
  }



  return (
    <div className="flex flex-col min-h-screen" style={{ backgroundColor: "#0d0d0d" }}>
      <Navigation />
      
      <main className="flex-grow p-0">
        <div className="w-full h-full">
          {/* Security Mode 標題已移除 */}
          
          <div className="w-full h-full flex flex-col">
              <div className="w-full h-full flex flex-col">
                <div className="flex justify-end mb-4">
                  <div className={`h-3 w-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}></div>
                </div>
                {/* Surveillance Mode 標題已移除 */}
                
                <div className="flex-grow flex flex-col items-center justify-center pt-20 pb-6">
                  {/* 表情符號和光環 */}
                  <div
                    className="relative flex items-center justify-center rounded-full transition-all duration-500"
                    style={{
                      width: `${emojiSize}px`,
                      height: `${emojiSize}px`,
                      background: "radial-gradient(circle, rgba(10,30,50,0.8) 0%, rgba(5,10,15,0.95) 70%)",
                      transition: "all 0.5s ease",
                      boxShadow: `0 0 ${emojiSize/6}px ${emojiSize/20}px ${
                        eyeColor === "yellow" ? "rgba(255, 255, 0, 1)" : 
                        eyeColor === "red" ? "rgba(255, 0, 0, 1)" : 
                        eyeColor === "green" ? "rgba(0, 255, 0, 1)" : 
                        "rgba(80, 190, 220, 1)"
                      }`
                    }}
                  >
                    <div
                      style={{
                        fontSize: `${emojiSize * 0.6}px`,
                        filter: "drop-shadow(0 0 15px rgba(80, 190, 220, 0.8))",
                        animation: `${threatDetected ? "pulse 0.5s infinite" : "pulse 3s infinite"}`,
                      }}
                    >
                      {currentEmoji || emotionEmoji[currentEmotion]}
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 text-xs text-white bg-black/50 text-center py-1">
                      {eyeColor}
                    </div>
                  </div>

                  {/* Status message */}
                  <div className={`mt-8 text-2xl text-center glow-text ${threatDetected ? "text-red-400" : "text-[#50bedc]"}`}>
                    {statusMessage}
                  </div>

                  {/* Recognized person */}
                  {recognizedPerson && (
                    <div className="mt-4 text-xl text-center text-green-400">
                      {recognizedPerson}
                    </div>
                  )}

                  {/* 啟動監視模式的按鈕 */}
                  {!hasSentCommandRef.current && (
                    <div className="mt-8">
                      <Button 
                        className="bg-green-700 hover:bg-green-800 text-white p-4 h-16"
                        onClick={startSurveillanceMode}
                      >
                        <div className="flex items-center justify-center w-full">
                          <Play className="h-6 w-6 mr-2" />
                          <span className="text-lg">啟動監視模式</span>
                        </div>
                      </Button>
                    </div>
                  )}
                  
                  {/* 結束監視模式的按鈕 */}
                  {hasSentCommandRef.current && (
                    <div className="mt-8">
                      <Button 
                        className="bg-red-700 hover:bg-red-800 text-white p-4 h-16"
                        onClick={stopSurveillanceMode}
                      >
                        <div className="flex items-center justify-center w-full">
                          <Square className="h-6 w-6 mr-2" />
                          <span className="text-lg">結束監視模式</span>
                        </div>
                      </Button>
                    </div>
                  )}

                  {/* Security level indicator 已移除 */}
                </div>
              </div>
            </div>
        </div>
      </main>
    </div>
  )
}
