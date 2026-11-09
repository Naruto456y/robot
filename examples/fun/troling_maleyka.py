#!/usr/bin/env python3
from Raspbot_Lib import Raspbot
import time
import os
import sys
import signal
import atexit

bot = Raspbot()
restored = False

def restore_all():
    global restored
    if restored:
        return
    restored = True
    print("🔄 Восстановление...")
    os.system("pkill -f h.py 2>/dev/null")
    os.system("pkill -f yahboom_oled.py 2>/dev/null")
    if os.path.exists("/home/pi/software/oled_yahboom/yahboom_oled.py"):
        os.system("python3 /home/pi/software/oled_yahboom/yahboom_oled.py &")
    try:
        bot.Ctrl_Servo(1, 95)
        bot.Ctrl_Servo(2, 25)
    except:
        pass
    print("✅ Восстановлено")

atexit.register(restore_all)
signal.signal(signal.SIGINT, lambda s, f: (restore_all(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda s, f: (restore_all(), sys.exit(0)))

# Отключаем OLED
os.system("sudo pkill -f yahboom_oled.py")
os.system("sudo pkill -f oled_system.py")

try:
    bot.Ctrl_Servo(1, 95)
    bot.Ctrl_Servo(2, 25)
except:
    pass

print("✅ Стандартный OLED отключён, камера в центре")

# ========== КНОПКИ ==========
# ПРАВИЛЬНЫЙ РЕГИСТР ДЛЯ KEY — 0x0D
REGISTER_KEY = 0x0D

def key_pressed():
    try:
        val = bot.read_data_array(REGISTER_KEY, 1)[0]
        return val == 0x01  # 0x01 — нажата, 0x00 — отпущена
    except Exception as e:
        return False

# Кнопка на голове (GPIO17)
HEAD_GPIO = 17
head_available = False
try:
    from gpiozero import Button
    head_button = Button(HEAD_GPIO, pull_up=True)
    head_available = True
    print("✅ Кнопка на голове (GPIO17) подключена")
except Exception as e:
    print(f"⚠️ GPIO17 недоступен: {e}")

print("🔘 Слушаю кнопки:")
print("   KEY (регистр 0x0D) → писк")
print("   Голова (GPIO17) → 'Привет'")
print("   Ctrl+C для выхода.")

try:
    while True:
        # KEY
        if key_pressed():
            os.system("play /home/pi/6588c6c12a849af2a7660e9dc55e8c4c.mp3")

        # Голова
        if head_available and head_button.is_pressed:
            print("🔘 Кнопка на голове нажата!")
            os.system('espeak -v ru "Привет, я робот" 2>/dev/null')
            time.sleep(1)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    restore_all()