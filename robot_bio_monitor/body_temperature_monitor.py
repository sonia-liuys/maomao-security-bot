import board
import busio
import adafruit_mlx90640
import time
import numpy as np

# 初始化I2C介面，MLX90640連接於SCL和SDA腳位
i2c = busio.I2C(board.SCL, board.SDA, frequency=400000)

# 初始化MLX90640
mlx = adafruit_mlx90640.MLX90640(i2c)
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ  # 設定讀取頻率

# 讀取溫度陣列暫存列表
frame = [0] * 768  # 32*24 = 768

def get_body_temperature(temperature_array):
    # MLX90640回傳整個畫面32x24像素溫度，選出人體區域最高溫當作體溫參考
    # 可視需求改進ROI(Region Of Interest)或加強平均計算避免雜訊
    temperature_np = np.array(temperature_array)
    max_temp = np.max(temperature_np)
    return max_temp

print("開始偵測人體溫度，請保持靠近感測器(約0.3-1公尺)...")

try:
    while True:
        try:
            mlx.getFrame(frame)
            body_temp = get_body_temperature(frame)
            print(f"偵測到最高溫度: {body_temp:.2f} °C")
        except Exception as e:
            print("讀取失敗，重試中...", e)
        time.sleep(0.5)  # 半秒更新一次
except KeyboardInterrupt:
    print("程式中止")