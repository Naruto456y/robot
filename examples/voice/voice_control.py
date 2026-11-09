#!/usr/bin/env python3
from moonshine_voice import MicTranscriber
from myrobot import Robot
import time

# Инициализация робота
robot = Robot()
robot.rgb_off()

# Функции для команд
def forward():
    print("🔊 Команда: Вперёд")
    robot.forward(150)
    robot.oled_show_text("Вперёд!")

def backward():
    print("🔊 Команда: Назад")
    robot.backward(150)
    robot.oled_show_text("Назад!")

def stop_robot():
    print("🔊 Команда: Стоп")
    robot.stop()
    robot.oled_show_text("Стоп")

def left():
    print("🔊 Команда: Влево")
    robot.left(150)
    robot.oled_show_text("Влево")

def right():
    print("🔊 Команда: Вправо")
    robot.right(150)
    robot.oled_show_text("Вправо")

print("🎤 Слушаю команды: вперёд, назад, влево, вправо, стоп")
print("Нажмите Ctrl+C для выхода.")

# Настройка транскрипции
transcriber = MicTranscriber(language="ru")

def process_text(text):
    text = text.lower().strip()
    if not text:
        return
    print(f"🔍 Распознано: {text}")
    if "вперёд" in text or "вперед" in text:
        forward()
    elif "назад" in text:
        backward()
    elif "стоп" in text or "стой" in text:
        stop_robot()
    elif "влево" in text:
        left()
    elif "вправо" in text:
        right()
    else:
        print(f"⚠️ Неизвестная команда: {text}")

try:
    while True:
        # Записываем 3 секунды и распознаём
        text = transcriber.transcribe(duration=3)
        process_text(text)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    robot.restore()