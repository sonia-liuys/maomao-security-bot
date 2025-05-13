from time import sleep, time
from adafruit_servokit import ServoKit
import board
import neopixel_spi as neopixel
import random
import math

# Number of NeoPixels
num_pixels = 7

# Initialize the ServoKit for 16 channels (for the Adafruit Servo HAT)
kit = ServoKit(channels=16)

# Servo assignments
# 1: Eye servo
# 2: Neck servo (horizontal movement)
# 3-6: Arm servos
# 7-9: Reserved for future use

# Set initial positions
kit.servo[1].angle = 90  # Eye servo
kit.servo[2].angle = 90  # Neck servo
kit.servo[3].angle = 160 # Right arm upper
kit.servo[4].angle = 20  # Right arm lower
kit.servo[5].angle = 20  # Left arm upper
kit.servo[6].angle = 160 # Left arm lower

# Initialize NeoPixel LEDs
spi = board.SPI()
pixels = neopixel.NeoPixel_SPI(spi, num_pixels, pixel_order=neopixel.GRB, auto_write=False)

# Define colors
COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "yellow": (255, 255, 0),
    "off": (0, 0, 0)
}

# Set initial color (green)
current_color = "green"

# Set all pixels to the same color
def set_all_pixels(color):
    for i in range(num_pixels):
        pixels[i] = color
    pixels.show()

# Blink function
def blink_eyes():
    # Save current color
    saved_color = COLORS[current_color]
    
    # Turn off LEDs
    set_all_pixels(COLORS["off"])
    sleep(0.1)  # Eyes closed
    
    # Turn back on
    set_all_pixels(saved_color)
    pixels.show()

# Function to move a servo smoothly to a target angle
def move_servo_smooth(servo_num, target_angle, step_size=1, delay=0.02):
    current_angle = kit.servo[servo_num].angle
    steps = abs(target_angle - current_angle)
    
    for _ in range(steps):
        if current_angle < target_angle:
            current_angle += step_size
        else:
            current_angle -= step_size
            
        kit.servo[servo_num].angle = int(current_angle)
        sleep(delay)
        
        # Check for blink during movement
        check_for_blink_and_color()
    
    # Ensure we reach exactly the target angle
    kit.servo[servo_num].angle = target_angle

# Function to check if it's time to blink or change color
def check_for_blink_and_color():
    global next_blink_time, last_color_change, color_index, current_color
    
    current_time = time()
    
    # Check for color change
    if current_time - last_color_change > color_change_interval:
        color_index = (color_index + 1) % len(color_names)
        current_color = color_names[color_index]
        print(f"Changing eye color to: {current_color}")
        set_all_pixels(COLORS[current_color])
        last_color_change = current_time
    
    # Check for blink
    if current_time > next_blink_time:
        print("Blinking eyes")
        blink_eyes()
        next_blink_time = current_time + random.uniform(blink_interval_min, blink_interval_max)

# Function to generate natural-looking neck movement
def natural_neck_movement():
    # Generate a random target angle for the neck within a natural range
    target_angle = random.randint(70, 110)
    print(f"Moving neck to {target_angle} degrees")
    move_servo_smooth(2, target_angle, step_size=1, delay=0.03)

# Function to generate natural-looking arm movements
def natural_arm_movement():
    # Decide which arm to move (or both)
    arm_choice = random.choice(['left', 'right', 'both'])
    
    if arm_choice == 'right' or arm_choice == 'both':
        # Right arm movement (servos 3 and 4)
        upper_angle = random.randint(140, 170)
        lower_angle = random.randint(10, 40)
        print(f"Moving right arm: upper={upper_angle}, lower={lower_angle}")
        move_servo_smooth(3, upper_angle, step_size=2, delay=0.02)
        move_servo_smooth(4, lower_angle, step_size=2, delay=0.02)
    
    if arm_choice == 'left' or arm_choice == 'both':
        # Left arm movement (servos 5 and 6)
        upper_angle = random.randint(10, 40)
        lower_angle = random.randint(140, 170)
        print(f"Moving left arm: upper={upper_angle}, lower={lower_angle}")
        move_servo_smooth(5, upper_angle, step_size=2, delay=0.02)
        move_servo_smooth(6, lower_angle, step_size=2, delay=0.02)

