#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import time
import datetime
import os
import threading
import pyaudio
import wave
from Raspbot_Lib import Raspbot

# ========== НАСТРОЙКИ ==========
DURATION = 600  # 10 минут (600 секунд)
HORIZONTAL_STEP = 2   # шаг по горизонтали (градусы)
VERTICAL_STEP = 2     # шаг по вертикали (градусы)
HORIZONTAL_MIN = 0
HORIZONTAL_MAX = 180
VERTICAL_MIN = 0
VERTICAL_MAX = 90
DELAY = 0.1  # задержка между движениями (сек)
FPS = 15     # кадров в секунду для видео

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = Raspbot()
bot.Ctrl_Servo(1, 90)
bot.Ctrl_Servo(2, 45)
time.sleep(0.5)

# ========== ПОДГОТОВКА КАМЕРЫ И ВИДЕО ==========
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
video_file = f"/home/pi/scan_video_{timestamp}.avi"
audio_file = f"/home/pi/scan_audio_{timestamp}.wav"

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Камера не доступна")
    exit(1)

# Настройки видео
fourcc = cv2.VideoWriter_fourcc(*'XVID')
fps = FPS
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter(video_file, fourcc, fps, (width, height))

# ========== ФУНКЦИЯ ЗАПИСИ АУДИО ==========
def record_audio():
    try:
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        RECORD_SECONDS = DURATION
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        print("🎤 Запись аудио...")
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf = wave.open(audio_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print("✅ Аудио сохранено")
    except Exception as e:
        print(f"❌ Ошибка аудио: {e}")

# ========== СКАНИРОВАНИЕ И ЗАПИСЬ ВИДЕО ==========
print("🔍 Начинаем сканирование с записью видео...")
start_time = time.time()
audio_thread = threading.Thread(target=record_audio)
audio_thread.start()

try:
    frame_count = 0
    total_checks = 0
    # Сканируем по вертикали
    for v_angle in range(VERTICAL_MAX, VERTICAL_MIN - 1, -VERTICAL_STEP):
        bot.Ctrl_Servo(2, v_angle)
        time.sleep(DELAY)
        # Сканируем по горизонтали
        for h_angle in range(HORIZONTAL_MIN, HORIZONTAL_MAX + 1, HORIZONTAL_STEP):
            bot.Ctrl_Servo(1, h_angle)
            time.sleep(DELAY)

            ret, frame = cap.read()
            if not ret:
                continue

            # Записываем кадр
            out.write(frame)
            frame_count += 1

            # Проверяем время
            if time.time() - start_time >= DURATION:
                print("⏰ Время истекло")
                break
        if time.time() - start_time >= DURATION:
            break

except KeyboardInterrupt:
    print("⏹️ Прервано пользователем")

finally:
    cap.release()
    out.release()
    audio_thread.join(timeout=5)
    # Возвращаем камеру в центр
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 45)
    print(f"📹 Видео сохранено: {video_file}")
    print(f"🎧 Аудио сохранено: {audio_file}")
    print(f"📊 Записано кадров: {frame_count}")
    print("🏁 Завершено.")