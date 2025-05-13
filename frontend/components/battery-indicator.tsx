"use client"

import { Battery } from "lucide-react"
import { useState, useEffect } from "react"

interface BatteryIndicatorProps {
  initialLevel?: number
  charging?: boolean
}

export default function BatteryIndicator({ initialLevel = 75, charging = false }: BatteryIndicatorProps) {
  const [level, setLevel] = useState(initialLevel)
  const [isCharging, setIsCharging] = useState(charging)

  // Simulate battery drain
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isCharging && level > 0) {
        setLevel((prev) => Math.max(prev - 0.01, 0))
      } else if (isCharging && level < 100) {
        setLevel((prev) => Math.min(prev + 0.05, 100))
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [level, isCharging])

  // Calculate estimated runtime based on battery level
  const getEstimatedRuntime = () => {
    // Assuming 100% battery gives 60 minutes runtime
    const minutes = Math.floor(level * 0.6)
    return `${minutes} MIN`
  }

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center">
          <Battery className="h-5 w-5 mr-2 text-[#50bedc]" />
          <span className="text-[#50bedc] font-mono">Power Status</span>
        </div>
        <span className="text-[#50bedc] font-mono bg-[#0a1520] px-2 py-1 rounded-full text-sm border border-[#50bedc]/30">
          {Math.floor(level)}%
        </span>
      </div>

      <div className="w-full h-2 bg-[#1a2530] rounded-full overflow-hidden">
        <div className="progress-bar" style={{ width: `${level}%` }}></div>
      </div>

      <div className="flex justify-between mt-2">
        <div className="text-[#50bedc]/80 text-xs font-mono">ESTIMATED RUNTIME: {getEstimatedRuntime()}</div>
        <div className="text-[#50bedc]/80 text-xs font-mono">POWER USAGE: NORMAL</div>
      </div>
    </div>
  )
}
