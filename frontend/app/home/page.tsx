"use client"

import { useState, useEffect, useRef } from "react"
import { Clock, Radar } from "lucide-react"
import Navigation from "@/components/navigation"
import BatteryIndicator from "@/components/battery-indicator"
import useRobotConnection from "@/hooks/useRobotConnection"
import RadarDisplay from "@/components/radar-display"

export default function PatrolMode() {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [radarSize, setRadarSize] = useState(350) // 默認雷達大小
  
  const { isConnected, setRobotMode } = useRobotConnection()
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

  return (
    <main className="flex min-h-screen flex-col bg-black text-white">
      <Navigation />

      {/* 頂部狀態欄已移除 */}

      {/* 全螢幕雷達區域 */}
      <div className="flex-grow flex items-center justify-center bg-black">
        <RadarDisplay 
          size={radarSize} 
          scanSpeed={1.8} 
          dotCount={20} 
        />
      </div>

      {/* 底部狀態欄已移除 */}
    </main>
  )
}