# Function to make the robot perform a subtle idle animation
def idle_movement():
    # Small random movements to simulate breathing or subtle shifts
    # Slightly move neck
    current_neck = kit.servo[2].angle
    small_shift = random.randint(-5, 5)
    new_neck = max(70, min(110, current_neck + small_shift))
    move_servo_smooth(2, new_neck, step_size=1, delay=0.05)
    
    # Slightly adjust one arm
    if random.random() > 0.5:  # 50% chance to move an arm
        arm_side = random.choice(['left', 'right'])
        if arm_side == 'right':
            current_angle = kit.servo[3].angle
            small_shift = random.randint(-3, 3)
            new_angle = max(140, min(170, current_angle + small_shift))
            move_servo_smooth(3, new_angle, step_size=1, delay=0.05)
        else:
            current_angle = kit.servo[5].angle
            small_shift = random.randint(-3, 3)
            new_angle = max(10, min(40, current_angle + small_shift))
            move_servo_smooth(5, new_angle, step_size=1, delay=0.05)

# Set initial color
set_all_pixels(COLORS[current_color])

# Variables for color rotation and blinking
color_index = 0
color_names = ["green", "red", "yellow"]
color_change_interval = 5  # seconds
last_color_change = time()
last_blink_time = time()
blink_interval_min = 2  # minimum seconds between blinks
blink_interval_max = 6  # maximum seconds between blinks
next_blink_time = time() + random.uniform(blink_interval_min, blink_interval_max)

# Variables for natural movement timing
last_major_movement = time()
major_movement_interval_min = 8  # seconds
major_movement_interval_max = 15  # seconds
next_major_movement = time() + random.uniform(major_movement_interval_min, major_movement_interval_max)

last_idle_movement = time()
idle_movement_interval_min = 3  # seconds
idle_movement_interval_max = 7  # seconds
next_idle_movement = time() + random.uniform(idle_movement_interval_min, idle_movement_interval_max)

print("Starting natural robot movement sequence...")

while True:
    current_time = time()
    
    # Check for blinks and color changes
    check_for_blink_and_color()
    
    # Check if it's time for a major movement sequence
    if current_time > next_major_movement:
        print("\nPerforming major movement sequence")
        
        # Move eyes in a scanning pattern
        eye_angles = [60, 90, 120, 90]
        for angle in eye_angles:
            move_servo_smooth(1, angle, step_size=1, delay=0.02)
            sleep(0.5)
        
        # Move neck
        natural_neck_movement()
        
        # Move arms in a natural pattern
        natural_arm_movement()
        
        # Set next major movement time
        last_major_movement = current_time
        next_major_movement = current_time + random.uniform(major_movement_interval_min, major_movement_interval_max)
        print(f"Next major movement in {next_major_movement - current_time:.1f} seconds")
    
    # Check if it's time for subtle idle movements
    if current_time > next_idle_movement:
        print("\nPerforming subtle idle movement")
        idle_movement()
        
        # Set next idle movement time
        last_idle_movement = current_time
        next_idle_movement = current_time + random.uniform(idle_movement_interval_min, idle_movement_interval_max)
    
    # Add some randomness to eye movements
    if random.random() < 0.1:  # 10% chance each cycle
        # Random eye movement
        eye_angle = random.randint(70, 110)
        print(f"Random eye movement to {eye_angle} degrees")
        move_servo_smooth(1, eye_angle, step_size=1, delay=0.02)
    
    # Add occasional "looking around" behavior
    if random.random() < 0.05:  # 5% chance each cycle
        print("Looking around sequence")
        # Look left
        move_servo_smooth(2, 70, step_size=1, delay=0.02)  # Neck left
        move_servo_smooth(1, 70, step_size=1, delay=0.02)  # Eye left
        sleep(random.uniform(0.5, 1.5))
        
        # Look right
        move_servo_smooth(2, 110, step_size=1, delay=0.02)  # Neck right
        move_servo_smooth(1, 110, step_size=1, delay=0.02)  # Eye right
        sleep(random.uniform(0.5, 1.5))
        
        # Return to center
        move_servo_smooth(2, 90, step_size=1, delay=0.02)  # Neck center
        move_servo_smooth(1, 90, step_size=1, delay=0.02)  # Eye center
    
    # Small delay between cycles to prevent excessive servo movement
    sleep(0.5)
