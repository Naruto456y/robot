#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анализ сцены с камеры: лица, объекты, QR, цвета
Вывод в консоль каждые 2 секунды
Нажмите Ctrl+C для выхода
"""
import cv2
import time
import numpy as np
import mediapipe as mp

def detect_faces(frame):
    """Возвращает количество лиц и координаты"""
    mp_face = mp.solutions.face_detection
    with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb)
        faces = []
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                h, w, _ = frame.shape
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                faces.append((x, y, width, height))
        return faces

def detect_objects(frame):
    """Возвращает список найденных объектов (MediaPipe Objectron)"""
    mp_obj = mp.solutions.objectron
    objects = []
    with mp_obj.Objectron(static_image_mode=False, max_num_objects=5,
                          min_detection_confidence=0.5, model_name='Chair') as objectron:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = objectron.process(rgb)
        if results.detected_objects:
            for obj in results.detected_objects:
                # Можно извлечь 3D-бокс, но для простоты просто отметим
                objects.append("object")
        return objects

def detect_qr(frame):
    """Возвращает данные QR-кода, если найден"""
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(frame)
    if data:
        return data
    return None

def detect_color(frame):
    """Определяет доминирующий цвет в центре кадра"""
    h, w, _ = frame.shape
    center = frame[h//2-10:h//2+10, w//2-10:w//2+10]
    avg = np.mean(center, axis=(0,1))
    color_name = "unknown"
    if avg[1] > 80 and avg[2] > 80:
        hsv = cv2.cvtColor(np.uint8([[avg]]), cv2.COLOR_BGR2HSV)[0][0]
        h_val = hsv[0]
        if h_val < 10: color_name = "Red"
        elif h_val < 30: color_name = "Orange"
        elif h_val < 60: color_name = "Yellow"
        elif h_val < 100: color_name = "Green"
        elif h_val < 130: color_name = "Cyan"
        elif h_val < 170: color_name = "Blue"
        else: color_name = "Purple"
    return color_name

def analyze_scene():
    print("🔍 Запуск анализа сцены (каждые 2 секунды). Нажмите Ctrl+C для выхода.")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Камера не доступна")
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Ошибка захвата кадра")
                break

            # Детекции
            faces = detect_faces(frame)
            objects = detect_objects(frame)
            qr_data = detect_qr(frame)
            color = detect_color(frame)

            # Формируем описание
            description = []
            if faces:
                description.append(f"{len(faces)} лиц(а)")
            if objects:
                description.append(f"{len(objects)} объекта(ов)")
            if qr_data:
                description.append(f"QR-код: {qr_data}")
            if color != "unknown":
                description.append(f"цвет в центре: {color}")

            if description:
                print(f"📸 Вижу: {', '.join(description)}")
            else:
                print("👀 Ничего не обнаружено")

            time.sleep(2)  # пауза между анализами

    except KeyboardInterrupt:
        print("\n👋 Анализ остановлен")
    finally:
        cap.release()

if __name__ == "__main__":
    analyze_scene()