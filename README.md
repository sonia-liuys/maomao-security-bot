# MaoMao Security Robot System Guide

## System Overview

MaoMao Security Robot is a multifunctional security patrol robot that combines AI visual recognition, various sensors, and multiple servo motors to perform security monitoring tasks in different environments.

### Hardware Components

- **Control System**: Raspberry Pi 5 and Arduino
- **Motion System**: 9 servo motors (controlling eyes, eyelids, neck, and arms)
- **Vision System**: Camera with Google Teachable Machine for AI visual recognition
- **Other Sensors**: distance sensors

## System Functions

MaoMao Security Robot has three main operating modes:

1. **Manual Mode**:
   - Directly control the robot's movement and actions through the web interface
   - Suitable for scenarios requiring precise control

2. **Patrol Mode**:
   - Robot automatically patrols within a designated area
   - Records and reports any anomalies detected

3. **Surveillance Mode**:
   - Robot remains stationary at a fixed position for monitoring
   - Uses AI visual recognition to identify specific faces and student IDs
   - Triggers alerts when anomalies are detected

### Additional Features

4. **Voice Interaction System**:
   - Chinese voice recognition and response
   - Multi-AI service support (OpenAI, Claude, Gemini, local Ollama)
   - Intelligent mood analysis system
   - Real-time emotion detection and response adaptation

5. **Biometric Monitoring**:
   - Body temperature monitoring
   - Heart rate monitoring
   - Health status tracking

## System Architecture

The entire system is divided into frontend and backend components:

### Frontend

The frontend is developed using the Next.js framework, providing an intuitive user interface that allows users to:

- Switch between the robot's operating modes
- View the robot's camera feed
- Manually control the robot's movement and actions
- Monitor the robot's system status (temperature, battery, etc.)

### Backend

The backend is developed in Python and is responsible for controlling all the robot's functions:

- **Core Control**: Coordinates the work of various subsystems
- **Visual Processing**: Processes camera images and performs AI recognition
- **Motion Control**: Controls the robot's movement and servo motors
- **Communication System**: Exchanges data with the frontend
- **Safety Monitoring**: Monitors system status to prevent overheating and other issues

## Code Structure

The project is organized into several main modules:

### Backend Code Structure

```
backend/
├── main.py                     # Main program that starts the entire system
├── config.json                 # System configuration
├── core/                       # Core control
│   └── robot_controller.py     # Main robot controller
├── vision/                     # Vision system
│   └── vision_system.py        # Vision processing and AI recognition
├── movement/                   # Movement system
│   ├── movement_controller.py  # Movement controller
│   └── mobility_control/       # Arduino mobility control
│       └── mobility_control.ino
├── servo/                      # Servo motor control
│   ├── servo_controller.py     # Servo motor controller
│   ├── arduino_controller.py   # Arduino communication
│   └── arduino_led_controller/ # LED control firmware
│       └── arduino_led_controller.ino
├── communication/              # Communication system
│   └── websocket_server.py     # WebSocket server
├── safety/                     # Safety system
│   └── watchdog.py             # System monitor
├── modes/                      # Operating modes
│   └── mode_manager.py         # Mode management
├── models/                     # AI models
│   ├── teachable_machine_model.tflite  # Main AI model
│   ├── labels.txt              # Model labels
│   └── pose-model/             # Pose detection model
├── utils/                      # Utilities
│   ├── logger.py               # Logging system
│   ├── config_loader.py        # Configuration loader
│   ├── audio_player.py         # Audio playback
│   └── sound_manager.py        # Sound management
├── tools/                      # Development tools
│   └── camera_viewer.py        # Camera testing tool
└── logs/                       # System logs
```

### Frontend Code Structure

```
frontend/
├── app/                        # Next.js app directory
│   ├── page.tsx                # Main page
│   ├── layout.tsx              # App layout
│   ├── home/                   # Home page (Patrol mode)
│   ├── remote/                 # Remote control page (Manual mode)
│   ├── safety/                 # Safety monitoring page (Surveillance mode)
│   ├── patrol/                 # Patrol mode interface
│   ├── test/                   # Test pages
│   ├── video-test/             # Video testing
│   └── video-basic/            # Basic video display
├── components/                 # React components
│   ├── ui/                     # UI components (shadcn/ui)
│   ├── navigation.tsx          # Navigation component
│   ├── battery-indicator.tsx   # Battery status
│   ├── emotion-display.tsx     # Emotion display
│   ├── radar-display.tsx       # Radar visualization
│   └── face-coordinates-table.tsx # Face detection display
├── hooks/                      # Custom React hooks
│   ├── useRobotConnection.js   # Robot connection management
│   └── use-toast.ts            # Toast notifications
├── lib/                        # Utilities
│   └── utils.ts                # Helper functions
└── public/                     # Static resources
```

### Additional Modules

```
robot_bio_monitor/              # Biometric monitoring
├── __init__.py
├── body_temperature_monitor.py # Temperature monitoring
└── heartrate_monitor.py        # Heart rate monitoring

robot_conversation/             # Voice interaction system
├── voice_assistant.py          # Main voice assistant
├── setup_ai.py                 # AI service configuration
├── mood_commands.py            # Emotion analysis
├── requirements.txt            # Python dependencies
└── README.md                   # Voice system documentation

robot_movement/                 # Movement control firmware
├── __init__.py
├── mobility_control.ino        # Basic mobility control
└── mobility_control_R4.ino     # Arduino R4 mobility control

sound/                          # Audio assets
├── robot.wav                   # Basic robot sounds
├── robot-bass.wav
├── robot-compute.wav
├── robot-happy1.wav
├── robot-happy2.wav
└── robot-happy3.wav
```

## Data Flow

1. **User Operation**: User sends commands through the frontend interface
2. **Frontend Processing**: Frontend formats commands and sends them to the backend via WebSocket
3. **Backend Processing**:
   - WebSocket server receives commands
   - Core controller parses commands and calls the appropriate subsystems
   - Executes commands (e.g., movement, taking photos, switching modes)
4. **Status Return**: Backend sends execution results and robot status back to the frontend via WebSocket
5. **Frontend Display**: Frontend updates the interface to display the latest robot status and video feed

## Starting the System

1. **Start the Backend**:
   ```
   cd backend
   python main.py
   ```

2. **Start the Frontend**:
   ```
   cd frontend
   npm run dev
   ```

3. **Access the Interface**: Open a browser and visit http://localhost:3000

## Important Notes

- The system is designed to run in both Mac development environment and Raspberry Pi deployment environment
- When running on Raspberry Pi, ensure all necessary dependencies are installed
- Temperature monitoring feature prevents system overheating
- Movement control has safety limits to prevent collisions
- The system uses WebSocket for real-time communication between frontend and backend
