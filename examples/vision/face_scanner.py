#!/usr/bin/env python3
import cv2
import time
import datetime
from Raspbot_Lib import Raspbot
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas
import mediapipe as mp
from myrobot import Robot

HORIZONTAL_STEPS = 15
VERTICAL_ANGLE = 90
MIN_DETECTION_CONFIDENCE = 0.5

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

def oled_message(text):
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((10, 20), text, fill="white")

bot = Raspbot()
r = Robot()

bot.Ctrl_Servo(2, VERTICAL_ANGLE)
time.sleep(0.5)

mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=MIN_DETECTION_CONFIDENCE)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    oled_message("Camera ERROR")
    exit(1)

found = False
saved_photo = ""

print("🔍 Сканирую...")
oled_message("Scanning...")

for angle in range(0, 181, HORIZONTAL_STEPS):
    bot.Ctrl_Servo(1, angle)
    time.sleep(0.25)

    ret, frame = cap.read()
    if not ret:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_detection.process(rgb)

    if results.detections:
        found = True
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_photo = f"/home/pi/face_{timestamp}.jpg"
        cv2.imwrite(saved_photo, frame)
        print(f"✅ Лицо найдено! Фото: {saved_photo}")
        break

cap.release()

if found:
    r.rgb_color(2)   # синий
    oled_message("Face FOUND!")
    print("🎉 Синий свет")
else:
    r.rgb_color(0)   # красный
    oled_message("No face :-(")
    print("❌ Красный свет")

time.sleep(5)
r.rgb_off()      # выключить
oled_message("")
print("🏁 Готово.")
