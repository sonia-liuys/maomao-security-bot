"use client"

import { useState, useEffect, useRef } from "react"

export default function VideoBasicPage() {
  const [connected, setConnected] = useState(false)
  const [videoActive, setVideoActive] = useState(false)
  const [log, setLog] = useState<string[]>([])
  
  const wsRef = useRef<WebSocket | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  // 添加日誌
  const addLog = (message: string) => {
    console.log(message);
    setLog(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  }
  
  // 連接到WebSocket服務器
  const connect = () => {
    // 確保在瀏覽器環境中執行
    if (typeof window === 'undefined') {
      console.log('不在瀏覽器環境中，無法創建 WebSocket');
      return;
    }
    
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {
        console.error('關閉現有WebSocket連接時出錯:', e);
      }
    }
    
    try {
      addLog("正在連接到測試視頻服務器...");
      console.log('嘗試連接到 WebSocket 服務器...');
      
      // 確保 WebSocket 在瀏覽器環境中可用
      if (!window.WebSocket) {
        addLog('瀏覽器不支援 WebSocket');
        return;
      }
      
      const ws = new WebSocket("ws://localhost:8766");
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('已連接到 WebSocket 服務器');
        addLog("已連接到測試視頻服務器");
        setConnected(true);
      };
      
      ws.onclose = () => {
        console.log('WebSocket 連接已關閉');
        addLog("連接已關閉");
        setConnected(false);
        setVideoActive(false);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket 錯誤:', error);
        addLog(`WebSocket錯誤: ${error}`);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "video_frame" && data.data && data.data.image) {
            const imgData = data.data;
            console.log(`收到視頻幀: ${imgData.width}x${imgData.height}`);
            addLog(`收到視頻幀: ${imgData.width}x${imgData.height}`);
            
            // 繪製視頻幀
            const canvas = canvasRef.current;
            if (!canvas) return;
            
            const ctx = canvas.getContext("2d");
            if (!ctx) return;
            
            // 創建圖像
            const img = new Image();
            img.onload = () => {
              // 清除畫布
              ctx.fillStyle = "#000";
              ctx.fillRect(0, 0, canvas.width, canvas.height);
              
              // 繪製圖像
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
              
              // 添加時間戳
              ctx.font = "12px Arial";
              ctx.fillStyle = "#fff";
              ctx.fillText(new Date().toLocaleTimeString(), 10, 20);
              
              console.log('圖像成功繪製到畫布上');
            };
            
            img.onerror = (err) => {
              console.error('圖像加載失敗:', err);
              addLog(`圖像加載失敗: ${err}`);
              
              // 顯示錯誤信息
              ctx.fillStyle = "#000";
              ctx.fillRect(0, 0, canvas.width, canvas.height);
              ctx.font = "16px Arial";
              ctx.fillStyle = "#f00";
              ctx.textAlign = "center";
              ctx.fillText("圖像加載失敗", canvas.width/2, canvas.height/2);
            };
            
            // 設置圖像源
            img.src = `data:image/jpeg;base64,${imgData.image}`;
          } else {
            addLog(`收到消息: ${data.type}`);
          }
        } catch (error) {
          console.error('處理消息時出錯:', error);
          addLog(`處理消息時出錯: ${error}`);
        }
      };
    } catch (error) {
      console.error('連接時出錯:', error);
      addLog(`連接時出錯: ${error}`);
    }
  };
  
  // 開始視頻流
  const startVideo = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog("WebSocket未連接，無法啟動視頻");
      return;
    }
    
    try {
      const command = {
        type: "start_video_stream",
        data: {},
        id: Date.now().toString()
      };
      
      wsRef.current.send(JSON.stringify(command));
      addLog("已發送開始視頻流命令");
      setVideoActive(true);
      
      // 初始化畫布
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.fillStyle = "#000";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.font = "16px Arial";
          ctx.fillStyle = "#0f0";
          ctx.textAlign = "center";
          ctx.fillText("正在等待視頻流...", canvas.width/2, canvas.height/2);
        }
      }
    } catch (error) {
      addLog(`發送視頻命令時出錯: ${error}`);
    }
  };
  
  // 停止視頻流
  const stopVideo = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog("WebSocket未連接，無法停止視頻");
      return;
    }
    
    try {
      const command = {
        type: "stop_video_stream",
        data: {},
        id: Date.now().toString()
      };
      
      wsRef.current.send(JSON.stringify(command));
      addLog("已發送停止視頻流命令");
      setVideoActive(false);
    } catch (error) {
      addLog(`發送視頻命令時出錯: ${error}`);
    }
  };
  
  // 發送ping命令
  const sendPing = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      addLog("WebSocket未連接，無法發送ping");
      return;
    }
    
    try {
      const command = {
        type: "ping",
        data: { timestamp: Date.now() },
        id: Date.now().toString()
      };
      
      wsRef.current.send(JSON.stringify(command));
      addLog("已發送ping命令");
    } catch (error) {
      addLog(`發送ping命令時出錯: ${error}`);
    }
  };
  
  // 清理
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>基本視頻測試</h1>
      
      <div style={{ display: 'flex', gap: '20px' }}>
        <div>
          <div style={{ marginBottom: '10px' }}>
            <button 
              onClick={connect} 
              disabled={connected}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: connected ? '#4CAF50' : '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                marginRight: '10px',
                cursor: 'pointer',
                opacity: connected ? 0.7 : 1
              }}
            >
              連接
            </button>
            
            <button 
              onClick={startVideo} 
              disabled={!connected || videoActive}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                marginRight: '10px',
                cursor: 'pointer',
                opacity: (!connected || videoActive) ? 0.7 : 1
              }}
            >
              開始視頻
            </button>
            
            <button 
              onClick={stopVideo} 
              disabled={!connected || !videoActive}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                marginRight: '10px',
                cursor: 'pointer',
                opacity: (!connected || !videoActive) ? 0.7 : 1
              }}
            >
              停止視頻
            </button>
            
            <button 
              onClick={sendPing} 
              disabled={!connected}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: '#FF9800',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                opacity: !connected ? 0.7 : 1
              }}
            >
              發送Ping
            </button>
          </div>
          
          <div style={{ 
            width: '640px', 
            height: '480px', 
            backgroundColor: '#000',
            border: '1px solid #333',
            marginBottom: '10px'
          }}>
            <canvas 
              ref={canvasRef} 
              width={640} 
              height={480} 
              style={{ width: '100%', height: '100%' }}
            />
          </div>
          
          <div>
            <p>連接狀態: <span style={{ color: connected ? 'green' : 'red' }}>{connected ? '已連接' : '未連接'}</span></p>
            <p>視頻狀態: <span style={{ color: videoActive ? 'green' : 'red' }}>{videoActive ? '活躍' : '未活躍'}</span></p>
          </div>
        </div>
        
        <div style={{ flex: 1 }}>
          <h2>日誌</h2>
          <div style={{ 
            height: '500px', 
            overflowY: 'auto', 
            border: '1px solid #ccc',
            padding: '10px',
            backgroundColor: '#f5f5f5',
            fontFamily: 'monospace',
            fontSize: '12px'
          }}>
            {log.map((entry, index) => (
              <div key={index} style={{ marginBottom: '4px' }}>{entry}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
