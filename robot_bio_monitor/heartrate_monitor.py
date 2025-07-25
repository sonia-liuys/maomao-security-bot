import cv2
import numpy as np
from scipy.signal import find_peaks

cap = cv2.VideoCapture(0)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
green_avg_list = []

def calculate_confidence(signal, peaks):
    if len(peaks) < 2:
        return 0.0  # 峰值太少，信心低
    peak_heights = signal[peaks]
    peak_prominence = np.mean(peak_heights)  # 平均峰值高度，越明顯越可信
    signal_std = np.std(signal)
    noise_level = signal_std if signal_std > 0 else 1e-6
    confidence = peak_prominence / noise_level
    # Normalize confidence to 0~1範圍，可調整上限
    confidence = min(confidence / 5.0, 1.0)
    return confidence

while True:
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    for (x,y,w,h) in faces:
        roi_y = y
        roi_h = int(h*0.25)
        roi = frame[roi_y:roi_y+roi_h, x:x+w]
        green_channel = roi[:, :, 1]
        green_avg = np.mean(green_channel)
        green_avg_list.append(green_avg)
        cv2.rectangle(frame, (x, roi_y), (x+w, roi_y+roi_h), (0,255,0), 2)

    cv2.imshow('PPG Heartbeat Detector', frame)

    if len(green_avg_list) > 300:
        signal = np.array(green_avg_list)
        signal = signal - np.mean(signal)
        signal = signal / np.std(signal)

        # 偵測峰值：distance調整最小峰間距，避免偵測過多峰
        peaks, _ = find_peaks(signal, distance=15)

        duration_sec = len(green_avg_list)/30
        heart_rate = len(peaks)/duration_sec*60

        confidence = calculate_confidence(signal, peaks)

        print(f"Estimated Heart Rate: {heart_rate:.2f} bpm, Confidence: {confidence:.2f}")

        green_avg_list = []

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()