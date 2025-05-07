"use client";

import { useState, useEffect, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function VideoTest() {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<string[]>([]);
  const [videoActive, setVideoActive] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  // 連接到WebSocket服務器
  const connect = () => {
    try {
      // 如果已經有連接，先關閉它
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (e) {
          console.error("關閉現有WebSocket連接時出錯:", e);
        }
      }
      
      // 連接到測試視頻服務器，使用不同的端口
      addMessage("正在連接到WebSocket服務器...");
      const ws = new WebSocket("ws://localhost:8766");
      wsRef.current = ws;
      
      // 設置連接逾時
      const connectionTimeout = setTimeout(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          addMessage("連接逾時，正在重試...");
          connect(); // 重試連接
        }
      }, 5000); // 5秒逾時
      
      ws.onopen = () => {
        clearTimeout(connectionTimeout);
        setConnected(true);
        addMessage("已連接到WebSocket服務器");
        addMessage(`WebSocket狀態: ${ws.readyState} (OPEN=1)`);
        
        // 連接成功後等待短暂再發送ping命令
        setTimeout(() => {
          sendPing();
          
          // 設置定期發送ping命令的計時器
          const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              sendPing();
            } else {
              clearInterval(pingInterval);
              
              // 如果連接已關閉，嘗試重新連接
              if (ws.readyState === 3) { // CLOSED=3
                addMessage("連接已關閉，嘗試重新連接...");
                setTimeout(connect, 1000); // 等待1秒再重新連接
              }
            }
          }, 10000); // 每10秒發送一次ping
        }, 500); // 等待500毫秒再發送第一個ping
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
          // 檢查消息類型
          if (typeof event.data === 'string') {
            // 嘗試解析JSON
            try {
              const data = JSON.parse(event.data);
              
              if (data.type === "video_frame" && data.data && data.data.image) {
                const imgLength = data.data.image.length;
                addMessage(`收到視頻幀: ${data.data.width}x${data.data.height}, 圖像數據長度: ${imgLength} 字節`);
                
                // 檢查base64字符串是否有效
                if (imgLength > 100) {
                  addMessage(`Base64字符串開頭: ${data.data.image.substring(0, 20)}...`);
                  drawVideoFrame(data.data.image);
                } else {
                  addMessage(`警告: 圖像數據太短，可能不是有效的base64字符串`);
                }
              } else if (data.type === "command_response") {
                addMessage(`收到命令響應: ${JSON.stringify(data.result)}`);
              } else if (data.type === "status_update") {
                addMessage(`收到狀態更新: ${JSON.stringify(data.data).substring(0, 100)}...`);
              } else if (data.type === "pong") {
                addMessage(`收到pong響應，延遲: ${Date.now() - (data.data?.timestamp || 0)}ms`);
              } else {
                addMessage(`收到消息類型: ${data.type}`);
              }
            } catch (e) {
              addMessage(`無法解析JSON: ${event.data.substring(0, 50)}...`);
              addMessage(`解析錯誤: ${e}`);
            }
          } else {
            addMessage(`收到非字符串消息類型: ${typeof event.data}`);
            if (event.data instanceof Blob) {
              addMessage(`Blob大小: ${event.data.size} 字節`);
            } else if (event.data instanceof ArrayBuffer) {
              addMessage(`ArrayBuffer大小: ${event.data.byteLength} 字節`);
            }
          }
        } catch (error) {
          addMessage(`處理消息時出錯: ${error}`);
        }
      };
    } catch (error) {
      addMessage(`連接錯誤: ${error}`);
    }
  };
  
  // 斷開WebSocket連接
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };
  
  // 發送ping命令以保持連接活躍
  const sendPing = () => {
    if (!wsRef.current) {
      addMessage("WebSocket實例不存在，無法發送ping命令");
      return;
    }
    
    if (wsRef.current.readyState !== WebSocket.OPEN) {
      addMessage(`WebSocket狀態不是OPEN，當前狀態: ${wsRef.current.readyState}`);
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
      addMessage(`發送ping命令，時間戳: ${pingCommand.data.timestamp}`);
    } catch (error) {
      addMessage(`發送ping命令時出錯: ${error}`);
      
      // 如果發送失敗，檢查連接狀態
      if (wsRef.current) {
        addMessage(`發送失敗時的WebSocket狀態: ${wsRef.current.readyState}`);
        
        // 如果連接已關閉，嘗試重新連接
        if (wsRef.current.readyState === 3 || wsRef.current.readyState === 2) { // CLOSED=3, CLOSING=2
          addMessage("連接已關閉或正在關閉，嘗試重新連接...");
          setTimeout(connect, 1000); // 等待1秒再重新連接
        }
      }
    }
  };
  
  // 發送開始視頻流命令
  const startVideo = () => {
    if (!wsRef.current) {
      addMessage("WebSocket實例不存在，嘗試重新連接...");
      connect();
      setTimeout(() => {
        addMessage("請在連接成功後再次點擊開始視頻按鈕");
      }, 1000);
      return;
    }
    
    if (wsRef.current.readyState !== 1) { // OPEN=1
      addMessage(`WebSocket狀態不是OPEN，當前狀態: ${wsRef.current.readyState}`);
      
      // 如果連接已關閉，嘗試重新連接
      if (wsRef.current.readyState === 3 || wsRef.current.readyState === 2) { // CLOSED=3, CLOSING=2
        addMessage("連接已關閉或正在關閉，嘗試重新連接...");
        connect();
        setTimeout(() => {
          addMessage("請在連接成功後再次點擊開始視頻按鈕");
        }, 1000);
      } else if (wsRef.current.readyState === 0) { // CONNECTING=0
        addMessage("連接中，請稍後再試...");
        setTimeout(() => {
          addMessage("請在連接成功後再次點擊開始視頻按鈕");
        }, 1000);
      }
      return;
    }
    
    try {
      // 先發送ping命令確保連接活躍
      sendPing();
      
      // 等待短暂後發送視頻流命令
      setTimeout(() => {
        if (!wsRef.current) {
          addMessage("WebSocket實例不存在，無法啟動視頻");
          return;
        }
        
        if (wsRef.current.readyState !== 1) { // OPEN=1
          addMessage(`WebSocket狀態不是OPEN，當前狀態: ${wsRef.current.readyState}`);
          return;
        }
        
        const command = {
          type: "start_video_stream",
          data: {},
          id: Date.now().toString()
        };
        
        try {
          wsRef.current.send(JSON.stringify(command));
          setVideoActive(true);
          addMessage("已發送開始視頻流命令");
        } catch (sendError) {
          addMessage(`發送視頻命令時出錯: ${sendError}`);
          
          // 如果發送失敗，檢查連接狀態
          if (wsRef.current) {
            addMessage(`發送失敗時的WebSocket狀態: ${wsRef.current.readyState}`);
          }
        }
      }, 500); // 等待500毫秒後發送視頻流命令
    } catch (error) {
      addMessage(`處理視頻命令時出錯: ${error}`);
    }
  };
  
  // 發送停止視頻流命令
  const stopVideo = () => {
    // 即使連接有問題，也先將前端狀態設為非視頻活躍
    setVideoActive(false);
    
    if (!wsRef.current) {
      addMessage("WebSocket實例不存在，已停止視頻");
      return;
    }
    
    if (wsRef.current.readyState !== 1) { // OPEN=1
      addMessage(`WebSocket狀態不是OPEN，當前狀態: ${wsRef.current.readyState}`);
      addMessage("已停止視頻顯示");
      return;
    }
    
    try {
      const command = {
        type: "stop_video_stream",
        data: {},
        id: Date.now().toString()
      };
      
      try {
        wsRef.current.send(JSON.stringify(command));
        addMessage("已發送停止視頻流命令");
      } catch (sendError) {
        addMessage(`發送停止視頻命令時出錯: ${sendError}`);
        
        // 如果發送失敗，檢查連接狀態
        if (wsRef.current) {
          addMessage(`發送失敗時的WebSocket狀態: ${wsRef.current.readyState}`);
        }
      }
    } catch (error) {
      addMessage(`處理停止視頻命令時出錯: ${error}`);
    }
  };
  
  // 添加消息到日誌
  const addMessage = (message: string) => {
    setMessages(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };
  
  // 繪製視頻幀
  const drawVideoFrame = (base64Image: string) => {
    if (!canvasRef.current) {
      addMessage("畫布元素不存在，無法繪製視頻幀");
      return;
    }
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      addMessage("無法獲取畫布上下文，無法繪製視頻幀");
      return;
    }
    
    // 檢查base64字符串是否有效
    if (!base64Image || base64Image.length < 100) {
      addMessage(`無效的base64圖像數據: 長度為 ${base64Image?.length || 0} 字節`);
      
      // 繪製錯誤訊息
      ctx.fillStyle = "#0a1520";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = "14px sans-serif";
      ctx.fillStyle = "#ff4040";
      ctx.textAlign = "center";
      ctx.fillText("無效的視頻幀數據", canvas.width / 2, canvas.height / 2);
      return;
    }
    
    // 創建新圖像
    const img = new Image();
    
    // 設置加載逾時
    const imageTimeout = setTimeout(() => {
      addMessage("圖像加載逾時");
      
      // 繪製逾時訊息
      ctx.fillStyle = "#0a1520";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = "14px sans-serif";
      ctx.fillStyle = "#ff4040";
      ctx.textAlign = "center";
      ctx.fillText("圖像加載逾時", canvas.width / 2, canvas.height / 2);
    }, 5000); // 5秒逾時
    
    // 設置圖像加載錯誤處理
    img.onerror = (err) => {
      clearTimeout(imageTimeout);
      addMessage(`圖像加載失敗: ${err}`);
      
      // 嘗試印出部分base64字符串以進行調試
      if (base64Image) {
        addMessage(`Base64字符串開頭: ${base64Image.substring(0, 30)}...`);
        addMessage(`Base64字符串結尾: ...${base64Image.substring(base64Image.length - 30)}`);
      }
      
      // 繪製錯誤訊息
      ctx.fillStyle = "#0a1520";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = "14px sans-serif";
      ctx.fillStyle = "#ff4040";
      ctx.textAlign = "center";
      ctx.fillText("視頻幀加載失敗", canvas.width / 2, canvas.height / 2);
      ctx.font = "12px sans-serif";
      ctx.fillText(`錯誤: ${err}`, canvas.width / 2, canvas.height / 2 + 20);
    };
    
    // 圖像加載成功後繪製
    img.onload = () => {
      clearTimeout(imageTimeout);
      addMessage(`圖像加載成功: ${img.width}x${img.height}`);
      
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
        
        // 添加時間戳和幀計數
        const timestamp = new Date().toLocaleTimeString();
        ctx.font = "12px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "left";
        ctx.fillText(`時間: ${timestamp}`, 10, 20);
        
        // 不要每幀都輸出日誌，源碼會變得難以閱讀
        // addMessage("圖像成功繪製到畫布上");
      } catch (drawError) {
        addMessage(`繪製圖像時出錯: ${drawError}`);
        
        // 繪製錯誤訊息
        ctx.fillStyle = "#0a1520";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.font = "14px sans-serif";
        ctx.fillStyle = "#ff4040";
        ctx.textAlign = "center";
        ctx.fillText("繪製圖像時出錯", canvas.width / 2, canvas.height / 2);
        ctx.font = "12px sans-serif";
        ctx.fillText(`${drawError}`, canvas.width / 2, canvas.height / 2 + 20);
      }
    };
    
    // 設置圖像源為base64編碼的圖像
    try {
      // 確保字符串開頭沒有多餘的空格或換行符
      const cleanBase64 = base64Image.trim();
      img.src = `data:image/jpeg;base64,${cleanBase64}`;
    } catch (error) {
      clearTimeout(imageTimeout);
      addMessage(`設置圖像源時出錯: ${error}`);
      
      // 繪製錯誤訊息
      ctx.fillStyle = "#0a1520";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.font = "14px sans-serif";
      ctx.fillStyle = "#ff4040";
      ctx.textAlign = "center";
      ctx.fillText("設置圖像源時出錯", canvas.width / 2, canvas.height / 2);
      ctx.font = "12px sans-serif";
      ctx.fillText(`${error}`, canvas.width / 2, canvas.height / 2 + 20);
    }
  };
  
  // 清理函數
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  // 初始化畫布
  useEffect(() => {
    if (!canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    
    ctx.fillStyle = "#0a1520";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = "14px sans-serif";
    ctx.fillStyle = "#40a0ff";
    ctx.textAlign = "center";
    ctx.fillText("等待視頻流連接...", canvas.width / 2, canvas.height / 2);
  }, []);
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">視頻流測試頁面</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <h2 className="text-xl font-semibold mb-2">視頻顯示</h2>
          <div className="relative aspect-video bg-slate-950 rounded-md overflow-hidden">
            <canvas 
              ref={canvasRef} 
              width={640} 
              height={480} 
              className="w-full h-full"
            />
          </div>
          
          <div className="flex gap-2 mt-4">
            <Button 
              onClick={connect} 
              disabled={connected}
              variant="default"
            >
              連接
            </Button>
            
            <Button 
              onClick={disconnect} 
              disabled={!connected}
              variant="destructive"
            >
              斷開
            </Button>
            
            <Button 
              onClick={startVideo} 
              disabled={!connected || videoActive}
              variant="outline"
            >
              開始視頻
            </Button>
            
            <Button 
              onClick={stopVideo} 
              disabled={!connected || !videoActive}
              variant="outline"
            >
              停止視頻
            </Button>
          </div>
        </Card>
        
        <Card className="p-4">
          <h2 className="text-xl font-semibold mb-2">日誌</h2>
          <div className="bg-slate-950 text-slate-300 p-2 rounded-md h-[480px] overflow-y-auto font-mono text-sm">
            {messages.length === 0 ? (
              <p className="text-slate-500">尚無日誌...</p>
            ) : (
              messages.map((msg, index) => (
                <div key={index} className="mb-1">{msg}</div>
              ))
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
