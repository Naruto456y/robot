#!/usr/bin/env python3
from Raspbot_Lib import Raspbot
import time
import os
import subprocess

bot = Raspbot()

# 1. Три писка
for _ in range(3):
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.3)
    bot.Ctrl_BEEP_Switch(0)
    time.sleep(0.2)

# 2. Камера в центр
bot.Ctrl_Servo(1, 95)
bot.Ctrl_Servo(2, 25)

# 3. OLED (запускаем в фоне)
subprocess.Popen(["python3", "/home/pi/software/oled_yahboom/yahboom_oled.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# 4. Запускаем raspbot.pyc (если нужно) в фоне
subprocess.Popen(["python3", "/home/pi/project_demo/raspbot/raspbot.pyc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("✅ Стартовый скрипт выполнен")