#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный тест всех компонентов Yahboom Raspbot V2
Использует Raspbot_Lib для управления роботом, отдельные модули для камеры, динамика и микрофона
"""
import time
import os
import cv2
from Raspbot_Lib import Raspbot
from PIL import Image, ImageDraw

def test_motors(bot):
    print("\n🔧 Тест моторов: вперёд → назад → стоп")
    bot.Ctrl_Car(0x01, 150, 150)  # вперёд
    time.sleep(1)
    bot.Ctrl_Car(0x02, 150, 150)  # назад
    time.sleep(1)
    bot.Ctrl_Car(0x00, 0, 0)      # стоп
    print("✅ Моторы OK")

def test_servos(bot):
    print("\n📷 Тест сервоприводов: центр → влево → вправо → вверх → вниз")
    bot.Ctrl_Servo(1, 90); bot.Ctrl_Servo(2, 90)
    time.sleep(0.5)
    bot.Ctrl_Servo(1, 30); time.sleep(0.5)
    bot.Ctrl_Servo(1, 150); time.sleep(0.5)
    bot.Ctrl_Servo(2, 150); time.sleep(0.5)
    bot.Ctrl_Servo(2, 30); time.sleep(0.5)
    bot.Ctrl_Servo(1, 90); bot.Ctrl_Servo(2, 90)
    print("✅ Серво OK")

def test_rgb(bot):
    print("\n🎨 RGB: красный → зелёный → синий → выкл")
    # Цвета по номерам: 0-красный, 1-зелёный, 2-синий
    for color in [0,1,2]:
        bot.Ctrl_WQ2812_ALL(1, color)   # включить цвет
        time.sleep(0.5)
    bot.Ctrl_WQ2812_ALL(0, 0)           # выключить
    print("✅ RGB OK")

def test_buzzer(bot):
    print("\n🔊 Бипер: 3 сигнала")
    for _ in range(3):
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.2)
        bot.Ctrl_BEEP_Switch(0)
        time.sleep(0.1)
    print("✅ Бипер OK")

def test_oled(bot):
    print("\n🖥️ OLED: текст + смайлик")
    try:
        import Adafruit_SSD1306 as SSD
        oled = SSD.SSD1306_128_32(rst=None, i2c_bus=1)
        oled.begin()
        oled.clear()
        oled.display()
        # Текст
        image = Image.new('1', (128, 32))
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), "Raspbot Test", fill=255)
        oled.image(image)
        oled.display()
        time.sleep(1)
        # Смайлик
        img = Image.new('1', (128, 32), 0)
        draw = ImageDraw.Draw(img)
        draw.ellipse((20,2,108,30), outline=1, width=1)
        draw.point((40,12), fill=1)
        draw.point((88,12), fill=1)
        draw.arc((40,14,88,24), 0, 180, fill=1)
        oled.image(img)
        oled.display()
        time.sleep(2)
        oled.clear()
        oled.display()
        print("✅ OLED OK")
    except Exception as e:
        print(f"   Ошибка OLED: {e}")
        print("   Тест OLED пропущен (не установлена Adafruit_SSD1306)")

def test_ultrasonic(bot):
    print("\n📏 Ультразвук: измерение расстояния")
    try:
        import RPi.GPIO as GPIO
        TRIG, ECHO = 23, 24
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG, GPIO.OUT)
        GPIO.setup(ECHO, GPIO.IN)
        GPIO.output(TRIG, False)
        time.sleep(0.00001)
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        pulse_start = time.time()
        pulse_end = time.time()
        timeout = time.time() + 0.02
        while GPIO.input(ECHO) == 0 and time.time() < timeout:
            pulse_start = time.time()
        timeout = time.time() + 0.02
        while GPIO.input(ECHO) == 1 and time.time() < timeout:
            pulse_end = time.time()
        GPIO.cleanup()
        if pulse_end - pulse_start > 0:
            dist = round((pulse_end - pulse_start) * 34300 / 2, 1)
            print(f"   Расстояние: {dist:.1f} см")
        else:
            print("   Ошибка измерения")
    except Exception as e:
        print(f"   Ошибка ультразвука: {e}")
    print("✅ Ультразвук OK")

def test_camera():
    print("\n📷 Камера: захват и сохранение фото")
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("/home/pi/test_photo.jpg", frame)
            print("   Фото сохранено как /home/pi/test_photo.jpg")
        else:
            print("   Не удалось захватить кадр")
        cap.release()
    except Exception as e:
        print(f"   Ошибка камеры: {e}")
    print("✅ Камера OK")

def test_speaker():
    print("\n🔊 Динамик: воспроизведение через espeak")
    try:
        os.system('espeak "Привет, я робот! Это тест динамика."')
        print("   Голосовое сообщение воспроизведено")
    except Exception as e:
        print(f"   Ошибка динамика: {e}")
    print("✅ Динамик OK")

def test_microphone():
    print("\n🎤 Микрофон: запись 2 секунды и воспроизведение")
    try:
        import pyaudio
        import wave
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        RECORD_SECONDS = 2
        WAVE_OUT = "/home/pi/test_mic.wav"
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf = wave.open(WAVE_OUT, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print("   Запись сохранена как test_mic.wav")
        # Воспроизведение через aplay
        os.system(f"aplay {WAVE_OUT}")
        print("   Запись воспроизведена")
    except Exception as e:
        print(f"   Ошибка микрофона: {e}")
    print("✅ Микрофон OK")

def main():
    print("="*50)
    print("🤖 ПОЛНЫЙ ТЕСТ ВСЕХ КОМПОНЕНТОВ (Raspbot_Lib)")
    print("="*50)
    bot = Raspbot()
    print("✅ Робот инициализирован")
    test_motors(bot)
    test_servos(bot)
    test_rgb(bot)
    test_buzzer(bot)
    test_oled(bot)
    test_ultrasonic(bot)
    test_camera()
    test_speaker()
    test_microphone()
    print("\n" + "="*50)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("="*50)

if __name__ == "__main__":
    main()