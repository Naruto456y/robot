#!/usr/bin/env python3
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
import psutil
import time
import socket

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32, rotate=0)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
except:
    font = ImageFont.load_default()

def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

while True:
    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, 31), outline="black", fill="black")
        draw.text((0, 0), f"IP: {get_ip()}", font=font, fill="white")
        draw.text((0, 10), f"CPU: {psutil.cpu_percent():5.1f}%", font=font, fill="white")
        ram = psutil.virtual_memory()
        draw.text((0, 20), f"RAM: {ram.percent:5.1f}%", font=font, fill="white")
    time.sleep(2)