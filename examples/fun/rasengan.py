   
# rasengan.py – Расенган на роботе (синий/белый, вращение, звук)
import myrobot
import time
import threading
import os

r = myrobot.Robot()

# ===== НАСТРОЙКИ =====
SOUND_FILE = "/home/pi/naruto_rasengan-145.mp3"   # путь к твоему mp3 с Расенганом
ROTATE_SPEED = 255                     # максимальная скорость
EFFECT_SPEED = 0.04                    # скорость мерцания
DURATION = 10                          # общая длительность (сек), подбери под звук

# ===== ЗАПУСК ЗВУКА (в фоне) =====
def play_sound():
    if os.path.exists(SOUND_FILE):
        os.system(f'mpg123 -f 50000 "{SOUND_FILE}" &')
    else:
        print(f"⚠️ Файл {SOUND_FILE} не найден – звук не воспроизводится")

# ===== МЕРЦАНИЕ СВЕТОДИОДОВ (голубой <-> белый) =====
def rasengan_lights():
    end_time = time.time() + DURATION
    color_index = 5  # голубой (5) и белый (6)
    while time.time() < end_time:
        col = 5 if color_index == 5 else 6
        # Зажигаем все 13 светодиодов текущим цветом
        for i in range(1, 14):
            r.rgb_led(i, col)
        color_index = 5 if color_index == 6 else 5
        time.sleep(EFFECT_SPEED)

# ===== ЗАПУСК ВСЕГО ОДНОВРЕМЕННО =====
sound_thread = threading.Thread(target=play_sound)
lights_thread = threading.Thread(target=rasengan_lights)

# Запускаем звук и мерцание
sound_thread.start()
lights_thread.start()

# Начинаем вращение вправо на максимальной скорости
r.rotate_right(ROTATE_SPEED)
# Ждём, пока отработает свет и звук (или пока сам не остановим)
lights_thread.join()
r.stop()           # остановить вращение
r.rgb_off()        # выключить свет

print("🌀 Расенган завершён!")