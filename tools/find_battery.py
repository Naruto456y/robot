#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import time
import os
from datetime import datetime
from Raspbot_Lib import Raspbot
from ultralytics import YOLO

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Raspbot()

# Загружаем модель YOLO-World (лёгкая, ищет по тексту)
print("📦 Загрузка модели YOLO-World...")
model = YOLO('yolov8s-world.pt')
model.set_classes(["AA battery", "battery", "alkaline battery"])
print("✅ Модель загружена")

# Параметры сканирования (медленно, но точно)
H_STEP = 3          # градусы по горизонтали
V_STEP = 3          # градусы по вертикали
H_MIN, H_MAX = 0, 180
V_MIN, V_MAX = 0, 90
DELAY = 0.15        # задержка после движения

CENTER_H, CENTER_V = 95, 25
bot.Ctrl_Servo(1, CENTER_H)
bot.Ctrl_Servo(2, CENTER_V)
time.sleep(0.5)

def beep(duration=1.0):
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(duration)
    bot.Ctrl_BEEP_Switch(0)

def save_detection(frame, box, confidence):
    """Сохраняет кадр с нарисованной рамкой вокруг батарейки"""
    x1, y1, x2, y2 = map(int, box)
    # Рисуем рамку
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
    # Подпись
    label = f"Battery {confidence:.2f}"
    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    # Имя файла с временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"/home/pi/battery_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"📸 Фото сохранено: {filename}")
    return filename

print("🔍 Начинаю поиск батарейки AA (медленное сканирование)...")
print("   При обнаружении будет сделан снимок и звуковой сигнал.")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Камера не доступна")
    exit(1)

try:
    found = False
    # Сканируем по горизонтали
    for h_angle in range(H_MIN, H_MAX + 1, H_STEP):
        bot.Ctrl_Servo(1, h_angle)
        time.sleep(DELAY)

        # Проход по вертикали снизу вверх
        for v_angle in range(V_MIN, V_MAX + 1, V_STEP):
            bot.Ctrl_Servo(2, v_angle)
            time.sleep(DELAY)
            ret, frame = cap.read()
            if not ret:
                continue

            # Уменьшаем для скорости, но сохраняем оригинал для фото
            small = cv2.resize(frame, (320, 240))
            results = model(small, verbose=False)

            if results and len(results) > 0:
                for r in results:
                    if r.boxes is not None and len(r.boxes) > 0:
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf > 0.3:
                                # Масштабируем координаты обратно к оригинальному кадру
                                scale_x = frame.shape[1] / 320
                                scale_y = frame.shape[0] / 240
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                x1 = int(x1 * scale_x)
                                y1 = int(y1 * scale_y)
                                x2 = int(x2 * scale_x)
                                y2 = int(y2 * scale_y)

                                found = True
                                print(f"🔋 Батарейка найдена! Уверенность: {conf:.2f}")
                                # Сохраняем фото с рамкой
                                save_detection(frame, (x1, y1, x2, y2), conf)
                                beep(1.0)
                                break
                    if found:
                        break
            if found:
                break

        if found:
            break

        # Проход по вертикали сверху вниз (для полного обзора)
        for v_angle in range(V_MAX, V_MIN - 1, -V_STEP):
            bot.Ctrl_Servo(2, v_angle)
            time.sleep(DELAY)
            ret, frame = cap.read()
            if not ret:
                continue
            small = cv2.resize(frame, (320, 240))
            results = model(small, verbose=False)
            if results and len(results) > 0:
                for r in results:
                    if r.boxes is not None and len(r.boxes) > 0:
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf > 0.3:
                                scale_x = frame.shape[1] / 320
                                scale_y = frame.shape[0] / 240
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                x1 = int(x1 * scale_x)
                                y1 = int(y1 * scale_y)
                                x2 = int(x2 * scale_x)
                                y2 = int(y2 * scale_y)

                                found = True
                                print(f"🔋 Батарейка найдена! Уверенность: {conf:.2f}")
                                save_detection(frame, (x1, y1, x2, y2), conf)
                                beep(1.0)
                                break
                    if found:
                        break
            if found:
                break

        if found:
            break

    if not found:
        print("❌ Батарейка не найдена.")

except KeyboardInterrupt:
    print("\n👋 Сканирование прервано")
finally:
    cap.release()
    bot.Ctrl_Servo(1, CENTER_H)
    bot.Ctrl_Servo(2, CENTER_V)
    print("🏁 Робот вернул камеру в центр.")