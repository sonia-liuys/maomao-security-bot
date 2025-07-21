"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  Power,
  Video,
  VideoOff,
  Scan,
  Play,
  Square,
  RotateCw
} from "lucide-react"
import Navigation from "@/components/navigation"
import useRobotConnection from "@/hooks/useRobotConnection"

export default function PatrolMode() {
  const [videoActive, setVideoActive] = useState(true)
  const [isPatrolling, setIsPatrolling] = useState(false)
  const [statusMessage, setStatusMessage] = useState("Ready to start patrol")
  const { isConnected, setRobotMode, sendCommand, lastMessage, robotStatus } = useRobotConnection()
  const [hasSentCommandRef, setHasSentCommandRef] = useState(false)

  // Switch to patrol mode
  useEffect(() => {
    if (isConnected && !hasSentCommandRef) {
      console.log("Connected to robot");
      // No longer auto-switch to patrol mode, waiting for user button click
    }
  }, [isConnected, hasSentCommandRef]);

  // Start Patrol Mode
  const startPatrolMode = () => {
    try {
      console.log("Switching to patrol mode");
      // Switch to patrol mode
      setRobotMode("PATROL");
      setHasSentCommandRef(true);
      setStatusMessage("Patrol Mode Started");
    } catch (error) {
      console.error("Failed to set mode:", error);
    }
  };
  
  // End Patrol Mode
  const stopPatrolMode = () => {
    try {
      console.log("Ending patrol mode");
      // First stop patrolling if currently active
      if (isPatrolling) {
        sendCommand({
          type: 'stop_patrol',
          data: {}
        });
      }
      
      // Switch to idle mode
      setRobotMode("IDLE");
      setHasSentCommandRef(false);
      setIsPatrolling(false);
      setStatusMessage("Patrol Mode Stopped");
    } catch (error) {
      console.error("Failed to stop mode:", error);
    }
  };

  // Listen for the latest message
  useEffect(() => {
    if (!lastMessage) return;
    
    try {
      // Check if this is a patrol status update message
      const message = lastMessage as { type: string; data: any };
      if (message && message.type === 'status_update') {
        const data = message.data;
        if (data && data.patrol_active !== undefined) {
          setIsPatrolling(data.patrol_active);
          setStatusMessage(data.patrol_active ? "Patrolling..." : "Patrol stopped");
        }
      }
    } catch (error) {
      console.error('Error processing message:', error);
    }
  }, [lastMessage]);

  const togglePatrol = () => {
    if (isPatrolling) {
      // Stop patrol
      sendCommand({
        type: 'stop_patrol',
        data: {}
      });
      setStatusMessage("Stopping patrol...");
    } else {
      // Start patrol
      sendCommand({
        type: 'start_patrol',
        data: {}
      });
      setStatusMessage("Starting patrol...");
    }
    // 預先更新UI狀態以提供即時反饋
    setIsPatrolling(!isPatrolling);
  };
  
  // Pause patrol function
  const pausePatrol = () => {
    // Send command to pause patrol
    sendCommand({
      type: 'stop_patrol',
      data: {}
    });
    setIsPatrolling(false);
    setStatusMessage("Patrol paused");
  };

  const toggleCamera = () => {
    setVideoActive(!videoActive);
    if (!videoActive) {
      sendCommand({
        type: "start_video_stream",
        data: {}
      });
    } else {
      sendCommand({
        type: "stop_video_stream",
        data: {}
      });
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 bg-[#050a10] text-white grid-bg">
      <Navigation />
      <Card className="w-full max-w-2xl bg-[#0a1520] border-[#50bedc]/30 p-6 flex flex-col mt-4">
        <div className="flex justify-between items-center mb-4">
          <div className="text-[#50bedc] text-lg">Patrol Mode</div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={toggleCamera} className="h-8 w-8 border-[#50bedc]/30 text-[#50bedc]">
              {videoActive ? <Video className="h-4 w-4" /> : <VideoOff className="h-4 w-4" />}
              <span className="sr-only">{videoActive ? "Turn off" : "Turn on"} camera</span>
            </Button>
          </div>
        </div>

        {/* Status Display */}
        <div className="mb-6 p-4 bg-[#0a1520] border border-[#50bedc]/30 rounded-md">
          <div className="text-[#50bedc] text-sm mb-2">Status</div>
          <div className="text-white">{statusMessage}</div>
          <div className="mt-2 flex items-center">
            <div className={`h-2 w-2 rounded-full ${isPatrolling ? "bg-green-500 animate-pulse" : "bg-gray-500"} mr-2`}></div>
            <span className="text-xs text-gray-400">{isPatrolling ? "Patrolling" : "Stopped"}</span>
          </div>
        </div>

        {/* Patrol Control Buttons */}
        <div className="grid grid-cols-1 gap-4 mb-4">
          {!hasSentCommandRef ? (
            <Button 
              className="bg-green-700 hover:bg-green-800 text-white p-4 h-16"
              onClick={startPatrolMode}
            >
              <div className="flex items-center justify-center w-full">
                <Play className="h-6 w-6 mr-2" />
                <span className="text-lg">Start Patrol Mode</span>
              </div>
            </Button>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {/* Start/Stop Patrol Button */}
              <Button 
                className={`${isPatrolling ? 'bg-orange-600 hover:bg-orange-700' : 'bg-green-700 hover:bg-green-800'} text-white p-4 h-16`}
                onClick={isPatrolling ? pausePatrol : togglePatrol}
              >
                <div className="flex items-center justify-center w-full">
                  {isPatrolling ? (
                    <>
                      <Square className="h-6 w-6 mr-2" />
                      <span className="text-lg">Pause Patrol</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-6 w-6 mr-2" />
                      <span className="text-lg">Begin Patrol</span>
                    </>
                  )}
                </div>
              </Button>
              
              {/* End Patrol Mode Button */}
              <Button 
                className="bg-red-700 hover:bg-red-800 text-white p-4 h-12 mt-2"
                onClick={stopPatrolMode}
              >
                <div className="flex items-center justify-center w-full">
                  <Square className="h-4 w-4 mr-2" />
                  <span className="text-md">End Patrol Mode</span>
                </div>
              </Button>
            </div>
          )}
        </div>

        {/* Other Control Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <Button className="bg-[#0a1520] hover:bg-[#152535] text-[#50bedc] p-3">
            <div className="flex flex-col items-center">
              <RotateCw className="h-5 w-5 mb-1" />
              <span className="text-sm">Rotate Patrol</span>
            </div>
          </Button>
          
          <Button className="bg-[#1a1520] hover:bg-[#251520] text-red-400 border-red-500/30 p-3">
            <div className="flex flex-col items-center">
              <Power className="h-5 w-5 mb-1" />
              <span className="text-sm">Power Off</span>
            </div>
          </Button>
        </div>
      </Card>
    </main>
  )
}
