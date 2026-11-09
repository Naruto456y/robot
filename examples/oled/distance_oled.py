#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from gpiozero import DistanceSensor
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

# ========== НАСТРОЙКИ УЛЬТРАЗВУКА ==========
TRIG = 23
ECHO = 24
sensor = DistanceSensor(echo=ECHO, trigger=TRIG, max_distance=2)

# ========== НАСТРОЙКА OLED ==========
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32, rotate=0)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font = ImageFont.load_default()

def oled_show(line1="", line2="", line3="", line4=""):
    with canvas(device) as draw:
        draw.rectangle((0,0,127,31), outline="black", fill="black")
        y = 0
        for text in [line1, line2, line3, line4]:
            if text:
                draw.text((0, y), text, font=font, fill="white")
            y += 8

print("📏 Ультразвук + OLED. Нажмите Ctrl+C для выхода.")
oled_show("Ultrasonic:", "Ready...")

try:
    while True:
        distance = sensor.distance * 100  # метры → см
        if distance < 2.0:  # если слишком близко
            msg = "Too close!"
        else:
            msg = f"{distance:.1f} cm"
        print(f"📏 {msg}")
        oled_show("Ultrasonic:", msg)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    sensor.close()
    oled_show("", "", "", "")
    print("🏁 Ресурсы освобождены.")
