from myrobot import Robot, os, time
from threading import Thread
import signal
import sys

r = Robot()

# ===== МУЗЫКА (в отдельном потоке) =====
def music():
    r.play_mp3("/home/pi/Happy_Birthday_Happy_Birthday_to_You_Music_Easy_Kids_Songs_-_Happy_Birthday_73703391.mp3")

rg = Thread(target=music, daemon=True)
rg.start()

# ===== RGB-ШОУ (в отдельном потоке) =====
def random_rgb_cod():
    from Raspbot_Lib import Raspbot, LightShow
    import time

    bot = Raspbot()
    lights = LightShow()

    try:
        while True:
            lights.execute_effect('random_running', lights.MAX_TIME, 0.1, -1)
    except KeyboardInterrupt:
        pass
    finally:
        lights.stop()
        lights.turn_off_all_lights()
        print("💡 RGB-лента выключена")

t = Thread(target=random_rgb_cod, daemon=True)
t.start()

# ===== ОБРАБОТЧИК ПРЕРЫВАНИЙ В ГЛАВНОМ ПОТОКЕ =====
def signal_handler(sig, frame):
    print("\n🛑 Остановка робота...")
    r.stop()
    r.restore()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # завершение процесса

# ===== ОСНОВНОЙ БЛОК =====
try:
    print("🎵 Включаю музыку и световое шоу...")
    r.rotate_left(10)   # медленное вращение
    time.sleep(10)      # 10 секунд

except KeyboardInterrupt:
    # Дополнительная защита (на всякий случай)
    print("\n🛑 Прервано пользователем")
finally:
    # Остановка в любом случае (даже если не было Ctrl+C)
    r.stop()
    r.restore()
    print("🎉 Скрипт завершён")