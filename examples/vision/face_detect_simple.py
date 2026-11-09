#!/usr/bin/env python3
import cv2
import mediapipe as mp
import time
from myrobot import Robot

mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)

robot = Robot()
robot.rgb_off()

print("👀 Сканирую лица. Красный – жду, зелёный – найдено!")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Камера не доступна")
    robot.restore()
    exit(1)

def draw_faces(frame, detections):
    """Рисует зелёные прямоугольники вокруг всех лиц"""
    h, w, _ = frame.shape
    for detection in detections:
        bbox = detection.location_data.relative_bounding_box
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        width = int(bbox.width * w)
        height = int(bbox.height * h)
        cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
    return frame

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb)
        if results.detections:
            print("✅ Обнаружен качок!")
            # Обводим лица
            frame_with_boxes = draw_faces(frame, results.detections)
            # Сохраняем с меткой времени
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"/home/pi/face_{timestamp}.jpg"
            cv2.imwrite(filename, frame_with_boxes)
            print(f"Сохранено в {filename}")
            robot.rgb_color(1)   # зелёный
            robot.beep_short()
            robot.say("Обнаружен качок")
            time.sleep(2)
        else:
            robot.rgb_color(0)   # красный
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    cap.release()
    robot.restore()
