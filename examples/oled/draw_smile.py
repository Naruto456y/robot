#!/usr/bin/env python3
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw
import time

# Правильные параметры для твоего дисплея
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32, rotate=0)

with canvas(device) as draw:
    # Очистка
    draw.rectangle((0, 0, 127, 31), outline="black", fill="black")

    # Рисуем смайлик
    draw.ellipse((20, 2, 108, 30), outline="white", width=1)   # голова
    draw.point((40, 12), fill="white")                         # левый глаз
    draw.point((88, 12), fill="white")                         # правый глаз
    draw.arc((40, 14, 88, 24), start=0, end=180, fill="white") # улыбка

print("Смайлик нарисован!")

time.sleep(10)