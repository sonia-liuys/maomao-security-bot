"use client"

import { useState, useEffect } from "react"

export default function ClockDisplay() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date())
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
  }

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    })
  }

  return (
    <div className="text-center">
      <div className="text-4xl font-mono text-cyan-400 glow-text">{formatTime(time)}</div>
      <div className="text-lg text-cyan-300">{formatDate(time)}</div>
    </div>
  )
}
