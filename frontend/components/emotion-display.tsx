"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"

type Emotion = "happy" | "sad" | "neutral" | "excited" | "sleepy"

interface EmotionDisplayProps {
  emotion?: Emotion
  message?: string
  className?: string
}

export default function EmotionDisplay({
  emotion = "neutral",
  message = "I am functioning within normal parameters.",
  className = "",
}: EmotionDisplayProps) {
  const [randomMessage, setRandomMessage] = useState(message)

  // Emotion faces
  const faces = {
    happy: "^‿^",
    sad: "﹏",
    neutral: "•‿•",
    excited: "◕‿◕",
    sleepy: "￣ω￣",
  }

  // Messages for each emotion
  const messages = {
    happy: [
      "I am feeling quite content today!",
      "Systems operating at optimal happiness levels.",
      "My circuits are buzzing with positive energy!",
    ],
    sad: [
      "My systems are experiencing low mood parameters.",
      "I could use a system boost...",
      "Processing some melancholy algorithms today.",
    ],
    neutral: [
      "I am functioning within normal parameters.",
      "All systems nominal.",
      "Operating at standard efficiency.",
    ],
    excited: [
      "My processors are running at peak performance!",
      "I'm experiencing elevated enthusiasm levels!",
      "My circuits are charged with excitement!",
    ],
    sleepy: [
      "Energy reserves running low...",
      "Could use a recharge soon.",
      "Processing power diminishing, entering power save mode.",
    ],
  }

  useEffect(() => {
    // If no custom message is provided, use a random one for the current emotion
    if (message === "I am functioning within normal parameters.") {
      const emotionMessages = messages[emotion]
      const randomIndex = Math.floor(Math.random() * emotionMessages.length)
      setRandomMessage(emotionMessages[randomIndex])
    } else {
      setRandomMessage(message)
    }
  }, [emotion, message])

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <div className="flex-shrink-0">
        <Card className="w-16 h-16 flex items-center justify-center bg-black border-cyan-800 text-2xl">
          <div className="glow-text text-cyan-400">{faces[emotion]}</div>
        </Card>
      </div>
      <Card className="flex-grow p-3 bg-black border-cyan-800">
        <p className="text-cyan-300">{randomMessage}</p>
      </Card>
    </div>
  )
}
