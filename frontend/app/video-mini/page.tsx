"use client"

import { useState, useEffect, useRef } from "react"

export default function VideoMiniPage() {
  const [connected, setConnected] = useState(false)
  const [videoActive, setVideoActive] = useState(false)
  const [log, setLog] = useState<string[]>([])
  
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  
  // 添加日誌
  const addLog = (msg: string) => {
    console.log(msg)
    setLog(prev => [...prev, `${new Date().toLocaleTimeString()}: ${msg}`])
  }
  
  // 連接到WebSocket
  const connect = () => {
    try {
      addLog("正在連接...")
      const ws = new WebSocket("ws://localhost:8766")
      wsRef.current = ws
      
      ws.onopen = () => {
        addLog("已連接")
        setConnected(true)
      }
      
      ws.onclose = () => {
        addLog("連接已關閉")
        setConnected(false)
        setVideoActive(false)
      }
      
      ws.onerror = (e) => {
        addLog(`錯誤: ${e}`)
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === "video_frame" && data.data && data.data.image) {
            // 繪製視頻幀
            const canvas = canvasRef.current
            if (!canvas) return
            
            const ctx = canvas.getContext("2d")
            if (!ctx) return
            
            const img = new Image()
            img.onload = () => {
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
            }
            
            img.src = `data:image/jpeg;base64,${data.data.image}`
          } else {
            addLog(`收到: ${data.type}`)
          }
        } catch (e) {
          addLog(`處理消息錯誤: ${e}`)
        }
      }
    } catch (e) {
      addLog(`連接錯誤: ${e}`)
    }
  }
  
  // 開始視頻
  const startVideo = () => {
    if (!wsRef.current || wsRef.current.readyState !== 1) {
      addLog("未連接")
      return
    }
    
    try {
      wsRef.current.send(JSON.stringify({
        type: "start_video_stream",
        data: {},
        id: Date.now().toString()
      }))
      
      setVideoActive(true)
      addLog("已發送開始視頻命令")
    } catch (e) {
      addLog(`發送命令錯誤: ${e}`)
    }
  }
  
  // 停止視頻
  const stopVideo = () => {
    if (!wsRef.current || wsRef.current.readyState !== 1) {
      return
    }
    
    try {
      wsRef.current.send(JSON.stringify({
        type: "stop_video_stream",
        data: {},
        id: Date.now().toString()
      }))
      
      setVideoActive(false)
      addLog("已發送停止視頻命令")
    } catch (e) {
      addLog(`發送命令錯誤: ${e}`)
    }
  }
  
  // 清理
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])
  
  return (
    <div style={{ padding: "20px" }}>
      <h1>極簡視頻測試</h1>
      
      <div style={{ display: "flex", gap: "20px" }}>
        <div>
          <div style={{ marginBottom: "10px" }}>
            <button 
              onClick={connect} 
              disabled={connected}
              style={{ marginRight: "10px", padding: "8px 16px" }}
            >
              連接
            </button>
            
            <button 
              onClick={startVideo} 
              disabled={!connected || videoActive}
              style={{ marginRight: "10px", padding: "8px 16px" }}
            >
              開始視頻
            </button>
            
            <button 
              onClick={stopVideo} 
              disabled={!connected || !videoActive}
              style={{ padding: "8px 16px" }}
            >
              停止視頻
            </button>
          </div>
          
          <div style={{ 
            width: "640px", 
            height: "480px", 
            border: "1px solid #ccc",
            backgroundColor: "#000"
          }}>
            <canvas 
              ref={canvasRef} 
              width={640} 
              height={480} 
              style={{ width: "100%", height: "100%" }}
            />
          </div>
          
          <div style={{ marginTop: "10px" }}>
            <p>連接狀態: {connected ? "已連接" : "未連接"}</p>
            <p>視頻狀態: {videoActive ? "活躍" : "未活躍"}</p>
          </div>
        </div>
        
        <div style={{ flex: 1 }}>
          <h2>日誌</h2>
          <div style={{ 
            height: "500px", 
            overflowY: "auto", 
            border: "1px solid #ccc", 
            padding: "10px",
            fontFamily: "monospace",
            fontSize: "12px"
          }}>
            {log.map((entry, i) => (
              <div key={i}>{entry}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
