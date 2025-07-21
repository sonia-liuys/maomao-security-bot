/*
 * Arduino NeoPixel LED Controller
 * 
 * This sketch controls NeoPixel LEDs based on commands from Raspberry Pi via Serial/USB.
 * It listens for color commands in the format: "SET_COLOR R,G,B"
 * Where R, G, B are values from 0-255.
 * 
 * Example: "SET_COLOR 255,0,0" will set all LEDs to red.
 */

#include <Adafruit_NeoPixel.h>

// Configuration
#define LED_PIN     6      // Data pin connected to the NeoPixel strip
#define NUM_PIXELS  7      // Number of NeoPixels in the strip
#define BRIGHTNESS  50     // NeoPixel brightness (0-255)

// Initialize the NeoPixel strip
Adafruit_NeoPixel pixels(NUM_PIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);

// Buffer for incoming serial data
String inputBuffer = "";
boolean commandComplete = false;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  
  // Initialize NeoPixel strip
  pixels.begin();
  pixels.setBrightness(BRIGHTNESS);
  pixels.clear();
  pixels.show();
  
  // Send ready message to Raspberry Pi
  Serial.println("READY");
}

void loop() {
  // Check for incoming serial data
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    // Add character to input buffer if not newline
    if (inChar != '\n') {
      inputBuffer += inChar;
    } else {
      // Newline received, mark command as complete
      commandComplete = true;
    }
  }
  
  // Process complete command
  if (commandComplete) {
    processCommand(inputBuffer);
    
    // Clear buffer and reset flag
    inputBuffer = "";
    commandComplete = false;
  }
}

void processCommand(String command) {
  command.trim();
  
  // Check for SET_COLOR command
  if (command.startsWith("SET_COLOR")) {
    // Extract color values
    int firstSpace = command.indexOf(' ');
    if (firstSpace != -1) {
      String colorStr = command.substring(firstSpace + 1);
      
      // Parse RGB values
      int firstComma = colorStr.indexOf(',');
      int secondComma = colorStr.lastIndexOf(',');
      
      if (firstComma != -1 && secondComma != -1 && firstComma != secondComma) {
        int r = colorStr.substring(0, firstComma).toInt();
        int g = colorStr.substring(firstComma + 1, secondComma).toInt();
        int b = colorStr.substring(secondComma + 1).toInt();
        
        // Set all pixels to the same color
        setAllPixels(r, g, b);
        
        // Confirm command execution
        Serial.print("OK SET_COLOR ");
        Serial.print(r);
        Serial.print(",");
        Serial.print(g);
        Serial.print(",");
        Serial.println(b);
      } else {
        Serial.println("ERROR: Invalid color format. Use R,G,B");
      }
    } else {
      Serial.println("ERROR: Invalid SET_COLOR command");
    }
  } 
  // Add other commands as needed
  else if (command == "STATUS") {
    Serial.println("STATUS: Arduino LED controller running");
  }
  else if (command == "CLEAR") {
    pixels.clear();
    pixels.show();
    Serial.println("OK CLEAR");
  }
  else {
    Serial.print("ERROR: Unknown command: ");
    Serial.println(command);
  }
}

// Set all pixels to the same RGB color
void setAllPixels(int r, int g, int b) {
  for (int i = 0; i < NUM_PIXELS; i++) {
    pixels.setPixelColor(i, pixels.Color(r, g, b));
  }
  pixels.show();
}
