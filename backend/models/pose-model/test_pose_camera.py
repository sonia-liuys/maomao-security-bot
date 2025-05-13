import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
import os

MODEL_PATH = "pose_model.tflite"
LABEL_PATH = "labels.txt"

# 讀取標籤
if os.path.exists(LABEL_PATH):
    with open(LABEL_PATH, 'r', encoding='utf-8') as f:
        labels = [l.strip() for l in f.readlines() if l.strip()]
else:
    labels = [str(i) for i in range(10)]

print("=== Label 對應表 ===")
for idx, label in enumerate(labels):
    print(f"{idx}: {label}")
print("==================")

# 載入 TFLite 模型
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape']
num_features = input_shape[1]

# 初始化 MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

def get_flattened_keypoints(results):
    if results.pose_landmarks:
        # 取 33 個點，每個點有 x, y, z, visibility
        keypoints = []
        for lm in results.pose_landmarks.landmark:
            keypoints.extend([lm.x, lm.y, lm.z, lm.visibility])
        return np.array(keypoints, dtype=np.float32)
    else:
        return None

cap = cv2.VideoCapture(0)
print("按 q 鍵離開")

while True:
    ret, frame = cap.read()
    if not ret:
        print("無法讀取攝影機")
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)
    keypoints = get_flattened_keypoints(results)

    label_text = "No Person"
    if keypoints is not None:
        # 若 keypoints 維度不足，補 0 到模型需求長度
        if keypoints.shape[0] < num_features:
            keypoints = np.pad(keypoints, (0, num_features - keypoints.shape[0]), 'constant')
        elif keypoints.shape[0] > num_features:
            keypoints = keypoints[:num_features]
        input_data = np.expand_dims(keypoints, axis=0).astype(np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])
        pred_idx = int(np.argmax(output_data))
        pred_label = labels[pred_idx] if pred_idx < len(labels) else str(pred_idx)
        confidence = float(np.max(output_data))
        label_text = f"{pred_label} ({confidence:.2f})"

    # 顯示 label 對應表在畫面左上角
    y0 = 70
    for idx, label in enumerate(labels):
        txt = f"{idx}: {label}"
        y = y0 + idx * 25
        cv2.putText(frame, txt, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, lineType=cv2.LINE_AA)

    # 顯示預測結果
    cv2.putText(frame, label_text, (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.imshow("Pose Model Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
