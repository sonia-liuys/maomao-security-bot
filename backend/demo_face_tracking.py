#!/usr/bin/env python3
"""
Demo script for face tracking and eye color feedback.
- Tracks human face using the camera.
- If no face is detected, turns eye color to green.
- If a face is detected, turns eye color to yellow and tracks the face.
"""
import time
from vision.vision_system import VisionSystem
from servo.servo_controller import ServoController
from utils import config_loader
from utils.sound_manager import SoundManager


def main():
    # Load config (modify as needed)
    config_loader_inst = config_loader.ConfigLoader()
    config = config_loader_inst.load_config()
    vision = VisionSystem(config.get('vision', {}))
    servo = ServoController(config.get('servo', {}))
    sound_manager = SoundManager()

    print("[INFO] Starting vision system...")
    vision.start()
    time.sleep(1)  # Give camera time to warm up

    # --- Servo sweep demo ---
    print("[INFO] Sweeping eye/neck to leftmost...")
    servo.follow_face(0.0, 0.5)
    time.sleep(1.2)
    print("[INFO] Sweeping eye/neck to rightmost...")
    servo.follow_face(1.0, 0.5)
    time.sleep(1.2)
    print("[INFO] Centering eye/neck...")
    servo.follow_face(0.5, 0.5)
    time.sleep(0.8)

    print("[INFO] Starting face tracking demo. Press Ctrl+C to exit.")
    # Thinking sound control
    last_thinking_sound_time = 0
    last_face_detected = False
    try:
        while True:
            vision_data = vision.get_latest_data()
            face_detected = vision_data.get("face_detected", False)
            face_x = vision_data.get("face_x", 0.5)
            face_y = vision_data.get("face_y", 0.5)

            now = time.time()
            if face_detected:
                # Play thinking sound only once per detection, and at most every 10s
                if not last_face_detected and (now - last_thinking_sound_time > 10.0):
                    sound_manager.play_thinking_sound()
                    last_thinking_sound_time = now
                # Face detected: track and set eye to yellow
                servo.set_eye_color("yellow")
                servo.follow_face(face_x, face_y)
                print(f"[TRACKING] Face detected at x={face_x:.2f}, y={face_y:.2f}")
            else:
                # No face: set eye to green (idle)
                servo.set_eye_color("green")
                print("[IDLE] No face detected.")
            last_face_detected = face_detected
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n[INFO] Exiting demo...")
    finally:
        vision.stop()
        servo.set_eye_color("green")
        print("[INFO] Eye color reset to green. Vision system stopped.")


if __name__ == "__main__":
    main()
