#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Универсальное демо для Yahboom Raspbot V2 (без моторов, без окон)
"""
import os
import sys
import time
import cv2
import subprocess
from Raspbot_Lib import Raspbot
import threading

bot = Raspbot()

# --- 1. RGB ---
def rgb_test():
    print("🎨 RGB-лента: красный → зелёный → синий → жёлтый → фиолетовый → голубой → белый")
    for c in range(7):
        bot.Ctrl_WQ2812_ALL(1, c)
        time.sleep(0.8)
    bot.Ctrl_WQ2812_ALL(0, 0)
    print("✅ RGB-тест завершён")

# --- 2. Бипер ---
def beep_test():
    print("🔊 Бипер: 3 коротких сигнала")
    for _ in range(3):
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.3)
        bot.Ctrl_BEEP_Switch(0)
        time.sleep(0.2)
    print("✅ Бипер протестирован")

# --- 3. OLED (luma.oled) ---
def oled_info():
    print("📟 Вывод информации на OLED...")
    try:
        from luma.core.interface.serial import i2c
        from luma.core.render import canvas
        from luma.oled.device import ssd1306
        import psutil, socket
        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial, width=128, height=32, rotate=0)
        def get_ip():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]; s.close(); return ip
            except: return "0.0.0.0"
        with canvas(device) as draw:
            draw.rectangle((0,0,127,31), outline="black", fill="black")
            draw.text((0,0), f"IP: {get_ip()}", fill="white")
            draw.text((0,10), f"CPU: {psutil.cpu_percent():5.1f}%", fill="white")
            draw.text((0,20), f"RAM: {psutil.virtual_memory().percent:5.1f}%", fill="white")
        print("✅ OLED обновлён")
    except Exception as e:
        print(f"❌ Ошибка OLED: {e}")

# --- 4. Ультразвук (исправлен для Pi 5) ---
def ultrasonic():
    print("📏 Ультразвук: измерение расстояния (5 измерений)...")
    try:
        from gpiozero import DistanceSensor
        sensor = DistanceSensor(echo=24, trigger=23)
        for i in range(5):
            dist = sensor.distance * 100  # в см
            print(f"  {i+1}: {dist:.1f} см")
            time.sleep(0.5)
        sensor.close()
        print("✅ Ультразвук завершён")
    except Exception as e:
        print(f"❌ Ошибка ультразвука: {e}")

# --- 5. Видеопоток (MJPEG) ---
def camera_stream():
    print("📷 Запуск видеопотока на http://192.168.1.56:6001/?action=stream")
    try:
        os.system("pkill -f mjpg_streamer")
        cmd = "mjpg_streamer -i 'input_uvc.so -d /dev/video0 -r 640x480 -f 30' -o 'output_http.so -p 6001 -w /usr/local/share/mjpg-streamer/www'"
        subprocess.Popen(cmd, shell=True)
        print("✅ Видеопоток запущен (порт 6001). Нажмите Enter для остановки.")
        input()
        os.system("pkill -f mjpg_streamer")
        print("✅ Видеопоток остановлен")
    except Exception as e:
        print(f"❌ Ошибка видео: {e}")

# --- 6. Лица (без окон, только сохранение) ---
def face_detection():
    print("👤 Распознавание лиц (без окон, фото сохраняется)")
    try:
        import mediapipe as mp
        mp_face = mp.solutions.face_detection
        face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Камера не доступна")
            return
        found = False
        for _ in range(50):  # попыток (≈2-3 секунды)
            ret, frame = cap.read()
            if not ret: continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_detection.process(rgb)
            if results.detections:
                found = True
                cv2.imwrite("/home/pi/face_detected.jpg", frame)
                print("📸 Лицо найдено, фото сохранено как face_detected.jpg")
                break
            time.sleep(0.1)
        cap.release()
        if not found:
            print("❌ Лицо не обнаружено за отведённое время")
        else:
            print("✅ Распознавание лиц завершено")
    except Exception as e:
        print(f"❌ Ошибка распознавания лиц: {e}")

# --- 7. QR (без окон) ---
def qr_code():
    print("📋 Распознавание QR-кодов (без окон)")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Камера не доступна")
            return
        detector = cv2.QRCodeDetector()
        found = False
        for _ in range(50):
            ret, frame = cap.read()
            if not ret: continue
            data, bbox, _ = detector.detectAndDecode(frame)
            if data:
                print(f"✅ QR-код: {data}")
                found = True
                break
            time.sleep(0.1)
        cap.release()
        if not found:
            print("❌ QR-код не обнаружен")
        else:
            print("✅ QR-сканер завершён")
    except Exception as e:
        print(f"❌ Ошибка QR: {e}")

# --- 8. Objectron (без окон) ---
def scene_recognition():
    print("🏞️ Распознавание объектов (Objectron, без окон)")
    try:
        import mediapipe as mp
        mp_obj = mp.solutions.objectron
        objectron = mp_obj.Objectron(static_image_mode=False, max_num_objects=5,
                                     min_detection_confidence=0.5, model_name='Chair')
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Камера не доступна")
            return
        found = False
        for _ in range(50):
            ret, frame = cap.read()
            if not ret: continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = objectron.process(rgb)
            if results.detected_objects:
                found = True
                cv2.imwrite("/home/pi/object_detected.jpg", frame)
                print("🔍 Объект обнаружен, фото сохранено как object_detected.jpg")
                break
            time.sleep(0.1)
        cap.release()
        if not found:
            print("❌ Объект не обнаружен")
        else:
            print("✅ Распознавание объектов завершено")
    except Exception as e:
        print(f"❌ Ошибка Objectron: {e}")

# --- 9. Микрофон ---
def microphone_test():
    print("🎤 Тест микрофона (запись 3 секунды)")
    try:
        import pyaudio
        import wave
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        RECORD_SECONDS = 3
        WAVE_OUTPUT_FILENAME = "/home/pi/test.wav"
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        stream.stop_stream(); stream.close(); p.terminate()
        wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(CHANNELS); wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE); wf.writeframes(b''.join(frames)); wf.close()
        print("✅ Запись сохранена в test.wav")
        os.system("aplay /home/pi/test.wav")
    except Exception as e:
        print(f"❌ Ошибка микрофона: {e}")

# --- 10. Динамик ---
def speaker_test():
    print("🔊 Тест динамика (проигрывание тестового MP3)")
    try:
        if not os.path.exists("/home/pi/test_sound.mp3"):
            os.system("wget -O /home/pi/test_sound.mp3 https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
        os.system("mpg123 /home/pi/test_sound.mp3")
        print("✅ Динамик протестирован")
    except Exception as e:
        print(f"❌ Ошибка динамика: {e}")

# --- Меню ---
def menu():
    print("\n" + "="*50)
    print("🤖 ДЕМО-СКРИПТ ВСЕХ ВОЗМОЖНОСТЕЙ (без моторов, без окон)")
    print("="*50)
    print("1. RGB-лента (цветовой круг)")
    print("2. Бипер (звуковой сигнал)")
    print("3. Дисплей (OLED информация)")
    print("4. Ультразвук (измерение расстояния)")
    print("5. Видеопоток (MJPEG на порт 6001)")
    print("6. Распознавание лиц (MediaPipe, без окон)")
    print("7. QR-коды (сканер, без окон)")
    print("8. Распознавание объектов (Objectron, без окон)")
    print("9. Микрофон (запись 3 сек)")
    print("10. Динамик (воспроизведение MP3)")
    print("0. ВЫХОД")
    print("="*50)

def main():
    while True:
        menu()
        choice = input("Выберите номер: ").strip()
        if choice == '1':
            rgb_test()
        elif choice == '2':
            beep_test()
        elif choice == '3':
            oled_info()
        elif choice == '4':
            ultrasonic()
        elif choice == '5':
            camera_stream()
        elif choice == '6':
            face_detection()
        elif choice == '7':
            qr_code()
        elif choice == '8':
            scene_recognition()
        elif choice == '9':
            microphone_test()
        elif choice == '10':
            speaker_test()
        elif choice == '0':
            print("👋 До свидания!")
            break
        else:
            print("❌ Неверный ввод")
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Прервано пользователем")
    finally:
        bot.Ctrl_WQ2812_ALL(0, 0)
        bot.Ctrl_BEEP_Switch(0)
        print("Ресурсы освобождены.")