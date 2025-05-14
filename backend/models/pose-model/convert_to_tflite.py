import tensorflow as tf

# 讀取 Keras H5 模型
keras_model_path = 'keras_model.h5'
tflite_model_path = 'pose_model.tflite'

print(f'Loading Keras model from {keras_model_path}...')
model = tf.keras.models.load_model(keras_model_path)

# 建立 TFLite 轉換器
converter = tf.lite.TFLiteConverter.from_keras_model(model)
# 可選：啟用最佳化（量化）
# converter.optimizations = [tf.lite.Optimize.DEFAULT]

print('Converting to TFLite format...')
tflite_model = converter.convert()

# 儲存 TFLite 模型
with open(tflite_model_path, 'wb') as f:
    f.write(tflite_model)

print(f'轉換完成，已產生 {tflite_model_path}')
