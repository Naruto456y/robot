#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
import psutil
import socket

# Путь к библиотеке Yahboom OLED
sys.path.append('/home/pi/software/oled_yahboom/')
from yahboom_oled import Yahboom_OLED

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

def get_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return f"{int(f.read())/1000:.1f}°C"
    except:
        return "N/A"

# Инициализация
oled = Yahboom_OLED(debug=False)
oled.init_oled_process()

while True:
    # Данные
    ip = get_ip()
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    temp = get_temp()

    # Очистка и вывод
    oled.clear()
    oled.add_line(f"IP: {ip}", 1)
    oled.add_line(f"CPU: {cpu:5.1f}%", 2)
    oled.add_line(f"RAM: {ram.percent:5.1f}%", 3)
    oled.add_line(f"Temp: {temp}", 4)
    oled.refresh()

    time.sleep(2)