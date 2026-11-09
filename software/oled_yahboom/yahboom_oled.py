#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import os
import subprocess
import datetime
from Raspbot_Lib import Raspbot
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306 as SSD

class Yahboom_OLED:
    def __init__(self, i2c_bus=1, debug=False):
        self.debug = debug
        self.i2c_bus = i2c_bus
        self.top = -2
        self.x = 0
        self.total_last = 0
        self.idle_last = 0
        self.str_CPU = "CPU:0%"

    def begin(self):
        try:
            self.oled = SSD.SSD1306_128_32(rst=None, i2c_bus=self.i2c_bus, gpio=1)
            self.oled.begin()
            self.oled.clear()
            self.oled.display()
            self.width = self.oled.width
            self.height = self.oled.height
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
            self.font = ImageFont.load_default()
            if self.debug:
                # print("OLED init OK")
                pass
            return True
        except Exception as e:
            if self.debug:
                print(f"OLED init error: {e}")
            return False

    def clear(self, refresh=False):
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        if refresh:
            self.refresh()

    def refresh(self):
        self.oled.image(self.image)
        self.oled.display()

    def add_text(self, start_x, start_y, text, refresh=False):
        if start_x > 128 or start_x < 0 or start_y < 0 or start_y > 32:
            return
        x = int(start_x + self.x)
        y = int(start_y + self.top)
        self.draw.text((x, y), str(text), font=self.font, fill=255)
        if refresh:
            self.refresh()

    def add_line(self, text, line=1, refresh=False):
        if line < 1 or line > 4:
            return
        y = int(8 * (line - 1))
        self.add_text(0, y, text, refresh)

    def get_CPU(self):
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            data = [int(x) for x in line.split()[1:10]]
            total = sum(data)
            idle = data[3]
            if self.total_last == 0:
                self.total_last = total
                self.idle_last = idle
                return "CPU: 0%"
            total_delta = total - self.total_last
            idle_delta = idle - self.idle_last
            self.total_last = total
            self.idle_last = idle
            if total_delta == 0:
                return "CPU: 0%"
            usage = int((1 - idle_delta / total_delta) * 100)
            return f"CPU:{usage:2d}%"
        except:
            return "CPU:ERR"

    def get_time(self):
        try:
            # Пытаемся использовать московское время через pytz
            try:
                import pytz
                tz = pytz.timezone('Europe/Moscow')
                now = datetime.datetime.now(tz)
            except:
                # Если pytz нет — используем UTC+3 вручную
                now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
            return now.strftime("%H:%M")
        except:
            return "00:00"

    def get_ram(self):
        try:
            result = subprocess.check_output("free | awk 'NR==2{printf \"RAM:%2d%% -> %.1fGB\", 100*($2-$7)/$2, ($2/1048576.0)}'", shell=True)
            return result.decode().strip()
        except:
            return "RAM:ERR"

    def get_disk(self):
        try:
            result = subprocess.check_output("df -h | awk '$NF==\"/\"{printf \"SDC:%s -> %.1fGB\", $5, $2}'", shell=True)
            return result.decode().strip()
        except:
            return "SDC:ERR"

    def get_ip(self):
        try:
            ip = os.popen("/sbin/ifconfig eth0 | grep 'inet ' | awk '{print $2}'").read().strip()
            if not ip:
                ip = os.popen("/sbin/ifconfig wlan0 | grep 'inet ' | awk '{print $2}'").read().strip()
            if not ip:
                ip = "No IP"
            if len(ip) > 15:
                ip = "No IP"
            return ip
        except:
            return "No IP"

    def main_program(self):
        if not self.begin():
            time.sleep(2)
            return
        while True:
            self.clear()
            cpu = self.get_CPU()
            time_str = self.get_time()
            self.add_line(f"{cpu}  {time_str}", 1)   # CPU + московское время
            self.add_line(self.get_ram(), 2)
            self.add_line(self.get_disk(), 3)
            self.add_line("IP:" + self.get_ip(), 4)
            self.refresh()
            time.sleep(2)

try:
    oled = Yahboom_OLED(debug=True)
    oled.main_program()
except KeyboardInterrupt:
    oled.clear(True)
    print("OLED stopped")