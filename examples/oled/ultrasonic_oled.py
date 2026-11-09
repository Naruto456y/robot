#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import time
from Raspbot_Lib import Raspbot

# ========== ПОДКЛЮЧЕНИЕ OLED (через luma.oled) ==========
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

# Настройка OLED (адрес 0x3C, размер 128x32)
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32, rotate=0)

# Шрифт (можно стандартный)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font = ImageFont.load_default()

def oled_show(line1="", line2="", line3="", line4=""):
    """Выводит до 4 строк на OLED"""
    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 31), outline="black", fill="black")
        y = 0
        for text in [line1, line2, line3, line4]:
            if text:
                draw.text((0, y), text, font=font, fill="white")
            y += 8

# ========== ИНИЦИАЛИЗАЦИЯ РОБОТА ==========
bot = Raspbot()

def get_distance():
    """Возвращает расстояние в см или -1 при ошибке"""
    try:
        bot.Ctrl_Ulatist_Switch(1)
        time.sleep(0.05)
        diss_H = bot.read_data_array(0x1b, 1)[0]
        diss_L = bot.read_data_array(0x1a, 1)[0]
        dis_mm = (diss_H << 8) | diss_L
        if dis_mm == 0:
            return -1
        return dis_mm / 10.0
    except Exception as e:
        print(f"Ошибка: {e}")
        return -1

# ========== ОСНОВНОЙ ЦИКЛ ==========
print("📏 Ультразвук + OLED. Нажмите Ctrl+C для выхода.")
oled_show("Ultrasonic:", "Ready...")

try:
    while True:
        dist = get_distance()
        if dist > 0:
            msg = f"{dist:5.1f} cm"
            print(f"📏 {msg}")
            oled_show("Ultrasonic:", msg)
        else:
            print("❌ Ошибка измерения")
            oled_show("Ultrasonic:", "ERROR")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    oled_show("", "", "", "")
    bot.Ctrl_Ulatist_Switch(0)
    print("🏁 Ресурсы освобождены")