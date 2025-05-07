"use client"

import { useEffect, useRef, useState } from 'react'

interface RadarDisplayProps {
  size?: number
  scanSpeed?: number
  dotCount?: number
  className?: string
}

const RadarDisplay = ({
  size = 300,
  scanSpeed = 2,
  dotCount = 8,
  className = ""
}: RadarDisplayProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [angle, setAngle] = useState(0)
  const [dots, setDots] = useState<Array<{x: number, y: number, distance: number, active: boolean}>>([])
  
  // 初始化雷達上的點
  useEffect(() => {
    const newDots = []
    for (let i = 0; i < dotCount; i++) {
      // 隨機生成點的位置和距離
      const randomAngle = Math.random() * Math.PI * 2
      const randomDistance = 0.3 + Math.random() * 0.6 // 30%-90%的半徑
      const x = Math.cos(randomAngle) * randomDistance
      const y = Math.sin(randomAngle) * randomDistance
      
      newDots.push({
        x,
        y,
        distance: randomDistance,
        active: false
      })
    }
    setDots(newDots)
  }, [dotCount])
  
  // 雷達掃描動畫
  useEffect(() => {
    const interval = setInterval(() => {
      setAngle(prevAngle => {
        const newAngle = (prevAngle + 0.02 * scanSpeed) % (Math.PI * 2)
        
        // 更新點的激活狀態
        setDots(prevDots => {
          return prevDots.map(dot => {
            const dotAngle = Math.atan2(dot.y, dot.x)
            const normalizedDotAngle = dotAngle < 0 ? dotAngle + Math.PI * 2 : dotAngle
            const normalizedScanAngle = newAngle
            
            // 當掃描線經過點時激活它
            const angleDiff = Math.abs(normalizedDotAngle - normalizedScanAngle)
            const isActive = angleDiff < 0.1 || angleDiff > Math.PI * 2 - 0.1
            
            return {
              ...dot,
              active: isActive
            }
          })
        })
        
        return newAngle
      })
    }, 16) // ~60fps
    
    return () => clearInterval(interval)
  }, [scanSpeed])
  
  // 繪製雷達
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    const centerX = size / 2
    const centerY = size / 2
    const radius = size / 2 - 10
    
    // 清除畫布
    ctx.clearRect(0, 0, size, size)
    
    // 繪製背景圓圈
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
    ctx.strokeStyle = 'rgba(80, 190, 220, 0.3)'
    ctx.lineWidth = 2
    ctx.stroke()
    
    // 繪製中間圓圈
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius * 0.66, 0, Math.PI * 2)
    ctx.stroke()
    
    // 繪製內圈
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius * 0.33, 0, Math.PI * 2)
    ctx.stroke()
    
    // 繪製十字線
    ctx.beginPath()
    ctx.moveTo(centerX - radius, centerY)
    ctx.lineTo(centerX + radius, centerY)
    ctx.moveTo(centerX, centerY - radius)
    ctx.lineTo(centerX, centerY + radius)
    ctx.strokeStyle = 'rgba(80, 190, 220, 0.2)'
    ctx.stroke()
    
    // 繪製掃描線
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.lineTo(
      centerX + Math.cos(angle) * radius,
      centerY + Math.sin(angle) * radius
    )
    ctx.strokeStyle = 'rgba(80, 190, 220, 0.8)'
    ctx.lineWidth = 2
    ctx.stroke()
    
    // 繪製掃描扇形
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, angle - 0.2, angle, false)
    ctx.lineTo(centerX, centerY)
    ctx.fillStyle = 'rgba(80, 190, 220, 0.2)'
    ctx.fill()
    
    // 繪製點
    dots.forEach(dot => {
      ctx.beginPath()
      ctx.arc(
        centerX + dot.x * radius,
        centerY + dot.y * radius,
        dot.active ? 4 : 3,
        0,
        Math.PI * 2
      )
      ctx.fillStyle = dot.active 
        ? 'rgba(255, 100, 100, 0.8)' 
        : 'rgba(80, 190, 220, 0.5)'
      ctx.fill()
      
      // 如果點被激活，繪製波紋效果
      if (dot.active) {
        ctx.beginPath()
        ctx.arc(
          centerX + dot.x * radius,
          centerY + dot.y * radius,
          6,
          0,
          Math.PI * 2
        )
        ctx.strokeStyle = 'rgba(255, 100, 100, 0.5)'
        ctx.stroke()
      }
    })
    
    // 繪製中心點
    ctx.beginPath()
    ctx.arc(centerX, centerY, 4, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(80, 190, 220, 0.8)'
    ctx.fill()
    
  }, [size, angle, dots])
  
  return (
    <div className={`relative ${className}`}>
      <canvas 
        ref={canvasRef} 
        width={size} 
        height={size}
        className="rounded-full bg-[#0a1520]"
      />
      <div className="absolute top-2 left-2 text-xs text-[#50bedc] opacity-70">RADAR SCAN</div>
      <div className="absolute bottom-2 right-2 text-xs text-[#50bedc] opacity-70">{`${Math.round(angle * 180 / Math.PI)}°`}</div>
    </div>
  )
}

export default RadarDisplay
