#!/usr/bin/env python3
import os
from myrobot import Robot

r = Robot()

r.switch_wifi(os.environ["WIFI_AI_SSID"], os.environ["WIFI_AI_PASS"])

print("📸 Делаю фото и отправляю на описание...")
description = r.describe_scene("Ты видишь здесь человеческое лицо. Ответь только True или False")
print("\n" + "="*50)
print("🧠 ОПИСАНИЕ СЦЕНЫ:")
print("="*50)
print(description)
print("="*50)
r.restore()

r.switch_wifi(os.environ["WIFI_HOME_SSID"], os.environ["WIFI_HOME_PASS"])