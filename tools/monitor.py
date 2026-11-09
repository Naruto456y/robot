#!/usr/bin/env python3
import os
import time
import subprocess

print("🔍 Мониторинг процессов OLED и RGB")
print("Нажмите Ctrl+C для выхода.\n")

while True:
    # 1. Процессы, связанные с OLED
    try:
        oled_procs = subprocess.check_output("ps aux | grep -E 'oled|yahboom_oled' | grep -v grep", shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        oled_procs = ""

    # 2. Процессы, связанные с RGB (если есть)
    try:
        rgb_procs = subprocess.check_output("ps aux | grep -E 'WQ2812|Ctrl_Car' | grep -v grep", shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        rgb_procs = ""

    # 3. Проверка, запущен ли стандартный OLED-скрипт
    if "yahboom_oled.py" in oled_procs:
        print("⚠️  Обнаружен стандартный OLED-скрипт (yahboom_oled.py). Он может мешать.")
        print(oled_procs)
    else:
        print("✅ Стандартный OLED-скрипт не обнаружен.")

    # 4. Показать текущее состояние RGB (если есть активные процессы)
    if rgb_procs:
        print("🎨 Активные RGB-процессы:")
        print(rgb_procs)

    # 5. Проверка, открыт ли I2C для OLED (адрес 0x3C)
    i2c_check = subprocess.run("sudo i2cdetect -y 1 | grep 3c", shell=True, capture_output=True, text=True)
    if i2c_check.stdout:
        print("✅ I2C-адрес OLED (0x3C) доступен.")
    else:
        print("❌ I2C-адрес OLED не обнаружен! Проверьте подключение.")

    # 6. Проверка, используется ли дисплей в данный момент (через lsof)
    try:
        lsof_check = subprocess.check_output("sudo lsof /dev/i2c-1 2>/dev/null | grep python", shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        lsof_check = ""

    if lsof_check:
        print("📟 OLED используется процессами:")
        print(lsof_check)
    else:
        print("📟 OLED не используется другими процессами.")

    print("-" * 50)
    time.sleep(2)
