#include <Adafruit_MotorShield.h>
#include "PS2X_lib.h"

// PS2 控制器
PS2X ps2x;
int error;

// 狀態變數
int robot_mode = 0;
int forward = 0, backward = 0;
int turn_180 = 0, turn_90_right = 0, turn_90_left = 0;
int button_state = 0;

// 串口控制
String serialCommand = "";
boolean commandAvailable = false;
boolean serialControlActive = false;

// 轉向定時器
unsigned long turnStartTime = 0;
boolean turnTimerActive = false;
const int turnDuration = 1000;  // 1秒轉向時間

// 馬達控制
int delay_period = 10;
//int delay_period = 200;
Adafruit_MotorShield AFMS = Adafruit_MotorShield();
Adafruit_DCMotor *motor1 = AFMS.getMotor(1);
Adafruit_DCMotor *motor2 = AFMS.getMotor(2);
Adafruit_DCMotor *motor3 = AFMS.getMotor(3);
Adafruit_DCMotor *motor4 = AFMS.getMotor(4);

// ✅ 超音波感測器腳位
const int trigPin = 7;
const int echoPin = 6;
long duration;
int distance;

// ✅ 正方形模式參數（慢速版）
int square_mode = 0;
int square_step = 0;
unsigned long square_start_time = 0;
const int square_forward_time = 2000;  // 原本 1000
const int square_turn_time = 1000;      // 原本 170

void setup() {
  Serial.begin(115200); // 處理串口命令函數
  AFMS.begin();

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  Serial.println("Robot mobility control initialized");
  Serial.println("Ready to receive commands");
  
  do {
    error = ps2x.config_gamepad(13, 11, 10, 12, true, true);
    if (error == 0) {
      Serial.println("PS2 Controller connected!");
      break;
    } else {
      delay(100);
    }
  } while (1);
}

void checkSerialCommand() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    
    // 換行符號表示一個完整的命令
    if (c == '\n') {
      commandAvailable = true;
      serialControlActive = true;
      break;
    } else {
      // 累積字符到命令字符串
      serialCommand += c;
    }
  }
}

void processSerialCommand() {
  // 移除可能的空白字符
  serialCommand.trim();
  
  Serial.print("收到命令: ");
  Serial.println(serialCommand);
  
  // 設置最後命令時間為當前時間
  static unsigned long lastCommandTime;
  lastCommandTime = millis(); // 更新最後命令時間，確保串口控制不會超時
  
  // 根據命令控制機器人
  if (serialCommand == "move_forward") {
    Serial.println("✅ 前進 (持續)");
    Serial.println("Forward (continuous)");
    // 使用PS2手柄的前進邏輯設置狀態變數
    forward = 1; 
    backward = turn_180 = turn_90_left = turn_90_right = 0;
    turnTimerActive = false;
  } 
  else if (serialCommand == "move_backward") {
    Serial.println("✅ 後退 (持續)");
    Serial.println("Backward (continuous)");
    // 使用PS2手柄的後退邏輯設置狀態變數
    backward = 1;
    forward = turn_180 = turn_90_left = turn_90_right = 0;
    turnTimerActive = false;
  } 
  else if (serialCommand == "move_left") {
    Serial.println("✅ 左轉 (1秒)");
    Serial.println("Left turn (1 second)");
    // 啟動轉向定時器
    setMotorsTurnLeft(160);
    turnStartTime = millis();
    turnTimerActive = true;
  } 
  else if (serialCommand == "move_right") {
    Serial.println("✅ 右轉 (1秒)");
    Serial.println("Right turn (1 second)");
    // 啟動轉向定時器
    setMotorsTurnRight(160);
    turnStartTime = millis();
    turnTimerActive = true;
  } 
  else if (serialCommand == "stop") {
    Serial.println("✅ 停止");
    Serial.println("Stop");
    // 重置所有狀態變數
    forward = backward = turn_180 = turn_90_left = turn_90_right = 0;
    square_mode = 0; // 確保方形路徑模式關閉
    turnTimerActive = false; // 取消任何正在進行的轉向定時器
    stopAllMotors(); // 立即停止馬達
  }
  else if (serialCommand == "start_patrol") {
    Serial.println("✅ 開始巡邏模式");
    Serial.println("Start patrol mode - Square path");
    square_mode = 1;
    square_step = 0;
    square_start_time = millis();
  }
  else {
    Serial.print("❌ 未知命令: ");
    Serial.println(serialCommand);
  }
  
  // 清除命令，準備接收下一個
  serialCommand = "";
}

int getDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2;
}

void loop() {
  // 檢查是否有串口指令
  checkSerialCommand();
  
  // 檢查轉向定時器
  if (turnTimerActive) {
    // 檢查是否已經運行了1秒
    if (millis() - turnStartTime >= turnDuration) {
      Serial.println("✅ 轉向完成 (1秒到期)");
      Serial.println("Turn completed (1 second timeout)");
      stopAllMotors();
      turnTimerActive = false;
    }
  }
  
  // 如果有串口指令，優先處理串口指令
  if (commandAvailable) {
    processSerialCommand();
    commandAvailable = false;
    return;
  }
  
  // 如果串口控制被激活，暫停 PS2 控制
  if (serialControlActive) {
    // 每5秒檢查一次串口連接，如果5秒內沒有收到命令，恢復 PS2 控制
    static unsigned long lastCommandTime = millis();
    
    // 檢查轉向計時器，即使在串口控制模式下也不跳過這個檢查
    // 這確保左右轉向完成後會停下來
    if (turnTimerActive) {
      // 返回來讓轉向計時器檢查繼續在下一個循環生效
      return;
    }
    
    if (millis() - lastCommandTime > 30000) {
      serialControlActive = false;
      Serial.println("串口控制超時，恢復 PS2 控制");
      stopAllMotors();  // 超時時停止所有馬達，確保安全
    }
    
    // 重要: 在串口控制模式下跳過其余的loop代碼
    // 這確保不會重新計算馬達速度並覆蓋串口命令設置的速度
    return;
  }
  
  ps2x.read_gamepad(false, 0);

  // ✅ 超音波避障：當距離小於 20 公分時，機器人會轉彎
  // int d = getDistance();
  // if (d < 20 && d != 0) {
  //   Serial.print(d);
  //   Serial.println("🚨 障礙物偵測，轉彎並後退！");
  //   // 根據需要選擇向右或向左轉
  //   stopAllMotors();
  //   delay(1000);
  //   //   // 後退一秒
  //   setAllMotors(160);  // 設置馬達反向運行，後退
  //   delay(1000);  // 後退1秒
  
  //   stopAllMotors();
  //   delay(500);
  //   setMotorsTurnRight(140);  // 這裡設置轉向右邊，你也可以使用 setMotorsTurnLeft(180)
  //   delay(1000);  // 控制轉彎的時間，可以根據實際情況調整
  //   stopAllMotors();
  //   return;
  // }


  if(button_state ==1){
    button_state = 0;
    return;

  }

  // ✅ 緊急停止
  if (ps2x.Button(PSB_SQUARE)) {
    Serial.println("🟥 緊急停止");
    forward = backward = turn_180 = turn_90_left = turn_90_right = 0;
    square_mode = 0;
    stopAllMotors();
    delay(delay_period);
    return;
  }

  //✅ 啟動正方形模式
  if (ps2x.NewButtonState(PSB_R2)) {
    Serial.println("🟦 正方形模式 ON");
    square_mode = 1;
    square_step = 0;
    square_start_time = millis();
    button_state = 1;
  }

  // ✅ 正方形模式邏輯
  if (square_mode) {
    Serial.print("step:");
    Serial.println(square_step);
    unsigned long now = millis();
    int ms = 180;
    if (square_step % 2 == 0) {
      setAllMotors(-ms);
      if (now - square_start_time > square_forward_time) {
        square_step++;
        square_start_time = now;
        Serial.println("ready to turn right");
        stopAllMotors();
        //delay(1000);
      }
    } else {
      Serial.println("turn right!");
      ms = 140;
      setMotorsTurnRight(ms);
      if (now - square_start_time > square_turn_time) {
        square_step++;
        square_start_time = now;
        stopAllMotors();
        //delay(1000);
      }
    }

    if (square_step >= 8) {
      Serial.println("✅ 正方形完成！");
      square_mode = 0;
      stopAllMotors();
    }

    delay(delay_period);
    return;
  }

  if (button_state == 1) {
    button_state = 0;
    return;
  }

  // 🔼 手動控制按鍵
  if (ps2x.NewButtonState(PSB_TRIANGLE)) {
    Serial.println("Triangle Pressed");
    forward = 1; backward = turn_180 = 0; button_state = 1;
  }

  if (ps2x.NewButtonState(PSB_CROSS)) {
    Serial.println("Cross Pressed");
    button_state = 1;
    backward = 1; forward = turn_180 = 0; button_state = 1;
  }

  if (ps2x.NewButtonState(PSB_CIRCLE)) {
    Serial.println("Circle Pressed");
    button_state = 1;
    turn_180 = 1; forward = backward = 0; button_state = 1;
  }

  if (ps2x.NewButtonState(PSB_R1)) {
    Serial.println("R1 Pressed");
    button_state = 1;
    turn_90_right = 1; button_state = 1;
  }

  if (ps2x.NewButtonState(PSB_L1)) {
    Serial.println("L1 Pressed");
    button_state = 1;
    turn_90_left = 1; button_state = 1;
  }

  int x = ps2x.Analog(PSS_LX) - 128;
  int y = ps2x.Analog(PSS_LY) - 128;
  if (abs(x) < 10) x = 0;
  if (abs(y) < 10) y = 0;

  int motorSpeed1 = (y - x) * 1.8;
  int motorSpeed2 = (y + x) * 1.8;
  int motorSpeed3 = (y + x) * 1.8;
  int motorSpeed4 = (y - x) * 1.8;

  // Turbo 模式
  if (ps2x.Button(PSB_L2)) {
    motorSpeed1 *= 1.6;
    motorSpeed2 *= 1.6;
    motorSpeed3 *= 1.6;
    motorSpeed4 *= 1.6;
  }

  // 特別動作
  if (forward) {
    motorSpeed1 = motorSpeed2 = motorSpeed3 = motorSpeed4 = -160;
  } else if (backward) {
    motorSpeed1 = motorSpeed2 = motorSpeed3 = motorSpeed4 = 160;
  } else if (turn_180) {
    setMotorsTurnRight(180);
    delay(400);
    turn_180 = 0;
    return;
  } else if (turn_90_right) {
    setMotorsTurnRight(180);
    delay(1100);
    turn_90_right = 0;
    return;
  } else if (turn_90_left) {
    setMotorsTurnLeft(180);
    delay(1100);
    turn_90_left = 0;
    return;
  }

  // Serial.print("m1:");
  // Serial.println(motorSpeed1);
  // Serial.print("m2:");
  // Serial.println(motorSpeed2);
  // Serial.print("m3:");
  // Serial.println(motorSpeed3);
  // Serial.print("m4:");
  // Serial.println(motorSpeed4);
  

  motorSpeed1 = constrain(motorSpeed1, -255, 255);
  motorSpeed2 = constrain(motorSpeed2, -255, 255);
  motorSpeed3 = constrain(motorSpeed3, -255, 255);
  motorSpeed4 = constrain(motorSpeed4, -255, 255);

  setMotorSpeed(motor1, motorSpeed1);
  setMotorSpeed(motor2, motorSpeed2);
  setMotorSpeed(motor3, motorSpeed3);
  setMotorSpeed(motor4, motorSpeed4);

  delay(delay_period);
}

