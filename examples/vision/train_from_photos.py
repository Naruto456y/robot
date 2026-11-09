#!/usr/bin/env python3
import face_recognition
import pickle
import glob
import cv2
import numpy as np
import os

# Путь к папке с фото робота (можно изменить)
PHOTO_PATTERN = "/home/pi/you_*.jpg"
OUTPUT_FILE = "/home/pi/known_face.pkl"

files = glob.glob(PHOTO_PATTERN)
if not files:
    print(f"❌ Нет фото по паттерну: {PHOTO_PATTERN}")
    print("   Сначала запустите face_recognize_precise.py, чтобы робот наснимал фото.")
    exit(1)

print(f"📸 Найдено {len(files)} фото")

encodings = []
for f in files:
    img = cv2.imread(f)
    if img is None:
        continue
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    boxes = face_recognition.face_locations(rgb)
    if not boxes:
        print(f"⚠️ На фото {f} лицо не найдено, пропускаем")
        continue
    enc = face_recognition.face_encodings(rgb, boxes)[0]
    encodings.append(enc)

if not encodings:
    print("❌ Не удалось получить энкодинги ни с одного фото")
    exit(1)

# Усредняем все энкодинги
mean_encoding = np.mean(encodings, axis=0)
# Также сохраняем все энкодинги (на случай, если усреднение ухудшит)
with open(OUTPUT_FILE, "wb") as f:
    pickle.dump(mean_encoding, f)

print(f"✅ Усреднённый энкодинг сохранён ({len(encodings)} фото)")
print(f"   Файл: {OUTPUT_FILE}")
