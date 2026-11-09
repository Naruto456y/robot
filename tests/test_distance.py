#!/usr/bin/env python3
import cv2
import face_recognition
import pickle
import time

try:
    with open("/home/pi/known_face.pkl", "rb") as f:
        known_encoding = pickle.load(f)
except:
    print("❌ Нет эталона")
    exit(1)

print("👀 Покажите лицо брата, затем лицо другого человека.")
print("   Расстояние < порога = совпадение.")
print("   Нажмите Ctrl+C для выхода.")

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        continue
    small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)
    if face_locations:
        encodings = face_recognition.face_encodings(rgb, face_locations)
        for enc in encodings:
            dist = face_recognition.face_distance([known_encoding], enc)[0]
            print(f"Расстояние: {dist:.3f}")
    time.sleep(0.3)
