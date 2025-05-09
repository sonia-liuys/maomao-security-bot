import { useState, useEffect, useCallback } from 'react';

const useRobotConnection = (url = 'ws://192.168.1.147:8765') => {
  // 在服務器端渲染時返回預設值
  if (typeof window === 'undefined') {
    console.log('useRobotConnection: 在服務器端渲染時返回預設值');
    return {
      isConnected: false,
      robotStatus: {},
      lastMessage: null,
      sendCommand: () => false,
      setRobotMode: () => false
    };
  }
  
  try {
  
  console.log(`初始化 WebSocket 連接到: ${url}`);
  
  // 確保 URL 是正確的
  if (!url.startsWith('ws://') && !url.startsWith('wss://')) {
    console.error(`無效的 WebSocket URL: ${url}，必須以 ws:// 或 wss:// 開頭`);
    url = 'ws://localhost:8765';
    console.log(`使用默認 URL: ${url}`);
  }
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [robotStatus, setRobotStatus] = useState({});
  const [lastMessage, setLastMessage] = useState(null);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);

  // 建立WebSocket連接
  useEffect(() => {
    // 確保在瀏覽器環境中執行
    if (typeof window === 'undefined') return;
    
    // 定義 WebSocket 狀態常量，避免使用 WebSocket.OPEN 等常量失敗
    // Define WebSocket state constants to avoid using WebSocket.OPEN etc. which might fail
    const WS_STATES = {
      CONNECTING: 0,
      OPEN: 1,
      CLOSING: 2,
      CLOSED: 3
    };
    
    let ws = null;
    let isUnmounted = false;
    let reconnectTimer = null;
    
    const connect = () => {
      if (isUnmounted) return;
      
      // 清除之前的重連計時器
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      
      console.log(`嘗試連接到機器人: ${url}`);
      
      try {
        // 關閉之前的連接
        if (ws) {
          try {
            ws.close();
          } catch (e) {
            console.error('關閉舊連接時出錯:', e);
          }
        }
        
        // 創建新的WebSocket連接
        ws = new WebSocket(url);
        console.log('已創建新的WebSocket連接');
        
        ws.onopen = () => {
          if (isUnmounted) return;
          console.log('已連接到機器人');
          setIsConnected(true);
          setReconnectAttempt(0); // 重置重連計數
          
          // 連接成功後發送ping命令
          try {
            const pingCommand = {
              type: 'ping',
              data: {
                timestamp: Date.now()
              }
            };
            ws.send(JSON.stringify(pingCommand));
            console.log('發送ping命令');
          } catch (error) {
            console.error('發送ping命令失敗:', error);
          }
        };
        
        ws.onclose = () => {
          if (isUnmounted) return;
          console.log('與機器人的連接已關閉');
          setIsConnected(false);
          
          // 嘗試重新連接
          const newAttempt = reconnectAttempt + 1;
          setReconnectAttempt(newAttempt);
          
          // 計算重連延遲，最多30秒
          const delay = Math.min(1000 * Math.pow(1.5, newAttempt), 30000);
          console.log(`將在 ${delay/1000} 秒後重新連接，嘗試次數: ${newAttempt}`);
          
          // 清除之前的重連計時器
          if (reconnectTimer) {
            clearTimeout(reconnectTimer);
          }
          
          reconnectTimer = setTimeout(() => {
            if (!isUnmounted) {
              console.log(`開始重連嘗試 #${newAttempt}`);
              connect();
            }
          }, delay);
        };
        
        ws.onerror = (event) => {
          if (isUnmounted) return;
          
          // 注意：WebSocket 的 onerror 事件不提供錯誤詳細信息
          console.log('WebSocket 連接發生錯誤');
          setIsConnected(false);
          
          // 嘗試重新連接
          if (reconnectAttempt < 5) {
            console.log(`將在 2 秒後嘗試重新連接，重試次數: ${reconnectAttempt + 1}`);
            setTimeout(() => {
              if (!isUnmounted) {
                setReconnectAttempt(prev => prev + 1);
              }
            }, 2000);
          }
        };
        
        ws.onmessage = (event) => {
          if (isUnmounted) return;
          
          try {
            // 檢查是否是字符串
            if (typeof event.data !== 'string') {
              console.log('收到非字符串數據:', typeof event.data);
              return;
            }
            
            // 檢查是否為空字符串
            if (!event.data.trim()) {
              console.log('收到空消息，已忽略');
              return;
            }
            
            // 處理特殊格式消息
            // 檢查是否為 JSON 格式
            const startsWithOpenBrace = event.data.trim().startsWith('{');
            const startsWithOpenBracket = event.data.trim().startsWith('[');
            const isPotentialJson = startsWithOpenBrace || startsWithOpenBracket;

            // 如果不像是 JSON，則直接處理為特殊格式消息
            if (!isPotentialJson) {
              // 特殊字符串消息處理
              if (event.data === 'ping' || event.data === 'pong') {
                console.log(`收到${event.data}消息`);
                if (event.data === 'ping') {
                  try {
                    ws.send('pong');
                    console.log('已回覆pong');
                  } catch (error) {
                    console.error('發送pong回覆失敗:', error);
                  }
                }
                return;
              }

              // 其他非 JSON 格式的消息，只進行記錄不嘗試處理
              console.log('收到非 JSON 格式的消息:', event.data.substring(0, 50) + 
                (event.data.length > 50 ? '...' : ''));
              return;
            }
            
            // 嘗試解析JSON
            let data;
            try {
              data = JSON.parse(event.data);
            } catch (error) {
              console.error('消息不是有效的JSON格式:', error);
              console.log('原始消息前100字符:', event.data.substring(0, 100) + '...');
              return;
            }
            
            // 處理不同類型的消息
            if (data.type === 'video_frame') {
              // 視頻幀消息 - 不打印完整數據以避免日誌過大
              console.log('收到視頻幀消息');
              if (data.data) {
                console.log('視頻幀信息:', {
                  timestamp: data.data.timestamp,
                  width: data.data.width,
                  height: data.data.height,
                  imageSize: data.data.image ? data.data.image.length : 'N/A'
                });
              }
            } else if (data.type === 'status_update' || data.type === 'status') {
              // 狀態更新消息
              console.log('收到狀態更新:', data.type);
              
              // 添加更詳細的日誌，檢查人臉座標數據
              // Add more detailed log, check face coordinates data
              console.log('[DEBUG] 收到的狀態更新包含以下數據:', {
                face_detected: data.data?.face_detected,
                face_x: data.data?.face_x,
                face_y: data.data?.face_y,
                recognized_person: data.data?.recognized_person
              });
              
              setRobotStatus(prev => ({
                ...prev,
                ...data.data
              }));
            } else if (data.type === 'recognition_result') {
              // 識別結果消息
              console.log('收到識別結果:', {
                eye_color: data.data?.eye_color,
                emoji: data.data?.emoji
              });
              setRobotStatus(prev => ({
                ...prev,
                ...data.data,
                recognition_result: data.data
              }));
            } else {
              // 其他類型的消息
              console.log('收到消息:', data.type);
            }
            
            // 更新最後收到的消息
            setLastMessage(data);
            
          } catch (error) {
            console.error('處理消息時出錯:', error);
          }
        };
        
        setSocket(ws);
      } catch (error) {
        console.error('創建WebSocket連接失敗:', error);
      }
    };
    
    connect();
    
    // 清理函數
    return () => {
      isUnmounted = true;
      if (ws) {
        try {
          ws.close();
        } catch (error) {
          console.error('關閉WebSocket連接失敗:', error);
        }
      }
    };
  }, [url, reconnectAttempt]);
  
  // 發送命令到機器人
  const sendCommand = useCallback((command) => {
    if (!socket) {
      console.error('無法發送命令: WebSocket實例不存在');
      return false;
    }
    
    // 檢查 WebSocket 是否已定義並且連接狀態是否正確
    // Check if WebSocket is defined and connection state is correct
    try {
      if (!isConnected) {
        console.error('無法發送命令: WebSocket未連接');
        return false;
      }
      
      // 確保 WebSocket.OPEN 常量存在
      // Ensure WebSocket.OPEN constant exists
      const OPEN_STATE = 1; // WebSocket.OPEN 的值是 1
      
      if (socket.readyState !== OPEN_STATE) {
        console.error(`無法發送命令: WebSocket狀態不是 OPEN (當前狀態: ${socket.readyState})`);
        console.log('WebSocket狀態代碼: CONNECTING=0, OPEN=1, CLOSING=2, CLOSED=3');
        return false;
      }
    } catch (error) {
      console.error('檢查 WebSocket 狀態時出錯:', error);
      return false;
    }
    
    try {
      // 添加唯一ID到命令
      const messageWithId = {
        ...command,
        id: Date.now().toString()
      };
      
      const commandString = JSON.stringify(messageWithId);
      socket.send(commandString);
      console.log(`已發送命令: ${command.type}`, command);
      
      // 特別處理視頻流命令
      if (command.type === 'start_video_stream') {
        console.log('已發送開始視頻流命令，等待視頻幀...');
      } else if (command.type === 'stop_video_stream') {
        console.log('已發送停止視頻流命令');
      }
      
      return true;
    } catch (error) {
      console.error('發送命令時出錯:', error);
      return false;
    }
  }, [socket, isConnected]);
  
  // 設置機器人模式
  const setRobotMode = useCallback((mode) => {
    console.log(`設置機器人模式: ${mode}`);
    
    try {
      if (!socket) {
        console.error('無法設置模式: WebSocket 實例不存在');
        return false;
      }
      
      if (!isConnected) {
        console.error('無法設置模式: WebSocket 未連接');
        return false;
      }
      
      // 確保 WebSocket.OPEN 常量存在
      // Ensure WebSocket.OPEN constant exists
      const OPEN_STATE = 1; // WebSocket.OPEN 的值是 1
      
      if (socket.readyState !== OPEN_STATE) {
        console.error(`無法設置模式: WebSocket 狀態不是 OPEN (當前狀態: ${socket.readyState})`);
        return false;
      }
    } catch (error) {
      console.error('檢查 WebSocket 狀態時出錯:', error);
      return false;
    }
    try {
      const message = {
        type: "set_mode",
        data: {
          mode: mode
        },
        id: Date.now().toString()
      };
      
      console.log('發送模式切換命令:', message);
      socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('發送模式切換命令失敗:', error);
      return false;
    }
  }, [socket, isConnected]);
  
  return {
    isConnected,
    robotStatus,
    lastMessage,
    sendCommand,
    setRobotMode
  };
  
  } catch (error) {
    console.error('使用 useRobotConnection 時發生錯誤:', error);
    return {
      isConnected: false,
      robotStatus: {},
      lastMessage: null,
      sendCommand: () => {
        console.error('無法發送命令: 連接發生錯誤');
        return false;
      },
      setRobotMode: () => {
        console.error('無法設置模式: 連接發生錯誤');
        return false;
      }
    };
  }
};

export default useRobotConnection;
