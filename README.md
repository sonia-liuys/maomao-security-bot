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

### Backend Code Structure

```
backend/
├── main.py                  # Main program that starts the entire system
├── config/                  # Configuration files
│   └── settings.py          # System settings
├── core/                    # Core control
│   ├── robot_controller.py  # Main robot controller
│   └── mode_manager.py      # Mode manager
├── vision/                  # Vision system
│   ├── camera.py            # Camera control
│   └── recognition.py       # AI recognition
├── movement/                # Movement system
│   └── movement_controller.py # Movement controller
├── servo/                   # Servo motor control
│   └── servo_controller.py  # Servo motor controller
├── communication/           # Communication system
│   └── websocket_server.py  # WebSocket server
└── safety/                  # Safety system
    └── watchdog.py          # System monitor
```

### Frontend Code Structure

```
frontend/
├── app/                     # Page components
│   ├── home/                # Home page (Patrol mode)
│   ├── remote/              # Remote control page (Manual mode)
│   └── safety/              # Safety monitoring page (Surveillance mode)
├── components/              # UI components
│   ├── ControlPanel.js      # Control panel
│   ├── VideoFeed.js         # Video feed
│   └── StatusDisplay.js     # Status display
├── hooks/                   # Custom hooks
│   └── useRobotConnection.js # Robot connection management
└── public/                  # Static resources
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
