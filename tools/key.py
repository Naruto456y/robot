#!/usr/bin/env python3
from Raspbot_Lib import Raspbot
import time

bot = Raspbot()

print("🔘 Жду нажатия KEY. Нажмите Ctrl+C для выхода.")

while True:
    # Читаем состояние кнопки (обычно 0 — нажата, 1 — отпущена)
    key_state = bot.read_data_array(0x0C, 1)[0]  # регистр 0x0C — KEY

    if key_state == 0:
        print("✅ Кнопка KEY нажата! Делаю фото...")
        # Твоя команда: например, камера или звук
        bot.Ctrl_BEEP_Switch(1)
        time.sleep(0.2)
        bot.Ctrl_BEEP_Switch(0)
        time.sleep(0.3)

    time.sleep(0.1)