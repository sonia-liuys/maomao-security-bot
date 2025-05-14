"""
Sound Manager for MaoMao Security Robot

This module provides a high-level wrapper for playing different sound effects
based on robot states and events.
"""

import os
import logging
import subprocess
from pathlib import Path

class SoundManager:
    """
    Sound Manager for handling different robot sound effects.
    Provides a high-level interface to play sounds based on robot states.
    """
    
    def __init__(self, logger=None):
        """
        Initialize the SoundManager.
        
        Args:
            logger: Logger instance for logging messages
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Get the project root directory (3 levels up from this file)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
        
        # Sound directory path
        self.sound_dir = project_root / "sound"
        
        # Define sound mappings
        self.sounds = {
            "intruder": "robot-bass.wav",    # For intruder detection
            "happy": "robot.wav",            # For happy/success states
            "thinking": "robot-compute.wav", # For processing/thinking states
            "angry": "robot-bass.wav"             # For shutdown/angry event
        }
        
        # Verify sounds exist
        for sound_type, filename in self.sounds.items():
            sound_path = self.sound_dir / filename
            if not sound_path.exists():
                self.logger.warning(f"Sound file not found: {sound_path}")
    
    def play_sound(self, sound_type):
        """
        Play a sound based on the specified type.
        
        Args:
            sound_type: Type of sound to play ('intruder', 'happy', 'thinking')
            
        Returns:
            bool: True if sound played successfully, False otherwise
        """
        if sound_type not in self.sounds:
            self.logger.warning(f"Unknown sound type: {sound_type}")
            return False
            
        filename = self.sounds[sound_type]
        sound_path = self.sound_dir / filename
        
        if not sound_path.exists():
            self.logger.warning(f"Sound file not found: {sound_path}")
            return False
            
        try:
            self.logger.info(f"Playing sound: {sound_type} ({filename})")
            # Use afplay on macOS, aplay on Linux
            if os.name == 'posix':
                if os.uname().sysname == 'Darwin':  # macOS
                    subprocess.Popen(['afplay', str(sound_path)])
                else:  # Linux
                    subprocess.Popen(['aplay', '-q', str(sound_path)])
            else:
                self.logger.warning("Sound playback not supported on this platform")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Error playing sound: {e}")
            return False
    
    def play_intruder_sound(self):
        """Play the intruder detection sound"""
        return self.play_sound("intruder")
    
    def play_happy_sound(self):
        """Play the happy/success sound"""
        return self.play_sound("happy")
    
    def play_thinking_sound(self):
        """Play the thinking/processing sound"""
        return self.play_sound("thinking")


# Standalone function for backward compatibility
def play_sound(sound_path):
    """
    Play a sound file using the appropriate command for the platform.
    
    Args:
        sound_path: Path to the sound file
    """
    try:
        if os.name == 'posix':
            if os.uname().sysname == 'Darwin':  # macOS
                subprocess.Popen(['afplay', sound_path])
            else:  # Linux
                subprocess.Popen(['aplay', '-q', sound_path])
    except Exception as e:
        logging.error(f"Error playing sound: {e}")
