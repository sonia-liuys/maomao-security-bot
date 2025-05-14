import os
import numpy as np
import cv2
import tensorflow as tf

MODEL_PATH = "pose_model.tflite"
LABEL_PATH = "labels.txt"  # 請放在同資料夾（每行一個label）
TEST_IMG_DIR = "test_images"  # 請建立此資料夾並放入測試圖片

# 讀取標籤
if os.path.exists(LABEL_PATH):
    with open(LABEL_PATH, 'r', encoding='utf-8') as f:
        labels = [l.strip() for l in f.readlines() if l.strip()]
else:
    labels = [str(i) for i in range(10)]

# 載入 TFLite 模型
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_shape = input_details[0]['shape']
input_height, input_width = input_shape[1], input_shape[2]

img_dir = os.path.join(os.path.dirname(__file__), TEST_IMG_DIR)
if not os.path.exists(img_dir):
    print(f"請將測試圖片放到 {img_dir} 目錄下！")
    exit(1)
img_files = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
if not img_files:
    print(f"{img_dir} 沒有找到任何圖片！")
    exit(1)

for img_name in img_files:
    img_path = os.path.join(img_dir, img_name)
    img = cv2.imread(img_path)
    if img is None:
        print(f"無法讀取圖片: {img_path}")
        continue
    img_resized = cv2.resize(img, (input_width, input_height))
    img_input = img_resized.astype(np.float32) / 255.0
    img_input = np.expand_dims(img_input, axis=0)

    interpreter.set_tensor(input_details[0]['index'], img_input)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])

    pred_idx = int(np.argmax(output_data))
    pred_label = labels[pred_idx] if pred_idx < len(labels) else str(pred_idx)
    confidence = float(np.max(output_data))

    print(f"圖片: {img_name}\t預測: {pred_label}\t信心度: {confidence:.3f}")
