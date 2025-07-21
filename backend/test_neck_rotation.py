#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neck Rotation Test Script for MaoMao Robot
This script tests the rotation of the robot's neck using servo ID 7.
"""

import os
import sys
import time
import logging
import json
import argparse
import math
from servo.servo_controller import ServoController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("NeckRotationTest")

# Default config values
DEFAULT_CONFIG = {
    "update_interval": 0.05,
    "blink_interval_min": 2.0,
    "blink_interval_max": 6.0,
    "led_blink_interval_min": 1.0,
    "led_blink_interval_max": 3.0,
    "center_position": {
        "neck": 90
    },
    "min_position": {
        "neck": 0 
    },
    "max_position": {
        "neck": 180
    }
}

def load_config():
    """Load configuration from config.json or use defaults"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            logger.info("Config loaded from config.json")
            return config
    except Exception as e:
        logger.warning(f"Could not load config.json: {e}. Using default config.")
        return DEFAULT_CONFIG

def test_smooth_rotation(servo_controller, pattern="sweep", cycles=3, delay=1.0, step_size=2):
    """
    Test neck rotation with different patterns
    
    Args:
        servo_controller: The initialized servo controller
        pattern: The rotation pattern ("sweep", "sine", "random")
        cycles: Number of cycles to repeat the pattern
        delay: Delay between movements in seconds
        step_size: Step size for smooth movements (smaller = smoother but slower)
    """
    logger.info(f"Starting neck rotation test using pattern: {pattern}")
    
    center_pos = 90  # Center position (looking straight ahead)
    min_pos = 30     # Minimum safe position
    max_pos = 150    # Maximum safe position
    
    try:
        # First reset to center
        logger.info(f"Centering neck at position {center_pos}")
        servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos)
        time.sleep(delay)
        
        for cycle in range(cycles):
            logger.info(f"Starting cycle {cycle+1}/{cycles}")
            
            if pattern == "sweep":
                # Simple sweep from left to right and back
                logger.info(f"Moving neck to left position {min_pos}")
                servo_controller.move_servo_smooth(ServoController.SERVO_NECK, min_pos, step_size=step_size)
                time.sleep(delay)
                
                logger.info(f"Moving neck to right position {max_pos}")
                servo_controller.move_servo_smooth(ServoController.SERVO_NECK, max_pos, step_size=step_size)
                time.sleep(delay)
                
                logger.info(f"Moving neck to center position {center_pos}")
                servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos, step_size=step_size)
                time.sleep(delay)
                
            elif pattern == "sine":
                # Sinusoidal pattern for smoother movement
                logger.info("Starting sine pattern movement")
                steps = 20
                for i in range(steps):
                    # Calculate position using sine wave
                    angle = (max_pos - min_pos) / 2 * math.sin(2 * math.pi * i / steps)
                    position = center_pos + angle
                    logger.debug(f"Sine position: {position:.1f}")
                    servo_controller.set_position(ServoController.SERVO_NECK, position)
                    time.sleep(delay / steps)
                
            elif pattern == "random":
                # Random positions
                import random
                for _ in range(4):  # 4 random positions per cycle
                    position = random.uniform(min_pos, max_pos)
                    logger.info(f"Moving to random position {position:.1f}")
                    servo_controller.move_servo_smooth(ServoController.SERVO_NECK, position, step_size=step_size)
                    time.sleep(delay / 2)
            
            logger.info(f"Completed cycle {cycle+1}/{cycles}")
            
        # Return to center at the end
        logger.info("Test completed, returning to center position")
        servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos, step_size=step_size)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        # Make sure to center the neck when interrupted
        servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos, step_size=10)
    except Exception as e:
        logger.error(f"Error during neck rotation test: {e}")
        # Make sure to center the neck in case of error
        try:
            servo_controller.set_position(ServoController.SERVO_NECK, center_pos)
        except:
            pass

def test_manual_positions(servo_controller, positions, delay=1.0):
    """
    Test specific neck positions
    
    Args:
        servo_controller: The initialized servo controller
        positions: List of positions to test
        delay: Delay between positions
    """
    logger.info(f"Testing manual positions: {positions}")
    center_pos = 90
    
    try:
        # First reset to center
        logger.info(f"Centering neck at position {center_pos}")
        servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos)
        time.sleep(delay)
        
        for i, position in enumerate(positions):
            position = float(position)
            logger.info(f"Moving to position {i+1}/{len(positions)}: {position}")
            servo_controller.move_servo_smooth(ServoController.SERVO_NECK, position)
            time.sleep(delay)
            
        # Return to center at the end
        logger.info("Test completed, returning to center position")
        servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        # Make sure to center the neck when interrupted
        servo_controller.move_servo_smooth(ServoController.SERVO_NECK, center_pos)
    except Exception as e:
        logger.error(f"Error during neck position test: {e}")
        # Make sure to center the neck in case of error
        try:
            servo_controller.set_position(ServoController.SERVO_NECK, center_pos)
        except:
            pass

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test robot neck rotation')
    parser.add_argument('--pattern', choices=['sweep', 'sine', 'random'], default='sweep',
                        help='Rotation pattern to test')
    parser.add_argument('--cycles', type=int, default=3,
                        help='Number of rotation cycles to perform')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between movements in seconds')
    parser.add_argument('--step', type=float, default=2,
                        help='Step size for smooth movements (smaller = smoother but slower)')
    parser.add_argument('--positions', type=str,
                        help='Comma-separated specific positions to test (e.g., "45,90,135")')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Initialize servo controller
    logger.info("Initializing servo controller...")
    servo_controller = ServoController(config)
    
    try:
        # Start the servo controller
        servo_controller.start()
        time.sleep(1)  # Give it time to initialize
        
        # Run the tests
        if args.positions:
            positions = [float(pos) for pos in args.positions.split(',')]
            test_manual_positions(servo_controller, positions, args.delay)
        else:
            test_smooth_rotation(servo_controller, args.pattern, args.cycles, args.delay, args.step)
            
    finally:
        # Stop the servo controller
        logger.info("Stopping servo controller...")
        servo_controller.stop()

if __name__ == "__main__":
    main()
