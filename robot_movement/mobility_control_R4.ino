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
// 下一個
#include "MatrixMiniR4.h"

void setup()
{
  MiniR4.begin();
  MiniR4.PWR.setBattCell(2);
  Serial.begin(9600);
  MiniR4.PS2.read_gamepad(false, 0);
  MiniR4.M1.setReverse(false);
  MiniR4.M2.setReverse(true);
  MiniR4.M3.setReverse(false);
  MiniR4.M4.setReverse(true);
}

void loop()
{
  if(MiniR4.PS2.Button(PSB_L1))
  {
    for(int i_0 = 0; i_0 < 4; i_0++)
    {
      MiniR4.M1.setPower(200);
      MiniR4.M2.setPower(200);
      MiniR4.M3.setPower(200);
      MiniR4.M4.setPower(200);
      delay(2000);
      MiniR4.M1.setPower(0);
      MiniR4.M2.setPower(0);
      MiniR4.M3.setPower(0);
      MiniR4.M4.setPower(0);
      delay(200);
      MiniR4.M1.setPower(200);
      MiniR4.M2.setPower((-200));
      MiniR4.M3.setPower(200);
      MiniR4.M4.setPower((-200));
      delay(500);
      MiniR4.M1.setPower(0);
      MiniR4.M2.setPower(0);
      MiniR4.M3.setPower(0);
      MiniR4.M4.setPower(0);
      delay(200);
    }
  }

}
// 下一個
#include "MatrixMiniR4.h"

void setup()
{
  MiniR4.begin();
  MiniR4.PWR.setBattCell(2);
  Serial.begin(9600);
  MiniR4.I2C1.MXLaserV2.begin();
}

void loop()
{
  if(MiniR4.I2C1.MXLaserV2.getDistance() < 10)
  {
    MiniR4.M1.setPower(0);
    MiniR4.M2.setPower(0);
  }

}
// 下一個oo
#include "MatrixMiniR4.h"

void setup()
{
  MiniR4.begin();
  MiniR4.PWR.setBattCell(2);
  Serial.begin(9600);
}

void loop()
{
  if(MiniR4.A1.getAIL() < 500)
  {
    Serial.print("Dark");
  }
  else
  {
    Serial.print("Bright");
  }

}