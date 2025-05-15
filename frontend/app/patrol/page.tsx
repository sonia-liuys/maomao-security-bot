"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Power,
  Video,
  VideoOff,
  Scan,
  Play,
  Square,
  RotateCw
} from "lucide-react"
import Navigation from "@/components/navigation"
import useRobotConnection from "@/hooks/useRobotConnection"

export default function PatrolMode() {
  const [videoActive, setVideoActive] = useState(true)
  const [isPatrolling, setIsPatrolling] = useState(false)
  const [statusMessage, setStatusMessage] = useState("準備開始巡邏")
  const { isConnected, setRobotMode, sendCommand, lastMessage, robotStatus } = useRobotConnection()
  const [hasSentCommandRef, setHasSentCommandRef] = useState(false)

  // 切換到巡邏模式
  useEffect(() => {
    if (isConnected && !hasSentCommandRef) {
      console.log("已連接到機器人");
      // 不再自動切換到巡邏模式，等待用戶點擊按鈕
    }
  }, [isConnected, hasSentCommandRef]);

  // 啟動巡邏模式
  const startPatrolMode = () => {
    try {
      console.log("切換到巡邏模式");
      // 切換到巡邏模式
      setRobotMode("PATROL");
      setHasSentCommandRef(true);
      setStatusMessage("巡邏模式已啟動");
    } catch (error) {
      console.error("設置模式失敗:", error);
    }
  };
  
  // 結束巡邏模式
  const stopPatrolMode = () => {
    try {
      console.log("結束巡邏模式");
      // 先停止巡邏如果正在巡邏中
      if (isPatrolling) {
        sendCommand({
          type: 'stop_patrol',
          data: {}
        });
      }
      
      // 切換到闲置模式
      setRobotMode("IDLE");
      setHasSentCommandRef(false);
      setIsPatrolling(false);
      setStatusMessage("巡邏模式已停止");
    } catch (error) {
      console.error("停止模式失敗:", error);
    }
  };

  // 監聽最後收到的消息
  useEffect(() => {
    if (!lastMessage) return;
    
    try {
      // 檢查是否是巡邏狀態更新消息
      const message = lastMessage as { type: string; data: any };
      if (message && message.type === 'status_update') {
        const data = message.data;
        if (data && data.patrol_active !== undefined) {
          setIsPatrolling(data.patrol_active);
          setStatusMessage(data.patrol_active ? "正在巡邏中..." : "巡邏已停止");
        }
      }
    } catch (error) {
      console.error('處理消息時出錯:', error);
    }
  }, [lastMessage]);

  const togglePatrol = () => {
    if (isPatrolling) {
      // 停止巡邏
      sendCommand({
        type: 'stop_patrol',
        data: {}
      });
      setStatusMessage("正在停止巡邏...");
    } else {
      // 開始巡邏
      sendCommand({
        type: 'start_patrol',
        data: {}
      });
      setStatusMessage("正在啟動巡邏...");
    }
    // 預先更新UI狀態以提供即時反饋
    setIsPatrolling(!isPatrolling);
  };
  
  // 暫停巡邏功能
  const pausePatrol = () => {
    // 發送暫停巡邏命令
    sendCommand({
      type: 'stop_patrol',
      data: {}
    });
    setIsPatrolling(false);
    setStatusMessage("巡邏已暫停");
  };

  const toggleCamera = () => {
    setVideoActive(!videoActive);
    if (!videoActive) {
      sendCommand({
        type: "start_video_stream",
        data: {}
      });
    } else {
      sendCommand({
        type: "stop_video_stream",
        data: {}
      });
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 bg-[#050a10] text-white grid-bg">
      <Navigation />
      <Card className="w-full max-w-2xl bg-[#0a1520] border-[#50bedc]/30 p-6 flex flex-col mt-4">
        <div className="flex justify-between items-center mb-4">
          <div className="text-[#50bedc] text-lg">巡邏模式</div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={toggleCamera} className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              {videoActive ? <Video className="h-4 w-4" /> : <VideoOff className="h-4 w-4" />}
              <span className="sr-only">{videoActive ? "關閉" : "開啟"}攝像頭</span>
            </Button>
          </div>
        </div>

        {/* 狀態顯示 */}
        <div className="mb-6 p-4 bg-[#0a1520] border border-[#50bedc]/30 rounded-md">
          <div className="text-[#50bedc] text-sm mb-2">狀態</div>
          <div className="text-white">{statusMessage}</div>
          <div className="mt-2 flex items-center">
            <div className={`h-2 w-2 rounded-full ${isPatrolling ? "bg-green-500 animate-pulse" : "bg-gray-500"} mr-2`}></div>
            <span className="text-xs text-gray-400">{isPatrolling ? "巡邏中" : "已停止"}</span>
          </div>
        </div>

        {/* 巡邏控制按鈕 */}
        <div className="grid grid-cols-1 gap-4 mb-4">
          {!hasSentCommandRef ? (
            <Button 
              className="bg-green-700 hover:bg-green-800 text-white p-4 h-16"
              onClick={startPatrolMode}
            >
              <div className="flex items-center justify-center w-full">
                <Play className="h-6 w-6 mr-2" />
                <span className="text-lg">啟動巡邏模式</span>
              </div>
            </Button>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {/* 開始/停止巡邏按鈕 */}
              <Button 
                className={`${isPatrolling ? 'bg-orange-600 hover:bg-orange-700' : 'bg-green-700 hover:bg-green-800'} text-white p-4 h-16`}
                onClick={isPatrolling ? pausePatrol : togglePatrol}
              >
                <div className="flex items-center justify-center w-full">
                  {isPatrolling ? (
                    <>
                      <Square className="h-6 w-6 mr-2" />
                      <span className="text-lg">暫停巡邏</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-6 w-6 mr-2" />
                      <span className="text-lg">開始巡邏</span>
                    </>
                  )}
                </div>
              </Button>
              
              {/* 結束巡邏模式按鈕 */}
              <Button 
                className="bg-red-700 hover:bg-red-800 text-white p-4 h-12 mt-2"
                onClick={stopPatrolMode}
              >
                <div className="flex items-center justify-center w-full">
                  <Square className="h-4 w-4 mr-2" />
                  <span className="text-md">結束巡邏模式</span>
                </div>
              </Button>
            </div>
          )}
        </div>

        {/* 其他控制按鈕 */}
        <div className="grid grid-cols-2 gap-4">
          <Button className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] p-3">
            <div className="flex flex-col items-center">
              <RotateCw className="h-5 w-5 mb-1" />
              <span className="text-sm">旋轉巡邏</span>
            </div>
          </Button>
          
          <Button className="bg-[#1a1520] hover:bg-[#251520] text-red-400 border-red-500/30 p-3">
            <div className="flex flex-col items-center">
              <Power className="h-5 w-5 mb-1" />
              <span className="text-sm">關閉電源</span>
            </div>
          </Button>
        </div>
      </Card>
    </main>
  )
}
