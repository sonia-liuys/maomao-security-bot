"use client"

import { useState, useEffect, useRef } from "react"
import { Clock, Radar, Play } from "lucide-react"
import Navigation from "@/components/navigation"
import BatteryIndicator from "@/components/battery-indicator"
import useRobotConnection from "@/hooks/useRobotConnection"
import RadarDisplay from "@/components/radar-display"
import { Button } from "@/components/ui/button"

export default function PatrolMode() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [radarSize, setRadarSize] = useState(350) // 默認雷達大小
  const [patrolStarted, setPatrolStarted] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  
  const { isConnected, setRobotMode, sendCommand } = useRobotConnection()
  // 使用ref追蹤是否已經發送過命令
  const hasSentCommandRef = useRef(false)
  
  // 切換到巡邏模式
  useEffect(() => {
    // 如果連接已建立且尚未發送過命令
    if (isConnected && !hasSentCommandRef.current) {
      // 添加延遲，確保連接已完全建立
      const timer = setTimeout(() => {
        try {
          setRobotMode("PATROL");
          console.log("切換到巡邏模式");
          hasSentCommandRef.current = true;
        } catch (error) {
          console.error("設置模式失敗:", error);
        }
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isConnected, setRobotMode])
  
  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])
  
  // 處理窗口大小變化，調整雷達大小
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const handleResize = () => {
        const newSize = Math.min(window.innerWidth * 0.85, window.innerHeight * 0.7)
        setRadarSize(newSize)
      }
      
      // 初始設置
      handleResize()
      
      // 添加窗口大小變化監聽
      window.addEventListener('resize', handleResize)
      
      return () => {
        window.removeEventListener('resize', handleResize)
      }
    }
  }, [])

  // 格式化時間
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  // 處理開始巡邏按鈕點擊
  const handleStartPatrol = () => {
    if (isStarting || patrolStarted) return;
    
    setIsStarting(true);
    
    // 發送開始巡邏命令
    const success = sendCommand({
      type: "start_patrol",
      data: {}
    });
    
    if (success) {
      console.log("巡邏已開始");
      setPatrolStarted(true);
    } else {
      console.error("無法開始巡邏");
    }
    
    setIsStarting(false);
  };

  return (
    <main className="flex min-h-screen flex-col bg-black text-white">
      <Navigation />

      {/* 頂部狀態欄 */}
      <div className="flex justify-between items-center p-4 bg-[#0a1520]/50">
        <div className="text-[#50bedc] text-sm">
          {formatTime(currentTime)}
        </div>
        <div className="text-[#50bedc] text-sm">
          {patrolStarted ? "巡邏中 / Patrolling" : "待命中 / Standby"}
        </div>
      </div>

      {/* 全螢幕雷達區域 */}
      <div className="flex-grow flex items-center justify-center bg-black relative">
        <RadarDisplay 
          size={radarSize} 
          scanSpeed={patrolStarted ? 2.5 : 1.8} 
          dotCount={20} 
        />
        
        {/* 開始巡邏按鈕 */}
        <div className="absolute bottom-8 left-0 right-0 flex justify-center">
          <Button
            onClick={handleStartPatrol}
            disabled={isStarting || patrolStarted}
            className={`bg-[#50bedc] hover:bg-[#3a9db8] text-black font-bold py-3 px-6 rounded-full flex items-center gap-2 ${patrolStarted ? 'opacity-50' : 'opacity-100'}`}
          >
            <Play className="h-5 w-5" />
            {isStarting ? "啟動中..." : patrolStarted ? "巡邏中" : "開始巡邏"}
          </Button>
        </div>
      </div>

      {/* 底部狀態欄 */}
      <div className="p-4 bg-[#0a1520]/50 flex justify-between items-center">
        <div className="text-[#50bedc] text-xs">
          系統狀態: {isConnected ? "已連接" : "未連接"}
        </div>
        <div className="text-[#50bedc] text-xs">
          MaoMao Security v1.0
        </div>
      </div>
    </main>
  )
}
