#!/usr/bin/env python3
from flask import Flask, Response
import cv2
import time

app = Flask(__name__)

def gen_frames():
    # Используем V4L2 бэкенд для лучшей производительности на Linux
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    
    # Устанавливаем параметры камеры
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # минимальный буфер
    
    # Проверяем, открылась ли камера
    if not cap.isOpened():
        print("❌ Не удалось открыть камеру")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Кодируем в JPEG с качеством 70 (быстрее, чем 100)
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        if not ret:
            continue
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               jpeg.tobytes() + b'\r\n')
    
    cap.release()

@app.route('/video')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("📡 Стриминг запущен на http://192.168.1.56:5000/video")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)