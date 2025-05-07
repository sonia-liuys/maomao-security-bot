"use client"

import { useState, useEffect } from "react"

export default function TestPage() {
  const [eyeColor, setEyeColor] = useState("green")
  const [message, setMessage] = useState("等待連接...")
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)

  // 直接在頁面上設置光環顏色的函數
  const getGlowColor = () => {
    console.log('計算光環顏色，當前眼睛顏色為:', eyeColor);
    if (eyeColor === 'yellow') {
      return 'rgba(255, 255, 0, 1)';
    } else if (eyeColor === 'red') {
      return 'rgba(255, 0, 0, 1)';
    } else if (eyeColor === 'green') {
      return 'rgba(0, 255, 0, 1)';
    } else {
      return 'rgba(80, 190, 220, 1)';
    }
  };
  
  // 建立 WebSocket 連接
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8765')
    
    ws.onopen = () => {
      console.log('WebSocket 連接已建立')
      setIsConnected(true)
      setMessage("已連接")
    }
    
    ws.onmessage = (event) => {
      console.log('收到消息:', event.data)
      try {
        const data = JSON.parse(event.data)
        setLastMessage(data)
        
        // 先打印整個消息的結構
        console.log('消息結構:', JSON.stringify(data, null, 2))
        
        // 特別處理識別結果消息
        if (data.type === 'recognition_result') {
          console.log('收到識別結果消息:', data)
          console.log('data.data:', data.data)
          console.log('data.data.eye_color:', data.data ? data.data.eye_color : 'undefined')
          
          if (data.data && data.data.eye_color) {
            const newColor = data.data.eye_color;
            console.log('設置眼睛顏色為:', newColor)
            
            // 直接設置元素樣式
            const emojiContainer = document.querySelector('.emoji-container');
            if (emojiContainer) {
              const glowColor = newColor === 'yellow' ? 'rgba(255, 255, 0, 1)' :
                              newColor === 'red' ? 'rgba(255, 0, 0, 1)' :
                              newColor === 'green' ? 'rgba(0, 255, 0, 1)' :
                              'rgba(80, 190, 220, 1)';
              
              console.log('直接設置光環顏色為:', glowColor);
              emojiContainer.setAttribute('style', `
                background: radial-gradient(circle, rgba(10,30,50,0.8) 0%, rgba(5,10,15,0.95) 70%);
                transition: all 0.5s ease;
                box-shadow: 0 0 30px 10px ${glowColor};
              `);
            }
            
            // 同時也更新狀態
            setEyeColor(newColor);
          }
        }
      } catch (error) {
        console.error('解析消息錯誤:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.log('WebSocket 錯誤:', error)
      setIsConnected(false)
      setMessage("連接錯誤")
    }
    
    ws.onclose = () => {
      console.log('WebSocket 連接已關閉')
      setIsConnected(false)
      setMessage("連接已關閉")
    }
    
    // 清理函數
    return () => {
      ws.close()
    }
  }, [])
  
  // 手動測試按鈕
  const setColor = (color: string) => {
    console.log('手動設置顏色為:', color)
    setEyeColor(color)
  }

  return (
    <div className="flex flex-col min-h-screen bg-black p-8">
      <h1 className="text-2xl font-bold text-white mb-4">WebSocket 測試頁面</h1>
      
      <div className="mb-4">
        <div className="text-white">連接狀態: {isConnected ? "已連接" : "未連接"}</div>
        <div className="text-white">消息: {message}</div>
      </div>
      
      <div className="mb-8">
        <h2 className="text-xl font-bold text-white mb-2">手動測試</h2>
        <div className="flex gap-2">
          <button 
            className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
            onClick={() => setColor("green")}
          >
            綠色
          </button>
          <button 
            className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
            onClick={() => setColor("yellow")}
          >
            黃色
          </button>
          <button 
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
            onClick={() => setColor("red")}
          >
            紅色
          </button>
        </div>
      </div>
      
      <div className="flex-grow flex flex-col items-center justify-center">
        <div className="relative">
          <div
            className="emoji-container w-[200px] h-[200px] flex items-center justify-center rounded-full transition-all duration-500"
            style={{
              background: "radial-gradient(circle, rgba(10,30,50,0.8) 0%, rgba(5,10,15,0.95) 70%)",
              transition: "all 0.5s ease",
              boxShadow: `0 0 30px 10px ${getGlowColor()}`
            }}
          >
            <div
              className="text-[100px]"
            >
              😐
            </div>
            <div className="absolute bottom-0 left-0 right-0 text-sm text-white bg-black/70 text-center py-1">
              {eyeColor}
            </div>
          </div>
        </div>
        
        {lastMessage && (
          <div className="mt-8 p-4 bg-gray-800 rounded text-white">
            <h3 className="text-lg font-bold mb-2">最後收到的消息:</h3>
            <pre className="whitespace-pre-wrap text-sm">
              {JSON.stringify(lastMessage, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
