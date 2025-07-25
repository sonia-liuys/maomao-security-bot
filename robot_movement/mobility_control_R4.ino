#include "MatrixMiniR4.h"

void setup()
{
  MiniR4.begin();
  MiniR4.PWR.setBattCell(2);
  Serial.begin(9600);
  MiniR4.PS2.read_gamepad(false, 0);
}

void loop()
{
  if(MiniR4.PS2.Button(PSB_PAD_UP))
  {
    MiniR4.M1.setPower(200);
    MiniR4.M2.setPower(200);
    MiniR4.M3.setPower(200);
    MiniR4.M4.setPower(200);
    delay(1000);
    MiniR4.M1.setPower(0);
    MiniR4.M2.setPower(0);
    MiniR4.M3.setPower(0);
    MiniR4.M4.setPower(0);
  }
  if(MiniR4.PS2.Button(PSB_PAD_DOWN))
  {
    MiniR4.M1.setPower((-200));
    MiniR4.M2.setPower((-200));
    MiniR4.M3.setPower((-200));
    MiniR4.M4.setPower((-200));
    delay(1000);
    MiniR4.M1.setPower(0);
    MiniR4.M2.setPower(0);
    MiniR4.M3.setPower(0);
    MiniR4.M4.setPower(0);
  }
  if(MiniR4.PS2.Button(PSB_PAD_RIGHT))
  {
    MiniR4.M1.setPower(200);
    MiniR4.M2.setPower((-200));
    MiniR4.M3.setPower(200);
    MiniR4.M4.setPower((-200));
    delay(1000);
    MiniR4.M1.setPower(0);
    MiniR4.M2.setPower(0);
    MiniR4.M3.setPower(0);
    MiniR4.M4.setPower(0);
  }
  if(MiniR4.PS2.Button(PSB_PAD_LEFT))
  {
    MiniR4.M1.setPower((-200));
    MiniR4.M2.setPower(200);
    MiniR4.M3.setPower((-200));
    MiniR4.M4.setPower(200);
    delay(1000);
    MiniR4.M1.setPower(0);
    MiniR4.M2.setPower(0);
    MiniR4.M3.setPower(0);
    MiniR4.M4.setPower(0);
  }

}