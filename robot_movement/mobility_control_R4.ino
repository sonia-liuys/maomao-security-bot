#include "MatrixMiniR4.h"



void setup()
{
  MiniR4.begin();
  MiniR4.PWR.setBattCell(2);
  Serial.begin(9600);
  MiniR4.I2C1.MXLaser.begin();
  MiniR4.M1.setReverse(false);
  MiniR4.M2.setReverse(true);
  delay(100);
}

void loop()
{
  MiniR4.M1.setPower(60);
  MiniR4.M2.setPower(60);
  delay(2000);
  MiniR4.M1.setPower(0);
  MiniR4.M2.setPower(0);
  delay(200);
  MiniR4.M1.setPower(60);
  MiniR4.M2.setPower((-60));
  delay(500);
  MiniR4.M1.setPower(0);
  MiniR4.M2.setPower(0);
  delay(200);

}