// ✅ 幫你做一些常用馬達控制函數

void setMotorSpeed(Adafruit_DCMotor *motor, int speed) {
  if (speed > 0) {
    motor->setSpeed(speed);
    motor->run(FORWARD);
  } else if (speed < 0) {
    motor->setSpeed(-speed);
    motor->run(BACKWARD);
  } else {
    motor->run(RELEASE);
  }
}

void setAllMotors(int speed) {
  if (speed > 0) {
    motor1->run(FORWARD);
    motor2->run(FORWARD);
    motor3->run(FORWARD);
    motor4->run(FORWARD);
  } else {
    speed = -speed;
    motor1->run(BACKWARD);
    motor2->run(BACKWARD);
    motor3->run(BACKWARD);
    motor4->run(BACKWARD);
  }

  motor1->setSpeed(speed);
  motor2->setSpeed(speed);
  motor3->setSpeed(speed);
  motor4->setSpeed(speed);
}

void stopAllMotors() {
  setAllMotors(0);
}

void setMotorsTurnRight(int speed) {
  setMotorSpeed(motor1, speed);
  setMotorSpeed(motor2, speed);
  setMotorSpeed(motor3, -speed);
  setMotorSpeed(motor4, -speed);
}

void setMotorsTurnLeft(int speed) {
  setMotorSpeed(motor1, -speed);
  setMotorSpeed(motor2, -speed);
  setMotorSpeed(motor3, speed);
  setMotorSpeed(motor4, speed);
}