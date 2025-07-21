"use client"

import { useState, useEffect, useRef } from "react"
import styles from './page.module.css'
import useRobotConnection from '@/hooks/useRobotConnection'
import { Card } from "@/components/ui/card"
import Navigation from "@/components/navigation"
import { Shield, Check, AlertTriangle, Play, Square, Bell } from "lucide-react"
import { Button } from "@/components/ui/button"

// Define emotion types
type Emotion = "happy" | "sad" | "neutral" | "excited" | "sleepy" | "suspicious" | "angry"

// Define robot status type
interface RobotStatus {
  face_detected?: boolean;
  recognized_person?: string;
  confidence?: number;
  mode?: string;
  current_mode?: string;
  [key: string]: any; // Allow other properties
}

// Define recognition result message type
interface RobotMessage {
  type: string;
  data: {
    eye_color?: string;
    emoji?: string;
    recognized?: boolean;
    name?: string;
    confidence?: number;
    message?: string;
    countdown?: number;
    mode?: string;
    current_mode?: string;
  };
}

export default function SafetyMode() {
  // State variables
  const [currentEmotion, setCurrentEmotion] = useState<Emotion>("neutral")
  const [securityLevel, setSecurityLevel] = useState("Normal")
  const [threatDetected, setThreatDetected] = useState(false)
  const [statusMessage, setStatusMessage] = useState("Ready to start security mode")
  const [recognizedPerson, setRecognizedPerson] = useState<string | null>(null)
  const [eyeColor, setEyeColor] = useState<string>("green")
  const [currentEmoji, setCurrentEmoji] = useState<string>("😐")
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<any>(null)
  const [emojiSize, setEmojiSize] = useState(350) // Default emoji size
  const [intruderDetected, setIntruderDetected] = useState(false)
  const [alarmActive, setAlarmActive] = useState(false)
  const [warningStage, setWarningStage] = useState(0) // 0: none, 1: warning, 2: alarm
  
  // Track if we've sent any commands
  const hasSentCommandRef = useRef(false)
  
  // Use robot connection hook
  const { isConnected: robotConnected, lastMessage: robotLastMessage, sendCommand: sendRobotCommand, robotStatus } = useRobotConnection('ws://security-bot.local:8765');
  
  // Cast robotStatus to our defined type
  const typedRobotStatus = robotStatus as RobotStatus;
  
  // Monitor robot connection - no automatic mode change
  useEffect(() => {
    if (robotConnected) {
      console.log('Connected to robot');
      // No automatic mode switching - wait for user to press the start button
      // This follows the user preference for manual mode control
    }
  }, [robotConnected]);
  
  // Start security mode function
  const startSurveillanceMode = () => {
    if (!hasSentCommandRef.current) {
      console.log('Switching to Security Mode');
      // Send command to switch mode
      sendRobotCommand({
        type: 'set_mode',
        data: { mode: 'SURVEILLANCE' } // Use uppercase to match enum values in backend
      });
      hasSentCommandRef.current = true;
      setStatusMessage("Security Mode Started");
      
      // Request status and start facial recognition
      setTimeout(() => {
        console.log('Requesting status update and starting face recognition');
        // Request current status
        sendRobotCommand({
          type: 'get_status',
          data: {}
        });
        
        // Explicitly start face recognition
        sendRobotCommand({
          type: 'start_recognition',
          data: {}
        });
      }, 1000);
    }
  };
  
  // Security warning and alarm functions
  const triggerSecurityWarning = (personName: string): void => {
    console.log(`Unauthorized person detected: ${personName} - initiating security protocol`);
    
    // Set intruder detected flag
    setIntruderDetected(true);
    
    // Start with warning stage
    setWarningStage(1);
    
    // Send security warning to robot
    sendRobotCommand({
      type: 'set_eye_color',
      data: { color: 'yellow' }
    });

    // Escalate to full alarm after a delay if intruder is still present
    setTimeout(() => {
      if (intruderDetected) {
        console.log(`Intruder still present: ${personName} - escalating to full alarm`);
        triggerSecurityAlarm(personName);
      }
    }, 5000); // 5 seconds warning before full alarm
  };
  
  // This function triggers the full security alarm
  const triggerSecurityAlarm = (personName: string): void => {
    // Only escalate if intruder is still detected
    if (!intruderDetected) return;
    
    console.log(`Triggering full security alarm for intruder: ${personName}`);
    
    // Activate alarm state
    setAlarmActive(true);
    setWarningStage(2);
    setSecurityLevel('Alarm');
    setEyeColor('red');
    setStatusMessage(`INTRUDER ALERT: ${personName}`);
    
    // Send alarm command to robot
    sendRobotCommand({
      type: 'trigger_alarm',
      data: { name: personName }
    });
  };
  
  // Function to clear the security alarm
  const clearSecurityAlarm = () => {
    console.log('Clearing security alarm');
    setIntruderDetected(false);
    setAlarmActive(false);
    setWarningStage(0);
    setSecurityLevel('Normal');
    setEyeColor('green');
    setStatusMessage('Security alarm cleared');
    
    // Send clear alarm command to robot
    sendRobotCommand({
      type: 'clear_alarm',
      data: {}
    });
    
    // Update the robot mode to Normal to ensure ESP32 client gets updated
    setTimeout(() => {
      console.log('Setting mode to Normal after alarm clear');
      sendRobotCommand({
        type: 'set_eye_color',
        data: { color: 'green' }
      });
      
      // Also explicitly send a normal mode command
      sendRobotCommand({
        type: 'set_mode',
        data: { mode: 'NORMAL' }
      });
    }, 300); // Small delay to ensure commands are processed in order
  };
  
  // End security mode function
  const stopSurveillanceMode = () => {
    console.log('Ending security mode');
    
    // Clear any active alarms first
    if (alarmActive || intruderDetected) {
      clearSecurityAlarm();
    }
    
    sendRobotCommand({
      type: 'set_mode',
      data: { mode: 'idle' }
    });
    hasSentCommandRef.current = false;
    setStatusMessage("Security Mode Stopped");
  };

  // Map of emotions to emoji
  const emotionEmoji: Record<Emotion, string> = {
    "happy": "😃",
    "sad": "😢",
    "neutral": "😐",
    "excited": "😮",
    "sleepy": "😴",
    "suspicious": "🤨",
    "angry": "😠"
  };

  // Monitor robot status for face detection and recognition
  useEffect(() => {
    if (!typedRobotStatus) return;
    
    // Check if face detection is active
    if (typedRobotStatus.face_detected) {
      console.log('Face detected:', typedRobotStatus);
      setStatusMessage("Face detected - analyzing...");
    }
    
    // Check if a person has been recognized
    if (typedRobotStatus.recognized_person) {
      const confidence = typedRobotStatus.confidence || 0;
      console.log('Person recognized from status:', typedRobotStatus.recognized_person, 'with confidence:', confidence);
      setRecognizedPerson(typedRobotStatus.recognized_person);
      
      // Check if the recognized person is authorized (Sonia) with high confidence
      if (typedRobotStatus.recognized_person.toLowerCase() === 'sonia' && confidence > 0.95) {
        // Authorized person detected with high confidence
        setCurrentEmotion('happy');
        setThreatDetected(false);
        setSecurityLevel('Normal');
        setStatusMessage(`Authorized: ${typedRobotStatus.recognized_person} (${(confidence * 100).toFixed(1)}%)`);
        // Reset eye color to green for authorized person
        setEyeColor('green');
      } else if (typedRobotStatus.recognized_person.toLowerCase() === 'sonia' && confidence <= 0.95) {
        // Potential Sonia but confidence too low - treat as unauthorized
        setCurrentEmotion('suspicious');
        setThreatDetected(true);
        setSecurityLevel('Warning');
        setStatusMessage(`Low confidence recognition: ${typedRobotStatus.recognized_person} (${(confidence * 100).toFixed(1)}%)`);
        setEyeColor('yellow');
        
        // Trigger security warning with confidence info
        triggerSecurityWarning(`${typedRobotStatus.recognized_person} (${(confidence * 100).toFixed(1)}%)`);
      } else {
        // Clearly unauthorized person detected - trigger warning
        setCurrentEmotion('suspicious');
        setThreatDetected(true);
        setSecurityLevel('Warning');
        setStatusMessage(`Unauthorized: ${typedRobotStatus.recognized_person} (${(confidence * 100).toFixed(1)}%)`);
        // Set eye color to yellow for warning
        setEyeColor('yellow');
        
        // Trigger security warning
        triggerSecurityWarning(typedRobotStatus.recognized_person);
      }
    }
  }, [typedRobotStatus]);

  // Monitor messages from robot
  useEffect(() => {
    try {
      if (!robotLastMessage) {
        return;
      }
      
      console.log('Received message:', robotLastMessage);
      setLastMessage(robotLastMessage);
      
      // Handle recognition results
      const message = robotLastMessage as RobotMessage;
      
      if (message.type === 'status_update' || message.type === 'status') {
        // Check if we're in surveillance mode as expected
        const statusData = message.data as unknown as { mode?: string; current_mode?: string };
        if (statusData?.mode === 'SURVEILLANCE' || statusData?.current_mode === 'SURVEILLANCE') {
          console.log('Confirmed in Security Control mode');
        }
      } else if (message.type === 'recognition_result') {
        console.log('Recognition result received:', message);
        
        const data = message.data;
        
        // Update eye color
        if (data && data.eye_color) {
          setEyeColor(data.eye_color);
        }
        
        // Update emoji
        if (data && data.emoji) {
          setCurrentEmoji(data.emoji);
        }
        
        // Update recognition status with confidence check
        const confidence = data.confidence || 0;
        if (data.recognized) {
          setRecognizedPerson(data.name || null);
          
          // Check if this is Sonia with high confidence
          if (data.name && data.name.toLowerCase() === 'sonia' && confidence > 0.95) {
            // High confidence Sonia recognition
            setCurrentEmotion('happy');
            setThreatDetected(false);
            setSecurityLevel('Normal');
            setStatusMessage(`Authorized: ${data.name} (${(confidence * 100).toFixed(1)}%)`);
          } else if (data.name && data.name.toLowerCase() === 'sonia' && confidence <= 0.95) {
            // Low confidence Sonia - treat as potential intruder
            setCurrentEmotion('suspicious');
            setThreatDetected(true);
            setSecurityLevel('Warning');
            setStatusMessage(`Low confidence: ${data.name} (${(confidence * 100).toFixed(1)}%)`);
            
            // Trigger security warning for low confidence Sonia
            triggerSecurityWarning(`${data.name} (low confidence: ${(confidence * 100).toFixed(1)}%)`);
          } else {
            // Not Sonia - unauthorized person
            setCurrentEmotion('suspicious');
            setThreatDetected(true);
            setSecurityLevel('Warning');
            setStatusMessage(`Unauthorized: ${data.name} (${(confidence * 100).toFixed(1)}%)`);
            
            // Trigger security warning
            triggerSecurityWarning(data.name || 'Unknown person');
          }
        } else {
          // No recognition at all
          setCurrentEmotion('suspicious');
          setThreatDetected(true);
          setSecurityLevel('Alert');
          setRecognizedPerson(null);
          setStatusMessage(data.message || 'Unrecognized person detected!');
        }
      }
    } catch (error) {
      console.error('Error processing message:', error);
    }
  }, [robotLastMessage]);
  
  return (
    <div className="flex flex-col h-screen">
      {/* Navigation component at the top */}
      <Navigation />
      
      {/* Main content */}
      <main className="flex-grow p-4">
        <Card className="w-full h-full flex flex-col p-4">
          <h1 className="text-2xl font-bold mb-4">Security Control</h1>
          
          <div className="flex-grow flex flex-col items-center justify-center">
            {/* Robot face display */}
            {/* Robot face display with prominent name */}
            <div className="relative flex items-center flex-col mb-8">
              {/* Main display area with emoji and name */}
              <div className="flex items-center mb-4">
                {/* Emoji container */}
                <div 
                  className={`relative flex items-center justify-center rounded-full ${
                    alarmActive ? "animate-pulse bg-red-900/30" : 
                    intruderDetected ? "animate-pulse bg-yellow-900/30" : 
                    "bg-blue-900/20"
                  }`}
                  style={{ 
                    width: `${emojiSize}px`, 
                    height: `${emojiSize}px`, 
                    boxShadow: `0 0 30px ${
                      eyeColor === "red" ? "rgba(255, 0, 0, 0.6)" : 
                      eyeColor === "yellow" ? "rgba(255, 255, 0, 0.6)" : 
                      "rgba(0, 255, 0, 0.4)"
                    }`
                  }}
                >
                  <div style={{ fontSize: `${emojiSize * 0.6}px` }}>
                    {currentEmoji || emotionEmoji[currentEmotion]}
                  </div>
                </div>
              </div>
              
              {/* Prominent name badge - always visible even if empty */}
              <div 
                className={`mt-2 py-3 px-8 rounded-full text-2xl font-bold text-center ${
                  !recognizedPerson ? "bg-gray-800/50 text-gray-400" :
                  intruderDetected ? "bg-red-900/80 text-red-100 border-2 border-red-500" : 
                  "bg-green-900/80 text-green-100 border-2 border-green-500"
                }`}
                style={{
                  minWidth: '70%',
                  maxWidth: '90%'
                }}
              >
                <div className="flex items-center justify-center space-x-3">
                  {recognizedPerson ? (
                    intruderDetected ? (
                      <AlertTriangle className="h-6 w-6" />
                    ) : (
                      <Check className="h-6 w-6" />
                    )
                  ) : (
                    <span className="h-6 w-6" />
                  )}
                  <span>{recognizedPerson || "No user detected"}</span>
                </div>
              </div>
            </div>
            
            {/* Security Status display */}
            <div className={`mb-4 text-center p-3 rounded-md ${
              securityLevel === "Alarm" ? "bg-red-900/30 text-red-500 border border-red-700" : 
              securityLevel === "Warning" ? "bg-yellow-900/30 text-yellow-500 border border-yellow-700" : 
              "bg-green-900/30 text-green-500 border border-green-700"
            }`}>
              <div className="text-xl font-bold flex items-center justify-center">
                {securityLevel === "Alarm" && <AlertTriangle className="mr-2 h-5 w-5" />}
                Security Status: {securityLevel}
              </div>
              <div className="mt-2 text-lg">{statusMessage}</div>
            </div>
            
            {/* Person recognition info with confidence */}
            {recognizedPerson && (
              <div className={`mb-6 p-4 border-2 rounded-md ${
                intruderDetected ? "border-red-400 bg-red-900/20" : "border-green-400 bg-green-900/20"
              }`}>
                <div className={`text-xl font-semibold text-center ${intruderDetected ? "text-red-400" : "text-green-400"}`}>
                  Identity: {recognizedPerson}
                </div>
                
                {/* Confidence meter */}
                <div className="mt-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span>Confidence:</span>
                    <span className={`font-mono ${typedRobotStatus.confidence && typedRobotStatus.confidence > 0.95 ? "text-green-400" : "text-yellow-400"}`}>
                      {typedRobotStatus.confidence ? `${(typedRobotStatus.confidence * 100).toFixed(1)}%` : "Unknown"}
                    </span>
                  </div>
                  
                  {/* Progress bar for confidence */}
                  <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${typedRobotStatus.confidence && typedRobotStatus.confidence > 0.95 ? "bg-green-500" : "bg-yellow-500"}`}
                      style={{ width: `${typedRobotStatus.confidence ? Math.min(typedRobotStatus.confidence * 100, 100) : 0}%` }}
                    ></div>
                  </div>
                </div>
                
                {/* Authorization status */}
                <div className="flex justify-center mt-3">
                  <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${intruderDetected ? "bg-red-800 text-white" : "bg-green-800 text-white"}`}>
                    {intruderDetected ? "UNAUTHORIZED" : "AUTHORIZED"}
                  </span>
                </div>
                
                {/* Threshold indicator */}
                <div className="text-xs text-center mt-2 text-gray-400">
                  {recognizedPerson.toLowerCase() === 'sonia' && typedRobotStatus.confidence && typedRobotStatus.confidence <= 0.95 && 
                    "Confidence below 95% threshold - access denied"}
                </div>
              </div>
            )}
            
            {/* Control buttons */}
            <div className="flex flex-col items-center">
              {/* Start Security Mode button */}
              {!hasSentCommandRef.current && (
                <Button 
                  className="bg-green-700 hover:bg-green-800 text-white p-4 h-16 w-64 mb-4"
                  onClick={startSurveillanceMode}
                >
                  <div className="flex items-center justify-center w-full">
                    <Play className="h-6 w-6 mr-2" />
                    <span className="text-lg">Start Security Mode</span>
                  </div>
                </Button>
              )}
              
              {/* End Security Mode button */}
              {hasSentCommandRef.current && (
                <Button 
                  className="bg-red-700 hover:bg-red-800 text-white p-4 h-16 w-64 mb-4"
                  onClick={stopSurveillanceMode}
                >
                  <div className="flex items-center justify-center w-full">
                    <Square className="h-6 w-6 mr-2" />
                    <span className="text-lg">End Security Mode</span>
                  </div>
                </Button>
              )}
              
              {/* Alarm clear button - only shown when alarm is active */}
              {alarmActive && (
                <Button 
                  className="bg-yellow-600 hover:bg-yellow-700 text-white p-3 h-14 w-64"
                  onClick={clearSecurityAlarm}
                >
                  <div className="flex items-center justify-center w-full">
                    <AlertTriangle className="h-5 w-5 mr-2" />
                    <span className="text-lg">Clear Alarm</span>
                  </div>
                </Button>
              )}
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
}
