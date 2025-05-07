"use client"

import { useState, useEffect, useRef } from "react"

export default function VideoTestPage() {
  const [connected, setConnected] = useState(false)
  const [videoActive, setVideoActive] = useState(false)
  const [messages, setMessages] = useState<string[]>([])
  
  const wsRef = useRef<WebSocket | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  // 添加消息到日誌
  const addMessage = (message: string) => {
    console.log(message); // 同時在控制台輸出
    setMessages(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };
  
  // 連接到WebSocket服務器
  const connect = () => {
    try {
      addMessage("正在連接到WebSocket服務器...");
      const ws = new WebSocket("ws://localhost:8766");
      wsRef.current = ws;
      
      ws.onopen = () => {
        setConnected(true);
        addMessage("已連接到WebSocket服務器");
        
        // 連接成功後立即發送ping命令
        sendPing();
      };
      
      ws.onclose = () => {
        setConnected(false);
        setVideoActive(false);
        addMessage("WebSocket連接已關閉");
      };
      
      ws.onerror = (error) => {
        addMessage(`WebSocket錯誤: ${error}`);
      };
      
      ws.onmessage = (event) => {
        try {
          if (typeof event.data === 'string') {
            const data = JSON.parse(event.data);
            
            if (data.type === "video_frame" && data.data && data.data.image) {
              // 收到視頻幀，繪製到畫布上
              drawVideoFrame(data.data);
            } else {
              addMessage(`收到消息: ${data.type}`);
            }
          } else {
            addMessage(`收到非字符串消息: ${typeof event.data}`);
          }
        } catch (error) {
          addMessage(`處理消息時出錯: ${error}`);
        }
      };
    } catch (error) {
      addMessage(`連接WebSocket時出錯: ${error}`);
    }
  };
  
  // 發送ping命令
  const sendPing = () => {
    if (!wsRef.current || wsRef.current.readyState !== 1) {
      return;
    }
    
    try {
      const pingCommand = {
        type: "ping",
        data: {
          timestamp: Date.now()
        },
        id: Date.now().toString()
      };
      
      wsRef.current.send(JSON.stringify(pingCommand));
      addMessage(`發送ping命令`);
    } catch (error) {
      addMessage(`發送ping命令時出錯: ${error}`);
    }
  };
  
  // 發送開始視頻流命令
  const startVideo = () => {
    if (!wsRef.current || wsRef.current.readyState !== 1) {
      addMessage("WebSocket未連接，無法啟動視頻");
      return;
    }
    
    try {
      const command = {
        type: "start_video_stream",
        data: {},
        id: Date.now().toString()
      };
      
      wsRef.current.send(JSON.stringify(command));
      setVideoActive(true);
      addMessage("已發送開始視頻流命令");
      
      // 初始化畫布
      if (canvasRef.current) {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.fillStyle = "#0a1520";
          ctx.fillRect(0, 0, canvas.width, canvas.height);
          ctx.font = "14px sans-serif";
          ctx.fillStyle = "#40a0ff";
          ctx.textAlign = "center";
          ctx.fillText("正在連接視頻流...", canvas.width / 2, canvas.height / 2);
        }
      }
    } catch (error) {
      addMessage(`發送視頻命令時出錯: ${error}`);
    }
  };
  
  // 發送停止視頻流命令
  const stopVideo = () => {
    if (!wsRef.current || wsRef.current.readyState !== 1) {
      addMessage("WebSocket未連接，無法停止視頻");
      return;
    }
    
    try {
      const command = {
        type: "stop_video_stream",
        data: {},
        id: Date.now().toString()
      };
      
      wsRef.current.send(JSON.stringify(command));
      setVideoActive(false);
      addMessage("已發送停止視頻流命令");
    } catch (error) {
      addMessage(`發送視頻命令時出錯: ${error}`);
    }
  };
  
  // 繪製視頻幀
  const drawVideoFrame = (frameData: any) => {
    if (!canvasRef.current) {
      console.error("畫布元素不存在");
      return;
    }
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      console.error("無法獲取畫布上下文");
      return;
    }
    
    // 檢查幀數據
    if (!frameData.image) {
      console.error("幀數據中沒有圖像");
      return;
    }
    
    console.log("收到視頻幀，準備顯示");
    console.log("視頻幀尺寸:", frameData.width, "x", frameData.height);
    console.log("視頻幀圖像數據長度:", frameData.image.length);
    
    // 創建新圖像
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
      
      // 嘗試在錯誤時印出圖像源的一部分以進行診斷
      if (img.src) {
        console.log("失敗的圖像源開頭:", img.src.substring(0, 50), "...");
      }
    };
    
    // 圖像加載成功後繪製
    img.onload = () => {
      console.log("圖像加載成功，尺寸:", img.width, "x", img.height);
      
      // 清除畫布
      ctx.fillStyle = "#0a1520";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // 計算圖像在畫布中的位置，保持縱橫比
      const imgRatio = img.width / img.height;
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
      
      // 繪製圖像
      try {
        ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
        console.log("圖像成功繪製到畫布上");
        
        // 添加時間戳
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        ctx.font = "10px monospace";
        ctx.fillStyle = "rgba(80, 190, 220, 0.8)";
        ctx.fillText(timeString, 10, canvas.height - 10);
      } catch (drawError) {
        console.error("繪製圖像時出錯:", drawError);
      }
    };
    
    // 設置圖像源為base64編碼的圖像
    try {
      // 確保base64字符串有效
      if (typeof frameData.image === 'string' && frameData.image.length > 0) {
        console.log("準備設置圖像源...");
        
        // 檢查base64字符串是否有效
        const base64Str = frameData.image;
        if (base64Str.length < 10) {
          console.error("無效的Base64字符串，長度太短");
          return;
        }
        
        img.src = `data:image/jpeg;base64,${base64Str}`;
        console.log("圖像源已設置");
      } else {
        console.error("無效的圖像數據類型:", typeof frameData.image);
      }
    } catch (error) {
      console.error("設置圖像源時出錯:", error);
    }
  };
  
  // 設置定期發送ping命令
  useEffect(() => {
    if (connected) {
      const pingInterval = setInterval(() => {
        sendPing();
      }, 10000); // 每10秒發送一次ping
      
      return () => {
        clearInterval(pingInterval);
      };
    }
  }, [connected]);
  
  // 在組件卸載時斷開連接
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  return (
    <div style={{ display: 'flex', flexDirection: 'row', height: '100vh', padding: '20px' }}>
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', marginRight: '20px' }}>
        <h1>視頻測試頁面 (簡化版)</h1>
        
        <div style={{ marginBottom: '20px' }}>
          <button 
            onClick={connect} 
            disabled={connected}
            style={{ 
              padding: '10px 20px', 
              margin: '0 10px 10px 0',
              backgroundColor: connected ? '#4CAF50' : '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: connected ? 'default' : 'pointer'
            }}
          >
            連接
          </button>
          
          <button 
            onClick={startVideo} 
            disabled={!connected || videoActive}
            style={{ 
              padding: '10px 20px', 
              margin: '0 10px 10px 0',
              backgroundColor: videoActive ? '#4CAF50' : '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: (!connected || videoActive) ? 'default' : 'pointer',
              opacity: (!connected || videoActive) ? 0.6 : 1
            }}
          >
            開始視頻
          </button>
          
          <button 
            onClick={stopVideo} 
            disabled={!connected || !videoActive}
            style={{ 
              padding: '10px 20px', 
              margin: '0 10px 10px 0',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: (!connected || !videoActive) ? 'default' : 'pointer',
              opacity: (!connected || !videoActive) ? 0.6 : 1
            }}
          >
            停止視頻
          </button>
        </div>
        
        <div style={{ 
          position: 'relative', 
          width: '640px', 
          height: '480px', 
          backgroundColor: '#0a1520',
          border: '1px solid #333',
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          <canvas 
            ref={canvasRef} 
            width={640} 
            height={480} 
            style={{ width: '100%', height: '100%' }}
          />
        </div>
        
        <div style={{ marginTop: '10px' }}>
          <p>連接狀態: {connected ? "已連接" : "未連接"}</p>
          <p>視頻狀態: {videoActive ? "活躍" : "未活躍"}</p>
        </div>
      </div>
      
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column' }}>
        <h2>日誌</h2>
        <div style={{ 
          flex: '1', 
          overflowY: 'auto', 
          border: '1px solid #ccc', 
          borderRadius: '4px',
          padding: '10px',
          backgroundColor: '#f5f5f5',
          fontFamily: 'monospace',
          fontSize: '12px'
        }}>
          {messages.map((msg, index) => (
            <div key={index} style={{ marginBottom: '5px' }}>{msg}</div>
          ))}
        </div>
      </div>
    </div>
  );
}
