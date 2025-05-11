"use client"

import { useState, useRef, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
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
  HandMetal,
  Eye,
  EyeOff,
  Clock,
  Scan,
  User,
  Square,
  Zap,
  ZapOff,
  Palette
} from "lucide-react"
import Navigation from "@/components/navigation"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import useRobotConnection from "@/hooks/useRobotConnection"
import { AlertTriangle } from "lucide-react"

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
  const [currentEyeColor, setCurrentEyeColor] = useState("green")
  const [isMoving, setIsMoving] = useState(false)
  const [movementDirection, setMovementDirection] = useState("") // "forward", "backward", "left", "right"
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  const { isConnected, setRobotMode, sendCommand, lastMessage, robotStatus } = useRobotConnection()
  // 將lastMessage轉換為RobotMessage類型
  const typedLastMessage = lastMessage as RobotMessage | null
  // 使用ref追蹤是否已經發送過命令
  const hasSentCommandRef = useRef(false)
  
  // 切換到手動模式並啟動視頻流
  useEffect(() => {
    console.log("連接狀態:", isConnected, "是否已發送命令:", hasSentCommandRef.current);
    
    // 如果連接已建立且尚未發送過命令
    if (isConnected && !hasSentCommandRef.current) {
      console.log("準備發送命令...");
      
      // 添加延遲，確保連接已完全建立
      const timer = setTimeout(() => {
        try {
          console.log("開始發送命令");
          
          // 切換到手動模式
          setRobotMode("MANUAL");
          console.log("切換到手動模式");
          
          // 啟動視頻流
          if (videoActive) {
            console.log("發送啟動視頻流命令");
            const result = sendCommand({
              type: "start_video_stream",
              data: {}
            });
            console.log("視頻流命令發送結果:", result);
          } else {
            console.log("視頻未啟用，不發送視頻流命令");
          }
          
          hasSentCommandRef.current = true;
          console.log("命令已發送標記已設置");
        } catch (error) {
          console.error("設置模式失敗:", error);
        }
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isConnected, setRobotMode, videoActive, sendCommand])
  
  // 監聽最後收到的消息，檢查警報狀態

  useEffect(() => {
    if (!lastMessage) return;
    
    try {
      // 使用類型斷言來確保 TypeScript 知道 lastMessage 的類型
      const message = lastMessage as RobotMessage;
      
      // 檢查是否是狀態更新消息
      if (message.type === 'status_update' && message.data && message.data.alarm_active !== undefined) {
        setAlarmActive(message.data.alarm_active);
        console.log(`警報狀態更新: ${message.data.alarm_active ? '活躍' : '非活躍'}`);
      }
      
      // 檢查是否是識別結果消息，並且眼睛顏色為紅色
      if (message.type === 'recognition_result' && 
          message.data && 
          message.data.eye_color === 'red') {
        setAlarmActive(true);
        console.log('收到紅色警報狀態');
      }
    } catch (error) {
      console.error('處理消息時出錯:', error);
    }
  }, [lastMessage])

  // 處理視頻流
  useEffect(() => {
    console.log("視頻流效果觸發，狀態:", {
      videoActive,
      isConnected,
      canvasExists: !!canvasRef.current
    });
    
    if (!canvasRef.current || !videoActive) {
      console.log("視頻流初始化跳過: ", !canvasRef.current ? "canvas不存在" : "視頻未啟用");
      return;
    }

    if (!isConnected) {
      console.log("視頻流初始化跳過: WebSocket未連接");
      return;
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) {
      console.error("無法獲取canvas上下文");
      return;
    }

    // 初始化畫布，顯示等待連接的訊息
    ctx.fillStyle = "#0a1520";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = "14px sans-serif";
    ctx.fillStyle = "#40a0ff";
    ctx.textAlign = "center";
    ctx.fillText("正在連接視頻流...", canvas.width / 2, canvas.height / 2);
    ctx.fillText("Connecting to video stream...", canvas.width / 2, canvas.height / 2 + 20);

    // 如果已連接，發送開始視頻流命令
    console.log("準備發送開始視頻流命令，連接狀態:", isConnected ? "已連接" : "未連接");
    
    // 直接發送一次視頻流命令，不等待
    try {
      console.log("立即發送視頻流命令");
      const immediateResult = sendCommand({
        type: "start_video_stream",
        data: {}
      });
      console.log("立即發送視頻流命令結果:", immediateResult);
    } catch (error) {
      console.error("立即發送視頻流命令失敗:", error);
    }
    
    // 添加延遲，確保連接已穩定，再發送一次
    const timer = setTimeout(() => {
      console.log("延遲後發送視頻流命令，連接狀態:", isConnected ? "已連接" : "未連接");
      if (!isConnected) {
        console.error("無法發送視頻流命令: WebSocket未連接");
        return;
      }
      
      try {
        const result = sendCommand({
          type: "start_video_stream",
          data: {}
        });
        console.log("延遲後視頻流命令已發送，結果:", result);
      } catch (innerError) {
        console.error("延遲後發送視頻流命令失敗:", innerError);
      }
    }, 2000);  // 延遲兩秒發送，給更多時間建立連接
    
    // 清理函數 - 停止視頻流
    return () => {
      console.log("清理視頻流效果");
      clearTimeout(timer);
      if (isConnected) {
        console.log("發送停止視頻流命令");
        try {
          sendCommand({
            type: "stop_video_stream",
            data: {}
          });
        } catch (error) {
          console.error("發送停止視頻流命令失敗:", error);
        }
      }
    };
  }, [videoActive, isConnected, sendCommand])

  // 處理視頻幀消息
  useEffect(() => {
    // 記錄詳細日誌，包含人臉識別資訊
    if (process.env.NODE_ENV === 'development') {
      console.log("視頻幀處理效果觸發，狀態:", {
        videoActive,
        hasCanvas: !!canvasRef.current,
        hasLastMessage: !!lastMessage,
        messageType: lastMessage ? typeof lastMessage : 'none',
        faceDetectionActive,
      });
      
      // 檢查是否收到人臉識別數據
      if (lastMessage && typeof lastMessage === 'object') {
        const msgObj = lastMessage as RobotMessage;
        const msgData = msgObj.data || {};
        console.log("[DEBUG] 人臉識別數據檢查:", { 
          face_detected: msgData.face_detected, 
          face_x: msgData.face_x, 
          face_y: msgData.face_y,
          recognized_person: msgData.recognized_person
        });
      }
    }
    
    // 檢查必要條件
    if (!canvasRef.current || !videoActive) {
      return;
    }
    
    if (!lastMessage) {
      return;
    }
    
    // 解析消息
    let messageType = '';
    let messageData = null;
    
    try {
      // 如果是字符串，嘗試解析JSON
      if (typeof lastMessage === 'string') {
        // 使用明確的字符串類型斷言
        const messageStr: string = lastMessage;
        const parsedMessage = JSON.parse(messageStr) as RobotMessage;
        messageType = parsedMessage.type || '';
        messageData = parsedMessage.data || null;
      } 
      // 如果已經是對象，直接使用
      else if (typeof lastMessage === 'object' && lastMessage !== null) {
        const msgObj = lastMessage as RobotMessage;
        messageType = msgObj.type || '';
        messageData = msgObj.data || null;
      }
    } catch (error) {
      console.error("解析消息出錯:", error);
      return;
    }
    
    // 檢查是否是視頻幀消息
    if (messageType === "video_frame" && messageData && messageData.image) {
      // 獲取畫布和上下文
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        console.error("無法獲取畫布上下文");
        return;
      }

      // 創建新圖像並設置事件處理
      const img = new Image();
      
      // 設置圖像加載錯誤處理
      img.onerror = (err) => {
        console.error("圖像加載失敗:", err);
        // 顯示錯誤信息
        ctx.fillStyle = "#0a1520";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.font = "14px sans-serif";
        ctx.fillStyle = "#ff4040";
        ctx.textAlign = "center";
        ctx.fillText("視頻幀加載失敗", canvas.width / 2, canvas.height / 2);
        ctx.fillText("Video frame loading failed", canvas.width / 2, canvas.height / 2 + 20);
      };
      
      img.onload = () => {
        // 清除畫布
        ctx.fillStyle = "#0a1520";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // 應用縮放
        const scaledWidth = img.width * zoomLevel;
        const scaledHeight = img.height * zoomLevel;
        
        // 計算圖像在畫布中的位置，保持縱橫比
        const imgRatio = scaledWidth / scaledHeight;
        const canvasRatio = canvas.width / canvas.height;
        let drawWidth, drawHeight, drawX, drawY;

        if (imgRatio > canvasRatio) {
          // 圖像較寬，以畫布寬度為基準
          drawWidth = canvas.width;
          drawHeight = canvas.width / imgRatio;
          drawX = 0;
          drawY = (canvas.height - drawHeight) / 2;
        } else {
          // 圖像較高，以畫布高度為基準
          drawHeight = canvas.height;
          drawWidth = canvas.height * imgRatio;
          drawX = (canvas.width - drawWidth) / 2;
          drawY = 0;
        }

        // 應用旋轉
        if (rotation !== 0) {
          // 保存當前繪圖狀態
          ctx.save();
          
          // 移動到畫布中心
          ctx.translate(canvas.width / 2, canvas.height / 2);
          
          // 旋轉畫布
          ctx.rotate(rotation * Math.PI / 180);
          
          // 繪製圖像，考慮中心點偏移
          try {
            ctx.drawImage(
              img, 
              -drawWidth / 2, 
              -drawHeight / 2, 
              drawWidth, 
              drawHeight
            );
          } catch (drawError) {
            console.error("繪製旋轉圖像時出錯:", drawError);
          }
          
          // 恢復繪圖狀態
          ctx.restore();
        } else {
          // 正常繪製圖像（無旋轉）
          try {
            ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
          } catch (drawError) {
            console.error("繪製圖像時出錯:", drawError);
          }
        }

        // 添加時間戳和狀態信息
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        ctx.font = "12px monospace";
        ctx.fillStyle = "rgba(80, 190, 220, 0.8)";
        ctx.textAlign = "left";
        ctx.fillText(timeString, 10, canvas.height - 10);

        // 添加縮放和旋轉信息
        ctx.textAlign = "right";
        ctx.fillText(`Zoom: ${zoomLevel.toFixed(1)}x | Rotation: ${rotation}°`, canvas.width - 10, canvas.height - 10);
        
        // 如果啟用了人臉識別且檢測到人臉，繪製人臉框和座標
        // 從 robotStatus 而不是 messageData 中獲取人臉座標數據
        console.log("[DEBUG] 繪製人臉框檢查 - 狀態中的數據:", { 
          faceDetectionActive, 
          robotStatus: {
            face_detected: robotStatus && 'face_detected' in robotStatus ? robotStatus.face_detected : undefined,
            face_x: robotStatus && 'face_x' in robotStatus ? robotStatus.face_x : undefined, 
            face_y: robotStatus && 'face_y' in robotStatus ? robotStatus.face_y : undefined
          }
        });
        // 使用類型斷言與可選鏈安全地訪問 robotStatus 屬性
        if (faceDetectionActive && robotStatus && 'face_detected' in robotStatus && robotStatus.face_detected === true) {
          try {
            // 獲取人臉座標（基於原始圖像的相對座標，範圍 0-1）
            // 確保在計算中是數字類型
            const faceX: number = ('face_x' in robotStatus && typeof robotStatus.face_x === 'number') ? Number(robotStatus.face_x) : 0.5;
            const faceY: number = ('face_y' in robotStatus && typeof robotStatus.face_y === 'number') ? Number(robotStatus.face_y) : 0.5;
            
            // 將相對坐標轉換為畫布上的實際坐標
            const canvasFaceX = drawX + faceX * drawWidth;
            const canvasFaceY = drawY + faceY * drawHeight;
            
            // 設置繪製樣式
            ctx.strokeStyle = "#00ff00"; // 綠色
            ctx.lineWidth = 2;
            
            // 繪製面部框（假設面部框大小固定或者根據置信度調整）
            const boxSize = Math.min(drawWidth, drawHeight) * 0.15; // 15% 的寬高
            
            // 繪製面部框
            ctx.beginPath();
            ctx.rect(
              canvasFaceX - boxSize / 2,
              canvasFaceY - boxSize / 2,
              boxSize,
              boxSize
            );
            ctx.stroke();
            
            // 繪製十字標記
            const crossSize = boxSize / 4;
            ctx.beginPath();
            ctx.moveTo(canvasFaceX - crossSize, canvasFaceY);
            ctx.lineTo(canvasFaceX + crossSize, canvasFaceY);
            ctx.moveTo(canvasFaceX, canvasFaceY - crossSize);
            ctx.lineTo(canvasFaceX, canvasFaceY + crossSize);
            ctx.stroke();
            
            // 添加座標文本
            ctx.font = "12px monospace";
            ctx.fillStyle = "#00ff00";
            ctx.textAlign = "left";
            ctx.fillText(
              `X: ${(faceX * 100).toFixed(1)}%, Y: ${(faceY * 100).toFixed(1)}%`,
              canvasFaceX + boxSize / 2 + 5,
              canvasFaceY
            );
            
            // 如果有識別出的人名，顯示在框上方
            // 使用 robotStatus 獲取已識別的人名和置信度
            if ('recognized_person' in robotStatus && robotStatus.recognized_person) {
              const confidence = 'confidence' in robotStatus && typeof robotStatus.confidence === 'number' ? 
                Number(robotStatus.confidence) : undefined;
              const confidenceText = confidence !== undefined 
                ? ` (${(confidence * 100).toFixed(0)}%)` 
                : '';
              ctx.fillText(
                `${robotStatus.recognized_person}${confidenceText}`,
                canvasFaceX - boxSize / 2,
                canvasFaceY - boxSize / 2 - 5
              );
            }
          } catch (error) {
            console.error("繪製人臉識別顯示時出錯:", error);
          }
        }
      }

      // 設置圖像源為base64編碼的圖像
      try {
        // 確保base64字符串有效
        if (typeof messageData.image === 'string' && messageData.image.length > 0) {
          const base64Str = messageData.image;
          if (base64Str.length > 10) { // 簡單的有效性檢查
            img.src = `data:image/jpeg;base64,${base64Str}`;
          } else {
            console.error("無效的Base64字符串，長度太短");
          }
        } else {
          console.error("無效的圖像數據類型");
        }
      } catch (error) {
        console.error("設置圖像源時出錯:", error);
      }
    }
  }, [lastMessage, videoActive])

  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(prev + 0.1, 2))
  }

  const handleZoomOut = () => {
    setZoomLevel((prev) => Math.max(prev - 0.1, 0.5))
  }

  const handleRotate = () => {
    setRotation((prev) => (prev + 45) % 360)
  }

  const toggleCamera = () => {
    setVideoActive(!videoActive)
    setStatusMessage(videoActive ? "Camera disabled" : "Camera enabled")
  }

  const handleRaiseHand = () => {
    setHandsUp(true)
    setStatusMessage("Hands raised")
  }
  
  const toggleFaceDetection = () => {
    setFaceDetectionActive(!faceDetectionActive)
    setStatusMessage(faceDetectionActive ? "Face detection disabled" : "Face detection enabled")
  }

  const handleLowerHand = () => {
    setHandsUp(false)
    setStatusMessage("Hands lowered")
  }

  const handleOpenEyes = () => {
    setEyesOpen(true)
    setStatusMessage("Eyes opened")
  }

  const handleCloseEyes = () => {
    setEyesOpen(false)
    setStatusMessage("Eyes closed")
  }

  const handleClearAlarm = () => {
    console.log('發送解除警報命令');
    
    // 發送解除警報命令到後端
    sendCommand({
      type: 'clear_alarm',
      data: {}
    });
    
    setAlarmActive(false);
    setStatusMessage('警報已解除');
  }

  const handlePowerOff = () => {
    setStatusMessage("Powering off...")
    // In a real app, this would trigger a shutdown sequence
  }
  
  // 雷射控制
  const toggleLaser = () => {
    const newLaserState = !laserActive;
    setLaserActive(newLaserState);
    
    // 發送命令到後端
    sendCommand({
      type: newLaserState ? 'activate_laser' : 'deactivate_laser',
      data: {}
    });
    
    setStatusMessage(newLaserState ? "雷射已啟動" : "雷射已關閉");
  }
  
  // 眼睛顏色控制
  const changeEyeColor = (color: string) => {
    setCurrentEyeColor(color);
    
    // 發送命令到後端
    sendCommand({
      type: 'set_eye_color',
      data: {
        color: color
      }
    });
    
    setStatusMessage(`眼睛顏色已設置為${color}`);
  }
  
  // 連續移動控制
  const startMoving = (direction: string) => {
    setIsMoving(true);
    setMovementDirection(direction);
    
    // 發送移動命令到後端
    sendCommand({
      type: 'move',
      data: {
        direction: direction,
        continuous: true
      }
    });
    
    setStatusMessage(`正在${getDirectionText(direction)}`);
  }
  
  const stopMoving = () => {
    if (isMoving) {
      setIsMoving(false);
      setMovementDirection("");
      
      // 發送停止命令到後端
      sendCommand({
        type: 'stop',
        data: {}
      });
      
      setStatusMessage("已停止移動");
    }
  }
  
  // 獲取方向文字描述
  const getDirectionText = (direction: string) => {
    switch(direction) {
      case 'forward': return '前進';
      case 'backward': return '後退';
      case 'left': return '左轉';
      case 'right': return '右轉';
      default: return '移動';
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-4 bg-[#050a10] text-white grid-bg">
      <Navigation />
      <Card className="w-full max-w-2xl h-[600px] bg-[#0a1520] border-[#50bedc]/30 p-6 flex flex-col mt-4">
        <div className="flex justify-between items-center mb-4">
          <div className="text-[#50bedc] text-sm">CAMERA FEED</div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={toggleCamera} className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              {videoActive ? <Video className="h-4 w-4" /> : <VideoOff className="h-4 w-4" />}
              <span className="sr-only">{videoActive ? "Disable" : "Enable"} Camera</span>
            </Button>
            <Button variant="outline" size="icon" onClick={handleZoomIn} className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              <Maximize className="h-4 w-4" />
              <span className="sr-only">Zoom In</span>
            </Button>
            <Button variant="outline" size="icon" onClick={handleZoomOut} className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              <Minimize className="h-4 w-4" />
              <span className="sr-only">Zoom Out</span>
            </Button>
            <Button variant="outline" size="icon" onClick={handleRotate} className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              <RotateCw className="h-4 w-4" />
              <span className="sr-only">Rotate</span>
            </Button>
            <Button 
              variant={faceDetectionActive ? "default" : "outline"} 
              size="icon" 
              onClick={toggleFaceDetection}
              className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              <User className="h-4 w-4" />
              <span className="sr-only">{faceDetectionActive ? "Disable" : "Enable"} Face Detection</span>
            </Button>
          </div>
        </div>

        <div className="relative flex-grow mb-4 border border-[#50bedc]/30 overflow-hidden rounded-md">
          {videoActive ? (
            <canvas ref={canvasRef} width={800} height={400} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-[#0a1520]">
              <VideoOff className="h-16 w-16 text-[#50bedc]/50" />
              <p className="text-[#50bedc]/50 absolute bottom-4 left-0 right-0 text-center">Video feed disabled</p>
            </div>
          )}

          <div className="absolute top-2 right-2 flex items-center gap-2 bg-[#0a1520]/80 px-2 py-1 rounded">
            <div className={`h-2 w-2 rounded-full ${videoActive ? "bg-red-500 animate-pulse" : "bg-gray-500"}`}></div>
            <span className={`text-xs ${videoActive ? "text-red-400" : "text-gray-400"}`}>
              {videoActive ? "REC" : "OFF"}
            </span>
          </div>
        </div>

        {/* Robot control buttons */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          {/* Original controls (smaller) */}
          <div className="grid grid-cols-3 gap-1">
            <Button
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] control-button p-1"
              onClick={handleRaiseHand}
              size="sm"
            >
              <div className="flex flex-col items-center">
                <HandMetal className="h-3 w-3 mb-1" />
                <span className="text-[10px]">Raise</span>
              </div>
            </Button>

            <Button
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] control-button p-1"
              onClick={handleLowerHand}
              size="sm"
            >
              <div className="flex flex-col items-center">
                <ArrowDown className="h-3 w-3 mb-1" />
                <span className="text-[10px]">Lower</span>
              </div>
            </Button>

            <Button
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] control-button p-1"
              onClick={handleOpenEyes}
              size="sm"
            >
              <div className="flex flex-col items-center">
                <Eye className="h-3 w-3 mb-1" />
                <span className="text-[10px]">Open</span>
              </div>
            </Button>

            <Button
              className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] control-button p-1"
              onClick={handleCloseEyes}
              size="sm"
            >
              <div className="flex flex-col items-center">
                <EyeOff className="h-3 w-3 mb-1" />
                <span className="text-[10px]">Close</span>
              </div>
            </Button>

            <Button 
              className={`${alarmActive ? 'bg-[#251520] hover:bg-[#352530] text-red-400' : 'bg-[#0a1520] hover:bg-[#152535] text-[#50bedc]'} control-button p-1`}
              onClick={handleClearAlarm}
              disabled={!alarmActive}
              size="sm"
            >
              <div className="flex flex-col items-center">
                <AlertTriangle className={`h-3 w-3 mb-1 ${alarmActive ? 'animate-pulse' : ''}`} />
                <span className="text-[10px]">{alarmActive ? '解除警報' : '無警報'}</span>
              </div>
            </Button>

            <Button
              className="bg-[#1a1520] hover:bg-[#251520] text-red-400 border-red-500/30 control-button p-1"
              onClick={handlePowerOff}
              size="sm"
            >
              <div className="flex flex-col items-center">
                <Power className="h-3 w-3 mb-1" />
                <span className="text-[10px]">Power</span>
              </div>
            </Button>
          </div>

          {/* Eye color controls */}
          <div className="flex flex-col gap-2">
            <div className="text-[#50bedc] text-xs mb-1 text-center">眼睛顏色</div>
            <div className="grid grid-cols-4 gap-2">
              <Button
                className={`${currentEyeColor === 'red' ? 'bg-red-700' : 'bg-red-600'} hover:bg-red-700 text-white p-1 h-8`}
                onClick={() => changeEyeColor('red')}
              >
                <div className="flex items-center justify-center w-full">
                  <div className="h-3 w-3 rounded-full bg-red-400 mr-1"></div>
                  <span className="text-xs">紅</span>
                </div>
              </Button>

              <Button
                className={`${currentEyeColor === 'yellow' ? 'bg-yellow-700' : 'bg-yellow-600'} hover:bg-yellow-700 text-white p-1 h-8`}
                onClick={() => changeEyeColor('yellow')}
              >
                <div className="flex items-center justify-center w-full">
                  <div className="h-3 w-3 rounded-full bg-yellow-400 mr-1"></div>
                  <span className="text-xs">黃</span>
                </div>
              </Button>

              <Button
                className={`${currentEyeColor === 'blue' ? 'bg-blue-700' : 'bg-blue-600'} hover:bg-blue-700 text-white p-1 h-8`}
                onClick={() => changeEyeColor('blue')}
              >
                <div className="flex items-center justify-center w-full">
                  <div className="h-3 w-3 rounded-full bg-blue-400 mr-1"></div>
                  <span className="text-xs">藍</span>
                </div>
              </Button>

              <Button
                className={`${currentEyeColor === 'green' ? 'bg-green-700' : 'bg-green-600'} hover:bg-green-700 text-white p-1 h-8`}
                onClick={() => changeEyeColor('green')}
              >
                <div className="flex items-center justify-center w-full">
                  <div className="h-3 w-3 rounded-full bg-green-400 mr-1"></div>
                  <span className="text-xs">綠</span>
                </div>
              </Button>
            </div>

            {/* Laser control */}
            <div className="mt-2">
              <Button
                className={`${laserActive ? 'bg-red-700 hover:bg-red-800' : 'bg-[#0a1520] hover:bg-[#152535]'} text-white p-1 w-full`}
                onClick={toggleLaser}
              >
                <div className="flex items-center justify-center w-full">
                  {laserActive ? (
                    <>
                      <Zap className="h-4 w-4 mr-2 text-yellow-400" />
                      <span className="text-xs">關閉雷射</span>
                    </>
                  ) : (
                    <>
                      <ZapOff className="h-4 w-4 mr-2" />
                      <span className="text-xs">開啟雷射</span>
                    </>
                  )}
                </div>
              </Button>
            </div>
          </div>

          {/* Status display */}
          <div className="flex flex-col justify-center items-center">
            <div className="text-[#50bedc] text-xs mb-1">狀態</div>
            <div className="bg-[#0a1520] border border-[#50bedc]/30 rounded p-2 w-full h-full flex items-center justify-center">
              <p className="text-[#50bedc] text-xs text-center">{statusMessage}</p>
            </div>
          </div>
        </div>

        {/* Movement control buttons */}
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-3">
            <div className="grid grid-cols-3 gap-2">
              <div></div>
              <Button 
                className={`${movementDirection === 'forward' ? 'bg-[#152535]' : 'bg-[#0a1520]'} hover:bg-[#152535] text-[#50bedc] control-button`}
                onClick={() => startMoving('forward')}
              >
                <ArrowUp className="h-5 w-5" />
              </Button>
              <div></div>

              <Button 
                className={`${movementDirection === 'left' ? 'bg-[#152535]' : 'bg-[#0a1520]'} hover:bg-[#152535] text-[#50bedc] control-button`}
                onClick={() => startMoving('left')}
              >
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <Button 
                className={`${isMoving ? 'bg-red-700 hover:bg-red-800 text-white' : 'bg-[#0a1520] hover:bg-[#152535] text-[#50bedc]'} control-button`}
                onClick={stopMoving}
              >
                <Square className="h-5 w-5" />
                <span className="sr-only">停止</span>
              </Button>
              <Button 
                className={`${movementDirection === 'right' ? 'bg-[#152535]' : 'bg-[#0a1520]'} hover:bg-[#152535] text-[#50bedc] control-button`}
                onClick={() => startMoving('right')}
              >
                <ArrowRight className="h-5 w-5" />
              </Button>

              <div></div>
              <Button 
                className={`${movementDirection === 'backward' ? 'bg-[#152535]' : 'bg-[#0a1520]'} hover:bg-[#152535] text-[#50bedc] control-button`}
                onClick={() => startMoving('backward')}
              >
                <ArrowDown className="h-5 w-5" />
              </Button>
              <div></div>
            </div>
          </div>
        </div>
      </Card>
    </main>
  )
}
