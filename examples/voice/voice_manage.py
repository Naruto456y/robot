#!/usr/bin/env python3
# voice_control.py – голосовое управление роботом
import myrobot
import speech_recognition as sr
import time
import sys

r = myrobot.Robot()
recognizer = sr.Recognizer()
mic = sr.Microphone()

# Подстройка под шум
print("🎤 Калибровка микрофона (2 сек)...")
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=2)
print("✅ Готов к работе. Говорите команды.\n")

# ===== СЛОВАРИ КОМАНД =====
MOVE_COMMANDS = {
    "вперёд": ("forward", 150),
    "вперед": ("forward", 150),
    "forward": ("forward", 150),
    "назад": ("backward", 150),
    "backward": ("backward", 150),
    "влево": ("left", 130),
    "left": ("left", 130),
    "вправо": ("right", 130),
    "right": ("right", 130),
    "стоп": ("stop", 0),
    "stop": ("stop", 0),
    "остановись": ("stop", 0),
    "поворот влево": ("rotate_left", 150),
    "поворот вправо": ("rotate_right", 150),
}

CAMERA_COMMANDS = {
    "камера влево": "left",
    "камера вправо": "right",
    "камера вверх": "up",
    "камера вниз": "down",
    "камера центр": "center",
    "центр": "center",
}

SPEED_UP = ["быстрее", "ускорься"]
SPEED_DOWN = ["медленнее", "замедлись", "тише"]

current_speed = 150


def listen_command():
    """Слушает микрофон и возвращает распознанный текст."""
    try:
        with mic as source:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=4)
        text = recognizer.recognize_google(audio, language="ru-RU").lower()
        return text
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"❌ Ошибка сети: {e}")
        return ""
    except Exception as e:
        print(f"❌ Ошибка микрофона: {e}")
        return ""


def execute_command(text):
    """Выполняет команду по распознанному тексту."""
    global current_speed

    if not text:
        return

    print(f"👤 Вы сказали: {text}")

    # === ДВИЖЕНИЕ ===
    for keyword, (cmd, speed) in MOVE_COMMANDS.items():
        if keyword in text:
            if cmd == "forward":
                r.forward(current_speed)
            elif cmd == "backward":
                r.backward(current_speed)
            elif cmd == "left":
                r.left(current_speed)
            elif cmd == "right":
                r.right(current_speed)
            elif cmd == "stop":
                r.stop()
            elif cmd == "rotate_left":
                r.rotate_left(current_speed)
            elif cmd == "rotate_right":
                r.rotate_right(current_speed)
            print(f"🏎️ Команда: {cmd} (скорость {current_speed})")
            return

    # === КАМЕРА ===
    for keyword, direction in CAMERA_COMMANDS.items():
        if keyword in text:
            if direction == "left":
                r.camera_left()
            elif direction == "right":
                r.camera_right()
            elif direction == "up":
                r.camera_up()
            elif direction == "down":
                r.camera_down()
            elif direction == "center":
                r.camera_center()
            print(f"📷 Камера: {direction}")
            return

    # === СКОРОСТЬ ===
    if any(w in text for w in SPEED_UP):
        current_speed = min(255, current_speed + 30)
        print(f"⚡ Скорость: {current_speed}")
        return
    if any(w in text for w in SPEED_DOWN):
        current_speed = max(60, current_speed - 30)
        print(f"🐢 Скорость: {current_speed}")
        return

    # === ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ===
    if "привет" in text:
        r.say("Привет, хозяин!")
        return
    if "фото" in text or "снимок" in text:
        r.save_photo(f"/home/pi/voice_photo_{int(time.time())}.jpg")
        r.say("Фото сохранено")
        return
    if "пискни" in text or "бип" in text:
        r.beep_short(2)
        return
    if "что ты видишь" in text or "опиши сцену" in text:
        r.say("Смотрю...")
        desc = r.describe_scene()
        r.say(desc[:200])
        return
    if "выключи свет" in text or "свет выключи" in text:
        r.rgb_off()
        return
    if "включи свет" in text:
        r.rgb_color(6)  # белый
        return
    if "заряд" in text or "батарея" in text:
        r.say(f"Заряд: {r.get_battery()} процентов")
        return
    if "выход" in text or "выключись" in text or "пока" in text:
        r.say("До свидания!")
        r.stop()
        r.restore()
        sys.exit(0)

    print("🤔 Команда не распознана")


if __name__ == "__main__":
    try:
        while True:
            print("🎤 Слушаю...")
            text = listen_command()
            execute_command(text)
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\n🛑 Завершение")
        r.stop()
        r.restore()