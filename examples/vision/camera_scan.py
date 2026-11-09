#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import time
import datetime
import os
import mediapipe as mp
from Raspbot_Lib import Raspbot

# ========== НАСТРОЙКИ (макс. точность) ==========
HORIZONTAL_MIN = 0
HORIZONTAL_MAX = 180
HORIZONTAL_STEP = 3      # очень мелкий шаг (3°)
VERTICAL_MIN = 0
VERTICAL_MAX = 90
VERTICAL_STEP = 3        # очень мелкий шаг (3°)
CENTER_H = 95
CENTER_V = 25
DELAY = 0.1              # задержка после движения

# Параметры MediaPipe
MIN_DETECTION_CONFIDENCE = 0.3  # очень низкий порог для макс. чувствительности
MARGIN = 25        # отступ вокруг лица (пикселей), чтобы захватить целиком

# ========== ИНИЦИАЛИЗАЦИЯ MediaPipe ==========
mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(
    model_selection=0,   # 0 – для лиц ближе 2 м, 1 – для дальних
    min_detection_confidence=MIN_DETECTION_CONFIDENCE
)

# ========== ИНИЦИАЛИЗАЦИЯ РОБОТА ==========
bot = Raspbot()
bot.Ctrl_Servo(1, CENTER_H)
bot.Ctrl_Servo(2, CENTER_V)
time.sleep(0.5)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Камера не доступна")
    exit(1)

# ========== КИВОК ==========
def nod_camera():
    print("👋 Кивок камерой...")
    bot.Ctrl_Servo(2, CENTER_V + 30)
    time.sleep(0.3)
    bot.Ctrl_Servo(2, CENTER_V - 30)
    time.sleep(0.3)
    bot.Ctrl_Servo(2, CENTER_V)
    time.sleep(0.3)

nod_camera()

print("🔍 Сканирование с максимальной точностью (MediaPipe)...")
print(f"   Горизонталь: {HORIZONTAL_MIN}°–{HORIZONTAL_MAX}°, шаг {HORIZONTAL_STEP}°")
print(f"   Вертикаль: {VERTICAL_MIN}°–{VERTICAL_MAX}°, шаг {VERTICAL_STEP}°")
print("   Для прерывания нажмите Ctrl+C\n")

try:
    found = False
    total_checks = 0

    for v_angle in range(VERTICAL_MAX, VERTICAL_MIN - 1, -VERTICAL_STEP):
        bot.Ctrl_Servo(2, v_angle)
        time.sleep(DELAY)

        for h_angle in range(HORIZONTAL_MIN, HORIZONTAL_MAX + 1, HORIZONTAL_STEP):
            bot.Ctrl_Servo(1, h_angle)
            time.sleep(DELAY / 2)

            ret, frame = cap.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb)

            total_checks += 1

            if results.detections:
                found = True
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                # Сохраняем полный кадр
                full_filename = f"/home/pi/face_full_{timestamp}.jpg"
                cv2.imwrite(full_filename, frame)
                print(f"\n✅ ЛИЦО НАЙДЕНО! (проверка №{total_checks})")

                # Обрабатываем каждое обнаруженное лицо
                for i, detection in enumerate(results.detections):
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = frame.shape
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)

                    # Расширяем рамку с отступом, чтобы лицо было целиком
                    x1 = max(0, x - MARGIN)
                    y1 = max(0, y - MARGIN)
                    x2 = min(w, x + width + MARGIN)
                    y2 = min(h, y + height + MARGIN)

                    # Вырезаем лицо с отступом
                    face_crop = frame[y1:y2, x1:x2]
                    if face_crop.size > 0:
                        crop_filename = f"/home/pi/face_crop_{timestamp}_{i}.jpg"
                        cv2.imwrite(crop_filename, face_crop)
                        print(f"   Обрезанное лицо #{i+1} сохранено: {crop_filename}")

                    # Рисуем рамку на полном кадре (для отладки)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    # Сохраняем кадр с рамкой
                    boxed_filename = f"/home/pi/face_boxed_{timestamp}.jpg"
                    cv2.imwrite(boxed_filename, frame)
                    print(f"   Кадр с рамкой сохранён: {boxed_filename}")

                nod_camera()  # кивок после обнаружения
                break
        if found:
            break

    if not found:
        print(f"\n❌ Лицо не обнаружено за {total_checks} проверок.")

except KeyboardInterrupt:
    print("\n👋 Сканирование прервано")

finally:
    cap.release()
    bot.Ctrl_Servo(1, CENTER_H)
    bot.Ctrl_Servo(2, CENTER_V)
    print("🏁 Робот вернул камеру в центр.")