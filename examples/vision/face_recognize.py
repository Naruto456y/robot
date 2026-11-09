#!/usr/bin/env python3
import cv2
import face_recognition
import pickle
import time
import os
from datetime import datetime
from Raspbot_Lib import Raspbot
from myrobot import Robot

r = Robot()

# ========== ЗАГРУЗКА ЭТАЛОНА ==========
try:
    with open("/home/pi/known_face.pkl", "rb") as f:
        known_encoding = pickle.load(f)
    print("✅ Эталон загружен")
except:
    print("❌ Файл known_face.pkl не найден. Запустите face_register.py")
    exit(1)

# ========== ИНИЦИАЛИЗАЦИЯ РОБОТА ==========
bot = Raspbot()
COLOR_RED = 0
COLOR_GREEN = 1

def set_color(color):
    bot.Ctrl_WQ2812_ALL(1, color)

def rgb_off():
    bot.Ctrl_WQ2812_ALL(0, 0)

def beep():
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.15)
    bot.Ctrl_BEEP_Switch(0)

print("👀 Сканирую лица. Красный – жду, зелёный – это ВЫ!")
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

        # Уменьшаем кадр для ускорения
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small)
        if face_locations:
            encodings = face_recognition.face_encodings(rgb_small, face_locations)
            for encoding in encodings:
                matches = face_recognition.compare_faces([known_encoding], encoding, tolerance=0.5)
                if matches[0]:
                    # Нашли нужное лицо
                    top, right, bottom, left = face_locations[0]
                    # Масштабируем координаты обратно
                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2
                    cv2.rectangle(frame, (left, top), (right, bottom), (0,255,0), 2)
                    cv2.putText(frame, "YOU", (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                    # Сохраняем фото
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"/home/pi/you_{timestamp}.jpg"
                    cv2.imwrite(filename, frame)
                    print(f"✅ ВЫ обнаружены! Фото: {filename}")

                    set_color(COLOR_GREEN)
                    beep()
                    r.say("Обнаружен лох")
                    time.sleep(2)
                    set_color(COLOR_RED)
                    time.sleep(0.5)
                    break  # выходим из цикла encodings, чтобы не повторять
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\n👋 Завершено")
    cap.release()
    rgb_off()
    print("🏁 Камера освобождена, RGB выключен.")
finally:
    cap.release()
    rgb_off()
    print("🏁 Камера освобождена, RGB выключен.")