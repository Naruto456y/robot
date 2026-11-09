#!/usr/bin/env python3
import cv2
import time
import os
from datetime import datetime
from Raspbot_Lib import Raspbot

# ========== КАСКАДНЫЙ ФАЙЛ ==========
CASCADE_PATH = "/home/pi/haarcascade_frontalface_default.xml"
if not os.path.exists(CASCADE_PATH):
    print("📥 Скачиваем каскадный файл...")
    import urllib.request
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml",
        CASCADE_PATH
    )
    print("✅ Скачано")

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
bot = Raspbot()

# ========== НАСТРОЙКИ ТОЧНОСТИ ==========
SCALE_FACTOR = 1.1        # шаг масштабирования (чем меньше, тем точнее, но медленнее)
MIN_NEIGHBORS = 8         # количество соседей (чем больше, тем строже – меньше ложных)
MIN_FACE_SIZE = (50, 50)  # минимальный размер лица (игнорируем маленькие объекты)
# Для максимальной точности можно уменьшить SCALE_FACTOR до 1.05 и увеличить MIN_NEIGHBORS до 10

# ========== ЦВЕТА RGB ==========
COLOR_RED = 0
COLOR_GREEN = 1

def set_color(color):
    bot.Ctrl_WQ2812_ALL(1, color)

def rgb_off():
    bot.Ctrl_WQ2812_ALL(0, 0)

def beep():
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.2)
    bot.Ctrl_BEEP_Switch(0)

print("👀 Сканирую лица (повышенная точность).")
print("   Красный – жду, зелёный – лицо найдено!")
print("   Нажмите Ctrl+C для выхода.")

set_color(COLOR_RED)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Камера не доступна")
    rgb_off()
    exit(1)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBORS,
            minSize=MIN_FACE_SIZE
        )
        if len(faces) > 0:
            x, y, w, h = faces[0]
            # Дополнительная проверка: соотношение сторон лица должно быть примерно 1:1
            aspect_ratio = w / h
            if 0.7 < aspect_ratio < 1.3:  # лица обычно почти квадратные
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/home/pi/face_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Лицо обнаружено! Фото: {filename}")
                set_color(COLOR_GREEN)
                # beep()
                time.sleep(2)
                set_color(COLOR_RED)
                time.sleep(0.5)
        time.sleep(0.05)  # небольшая пауза
except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    cap.release()
    rgb_off()
    print("🏁 Камера освобождена, RGB выключен.")