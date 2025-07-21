"use client"

import { useState, useRef, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Power,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Video,
  VideoOff,
  Maximize,
  Minimize,
  RotateCw,
  ThumbsUp,
  ThumbsDown,
  Eye,
  EyeOff,
  Square,
  AlertTriangle,
  Bell
} from "lucide-react"
import Navigation from "@/components/navigation"
import useRobotConnection from "@/hooks/useRobotConnection"

// 定義消息類型介面
interface RobotMessage {
  type: string;
  data?: {
    image?: string;
    timestamp?: number;
    width?: number;
    height?: number;
    alarm_active?: boolean;
    eye_color?: string;
    message?: string;
    recognized_person?: string;
    confidence?: number;
    emoji?: string;
    face_detected?: boolean;
    face_x?: number;
    face_y?: number;
    [key: string]: any;
  };
  id?: string;
}

export default function RemoteMode() {
  const [videoActive, setVideoActive] = useState(true)
  const [zoomLevel, setZoomLevel] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [handsUp, setHandsUp] = useState(false)
  const [eyesOpen, setEyesOpen] = useState(true)
  const [alarmActive, setAlarmActive] = useState(false)
  const [statusMessage, setStatusMessage] = useState("Ready to assist")
  const [faceDetectionActive, setFaceDetectionActive] = useState(false)
  const [laserActive, setLaserActive] = useState(false)
  const [patrolActive, setPatrolActive] = useState(false)
  const [currentMode, setCurrentMode] = useState("MANUAL")
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  const { isConnected, setRobotMode, sendCommand, lastMessage, robotStatus } = useRobotConnection()
  // 將lastMessage轉換為RobotMessage類型
  const typedLastMessage = lastMessage as RobotMessage | null
  // 使用ref追蹤是否已經發送過命令
  const hasSentCommandRef = useRef(false)
  
  // Start video stream if needed, but don't change the robot mode
  useEffect(() => {
    if (isConnected && !hasSentCommandRef.current) {
      const timer = setTimeout(() => {
        try {
          // No longer auto-switch to manual mode, preserving current mode
          console.log("Connected to robot in Remote Control page");
          
          // Only start the video stream if needed
          if (videoActive) {
            sendCommand({
              type: "start_video_stream",
              data: {}
            });
          }
          
          hasSentCommandRef.current = true;
        } catch (error) {
          console.error("Failed to start video stream:", error);
        }
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isConnected, videoActive, sendCommand])
  
  // 監聽最後收到的消息，檢查警報狀態和更新當前模式
  useEffect(() => {
    if (!lastMessage) return;
    
    try {
      const message = lastMessage as RobotMessage;
      
      if (message.type === 'status_update' && message.data) {
        // 更新警報狀態
        if (message.data.alarm_active !== undefined) {
          setAlarmActive(message.data.alarm_active);
        }
        
        // 更新當前模式
        if (message.data.mode) {
          setCurrentMode(message.data.mode);
        }
      }
      
      if (message.type === 'recognition_result' && message.data && message.data.eye_color === 'red') {
        setAlarmActive(true);
      }
    } catch (error) {
      console.error('處理消息時出錯:', error);
    }
  }, [lastMessage]);
  
  // 處理模式切換
  const handleModeChange = (value: string) => {
    setRobotMode(value);
    setStatusMessage(`Switching to ${value} mode...`);
    setCurrentMode(value);
  };
  
  // 處理圖像加載
  const handleImageLoad = (image: HTMLImageElement, canvas: HTMLCanvasElement) => {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    canvas.width = image.width;
    canvas.height = image.height;
    
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.scale(zoomLevel, zoomLevel);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);
    
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    
    if (typedLastMessage && 
        typedLastMessage.data && 
        typedLastMessage.data.face_detected && 
        typedLastMessage.data.face_x !== undefined && 
        typedLastMessage.data.face_y !== undefined) {
      
      const faceX = typedLastMessage.data.face_x * canvas.width;
      const faceY = typedLastMessage.data.face_y * canvas.height;
      const faceSize = canvas.width * 0.15;
      
      ctx.strokeStyle = 'rgba(80, 190, 220, 0.8)';
      ctx.lineWidth = 2;
      ctx.strokeRect(faceX - faceSize/2, faceY - faceSize/2, faceSize, faceSize);
      
      if (typedLastMessage.data.recognized_person) {
        ctx.fillStyle = 'rgba(10, 21, 32, 0.7)';
        ctx.fillRect(faceX - faceSize/2, faceY + faceSize/2, faceSize, 20);
        
        ctx.fillStyle = 'rgb(80, 190, 220)';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(
          `${typedLastMessage.data.recognized_person} (${Math.round((typedLastMessage.data.confidence || 0) * 100)}%)`, 
          faceX, 
          faceY + faceSize/2 + 14
        );
      }
    }
    
    ctx.restore();
  };
  
  // 處理視頻幀
  useEffect(() => {
    if (!typedLastMessage || !typedLastMessage.data || typedLastMessage.type !== 'video_frame') {
      return;
    }
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    try {
      const imageData = typedLastMessage.data.image;
      if (!imageData) return;
      
      const image = new Image();
      image.onload = () => handleImageLoad(image, canvas);
      image.onerror = (err) => console.error('圖像加載錯誤:', err);
      image.src = `data:image/jpeg;base64,${imageData}`;
    } catch (error) {
      console.error('處理視頻幀時出錯:', error);
    }
  }, [typedLastMessage, zoomLevel, rotation]);
  
  // UI 控制函數
  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.1, 2.0));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.1, 0.5));
  const handleRotate = () => setRotation(prev => (prev + 90) % 360);
  const toggleCamera = () => setVideoActive(!videoActive);
  
  const handleRaiseHand = () => {
    setHandsUp(true);
    sendCommand({
      type: "servo",
      data: { id: "arms", position: "up" }
    });
  };
  
  const handleLowerHand = () => {
    setHandsUp(false);
    sendCommand({
      type: "servo",
      data: { id: "arms", position: "down" }
    });
  };
  
  const handleOpenEyes = () => {
    setEyesOpen(true);
    sendCommand({
      type: "servo",
      data: { id: "eyes", position: "open" }
    });
  };
  
  const handleCloseEyes = () => {
    setEyesOpen(false);
    sendCommand({
      type: "servo",
      data: { id: "eyes", position: "closed" }
    });
  };
  
  const handleClearAlarm = () => {
    sendCommand({
      type: 'clear_alarm',
      data: {}
    });
    setAlarmActive(false);
    setStatusMessage('警報已解除');
  }

  const handlePowerOff = () => {
    setStatusMessage("Powering off...")
  }
  
  // 觸發警報模式
  const handleAlarmMode = () => {
    sendCommand({
      type: "trigger_alarm_mode",
      data: {}
    });
    setAlarmActive(true);
    setStatusMessage('已啟動警報模式！');
  }

  // 處理移動命令
  const handleMove = (direction: string) => {
    sendCommand({
      type: "move",
      data: {
        direction: direction,
        continuous: true
      }
    });
  };

  // 處理停止移動命令
  const handleStop = () => {
    sendCommand({
      type: "stop",
      data: {}
    });
  };

  // 處理雷射開關
  const toggleLaser = () => {
    const newState = !laserActive;
    setLaserActive(newState);
    sendCommand({
      type: newState ? "activate_laser" : "deactivate_laser",
      data: {}
    });
  };
  
  // 處理巡邏模式開關
  const togglePatrol = () => {
    const newState = !patrolActive;
    setPatrolActive(newState);
    sendCommand({
      type: "patrol",
      data: {
        action: newState ? "start" : "stop"
      }
    });
  };

  // Set eye color
  const setEyeColor = (color: string) => {
    sendCommand({
      type: "set_eye_color",
      data: { color: color }
    });
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 bg-[#050a10] text-white grid-bg">
      <Navigation />
      <Card className="w-full max-w-3xl bg-[#0a1520] border-[#50bedc]/30 p-4 flex flex-col mt-4">
        {/* Mode selector and status */}
        <div className="flex justify-between items-center mb-4 bg-[#0c1c2c] p-2 rounded-md border border-[#50bedc]/20">
          <div className="flex-1">
            <div className="text-[#50bedc] text-xs mb-1">ROBOT MODE</div>
            <Select value={currentMode} onValueChange={handleModeChange}>
              <SelectTrigger className="w-full bg-[#0a1520] border-[#50bedc]/30 h-8 text-sm">
                <SelectValue placeholder="Select mode" />
              </SelectTrigger>
              <SelectContent className="bg-[#0a1520] border-[#50bedc]/30">
                <SelectItem value="MANUAL" className="text-white hover:bg-[#152535]">Manual Control</SelectItem>
                <SelectItem value="SURVEILLANCE" className="text-white hover:bg-[#152535]">Security Surveillance</SelectItem>
                <SelectItem value="PATROL" className="text-white hover:bg-[#152535]">Patrol Mode</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="ml-4 text-xs">
            <div className="text-[#50bedc]">STATUS</div>
            <div className={`mt-1 px-2 py-1 rounded text-center ${alarmActive ? 'bg-red-900/50 text-red-300' : 'bg-green-900/50 text-green-300'}`}>
              {alarmActive ? 'ALARM ACTIVE' : statusMessage}
            </div>
          </div>
        </div>
        
        {/* 頂部控制欄 */}
        <div className="flex justify-between items-center mb-2">
          <div className="text-[#50bedc] text-xs">CAMERA FEED</div>
          <div className="flex gap-1">
            <Button variant="outline" size="icon" onClick={toggleCamera} className="h-6 w-6 border-[#50bedc]/30 text-[#50bedc] p-1">
              {videoActive ? <Video className="h-3 w-3" /> : <VideoOff className="h-3 w-3" />}
            </Button>
            <Button variant="outline" size="icon" onClick={handleZoomIn} className="h-6 w-6 border-[#50bedc]/30 text-[#50bedc] p-1">
              <Maximize className="h-3 w-3" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleZoomOut} className="h-6 w-6 border-[#50bedc]/30 text-[#50bedc] p-1">
              <Minimize className="h-3 w-3" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleRotate} className="h-6 w-6 border-[#50bedc]/30 text-[#50bedc] p-1">
              <RotateCw className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Video feed */}
        <div className="relative flex-1 mb-3 bg-black/20 rounded-md overflow-hidden h-[420px]">
          {alarmActive && (
            <div className="absolute inset-0 border-4 border-red-500 animate-pulse rounded-md z-10"></div>
          )}
          <canvas 
            ref={canvasRef} 
            className="w-full h-full object-contain"
          />
          <div className="absolute top-2 right-2 flex items-center space-x-1">
            <div className={`h-2 w-2 rounded-full ${videoActive ? "bg-red-500 animate-pulse" : "bg-gray-500"}`}></div>
            <span className={`text-xs ${videoActive ? "text-red-400" : "text-gray-400"}`}>
              {videoActive ? "REC" : "OFF"}
            </span>
          </div>
        </div>

        {/* 控制面板 - 使用更緊湊的布局 */}
        <div className="grid grid-cols-2 gap-2">
          {/* 左側：移動控制 */}
          <div className="grid grid-cols-3 gap-1">
            <div></div>
            <Button 
              size="sm"
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] h-8"
              onClick={() => handleMove("forward")}
            >
              <ArrowUp className="h-4 w-4" />
            </Button>
            <div></div>

            <Button 
              size="sm"
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] h-8"
              onClick={() => handleMove("left")}
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <Button 
              size="sm"
              className="bg-red-600 hover:bg-red-700 text-white h-8"
              onClick={handleStop}
            >
              <Square className="h-4 w-4" />
            </Button>
            <Button 
              size="sm"
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] h-8"
              onClick={() => handleMove("right")}
            >
              <ArrowRight className="h-4 w-4" />
            </Button>

            <div></div>
            <Button 
              size="sm"
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] h-8"
              onClick={() => handleMove("backward")}
            >
              <ArrowDown className="h-4 w-4" />
            </Button>
            <div></div>
          </div>

          {/* 右側：功能按鈕和狀態控制 */}
          <div>
            {/* Eye Color Control */}
            <div className="mb-2">
              <div className="flex items-center mb-1">
                <span className="text-[#50bedc] text-xs mr-2">Eye Color:</span>
                <div className="flex gap-1 flex-1">
                  <Button 
                    size="sm"
                    className="bg-red-600 hover:bg-red-700 h-6 flex-1 p-0"
                    onClick={() => setEyeColor("red")}
                  ></Button>
                  <Button 
                    size="sm"
                    className="bg-yellow-500 hover:bg-yellow-600 h-6 flex-1 p-0"
                    onClick={() => setEyeColor("yellow")}
                  ></Button>
                  <Button 
                    size="sm"
                    className="bg-blue-600 hover:bg-blue-700 h-6 flex-1 p-0"
                    onClick={() => setEyeColor("blue")}
                  ></Button>
                  <Button 
                    size="sm"
                    className="bg-green-600 hover:bg-green-700 h-6 flex-1 p-0"
                    onClick={() => setEyeColor("green")}
                  ></Button>
                </div>
              </div>
            </div>

            {/* 雷射開關 */}
            <div className="mb-2">
              <Button 
                size="sm"
                className={`w-full h-8 ${laserActive ? 'bg-red-600 hover:bg-red-700' : 'bg-[#0a1520] hover:bg-[#152535] text-[#50bedc]'}`}
                onClick={toggleLaser}
              >
                {laserActive ? 'Disable Laser' : 'Enable Laser'}
              </Button>
            </div>
            
            {/* 巡邏模式開關 */}
            <div className="mb-2">
              <Button 
                size="sm"
                className={`w-full h-8 ${patrolActive ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-[#0a1520] hover:bg-[#152535] text-[#50bedc]'}`}
                onClick={togglePatrol}
              >
                {patrolActive ? 'Stop Patrol' : 'Start Patrol'}
              </Button>
            </div>
            
            {/* 警報模式按鈕 */}
            <div className="mb-2">
              <Button 
                size="sm"
                className={`w-full h-8 bg-red-600 hover:bg-red-700 text-white`}
                onClick={handleAlarmMode}
              >
                <div className="flex items-center justify-center w-full">
                  <Bell className="h-4 w-4 mr-1" />
                  <span>Trigger Alarm Mode</span>
                </div>
              </Button>
            </div>

            {/* 其他功能按鈕 */}
            <div className="grid grid-cols-4 gap-1">
              <Button
                size="sm"
                className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] p-1 h-8"
                onClick={handleRaiseHand}
              >
                <ThumbsUp className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] p-1 h-8"
                onClick={handleLowerHand}
              >
                <ThumbsDown className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] p-1 h-8"
                onClick={handleOpenEyes}
              >
                <Eye className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] p-1 h-8"
                onClick={handleCloseEyes}
              >
                <EyeOff className="h-4 w-4" />
              </Button>
              
              <Button 
                size="sm"
                className={`${alarmActive ? 'bg-[#251520] hover:bg-[#352530] text-red-400' : 'bg-[#0a1520] hover:bg-[#152535] text-[#50bedc]'} p-1 h-8 col-span-2`}
                onClick={handleClearAlarm}
                disabled={!alarmActive}
              >
                <div className="flex items-center">
                  <AlertTriangle className={`h-4 w-4 mr-1 ${alarmActive ? 'animate-pulse' : ''}`} />
                  <span className="text-xs">{alarmActive ? 'Clear Alarm' : 'No Alarm'}</span>
                </div>
              </Button>

              <Button
                size="sm"
                className="bg-[#1a1520] hover:bg-[#251520] text-red-400 border-red-500/30 p-1 h-8 col-span-2"
                onClick={handlePowerOff}
              >
                <div className="flex items-center">
                  <Power className="h-4 w-4 mr-1" />
                  <span className="text-xs">Power</span>
                </div>
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </main>
  )
}
