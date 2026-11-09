#!/usr/bin/env python3
# face_beep.py – пищать при появлении лица
import myrobot

r = myrobot.Robot()

try:
    print("👀 Запущено обнаружение лиц. Для выхода нажмите Ctrl+C")
    r.detect_faces_stream(
        beep_on=True,           # ✅ издавать звук при обнаружении
        say_text=None,          # без голосового сообщения
        rgb_on=False,           # не включать RGB-ленту
        save_photo=False,       # не сохранять фото
        draw_boxes=False,       # не рисовать рамки (можно True, если хочешь видеть)
        confidence=0.8        # порог уверенности
    )
except KeyboardInterrupt:
    print("\n🛑 Остановлено")
finally:
    r.restore()                 # корректно выключить моторы и вернуть настройки