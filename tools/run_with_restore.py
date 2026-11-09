#!/usr/bin/env python3
import sys
import os
import subprocess
import atexit
import signal

restored = False

def restore():
    global restored
    if restored:
        return
    restored = True
    os.system("/home/pi/restore_oled.sh")

atexit.register(restore)
signal.signal(signal.SIGINT, lambda s, f: (restore(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda s, f: (restore(), sys.exit(0)))

# Отключаем OLED (быстро)
os.system("sudo pkill -f yahboom_oled.py")
os.system("sudo pkill -f oled_system.py")

# Центрируем камеру в отдельном процессе (чтобы не нагружать основной)
os.system("python3 -c \"from Raspbot_Lib import Raspbot; bot=Raspbot(); bot.Ctrl_Servo(1,95); bot.Ctrl_Servo(2,25)\"")

if len(sys.argv) < 2:
    print("❌ Укажите скрипт для запуска")
    sys.exit(1)

script_path = sys.argv[1]
script_args = sys.argv[2:]

try:
    result = subprocess.run([sys.executable, script_path] + script_args)
    sys.exit(result.returncode)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    sys.exit(1)