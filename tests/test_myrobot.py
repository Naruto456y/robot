#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Полный тест модуля myrobot (все публичные и приватные методы).
Запуск: python3 /home/pi/test_myrobot.py
"""

import sys
import time
import os

# Добавляем путь, если нужно
sys.path.insert(0, '/home/pi')

# ========== ИМПОРТ МОДУЛЯ ==========
print("⏳ Импорт myrobot...")
import myrobot
from myrobot import Robot, r, t

print("✅ Импорт выполнен")

# ========== СОЗДАНИЕ ЭКЗЕМПЛЯРА ==========
robot = Robot()
print("🤖 Робот инициализирован")

# ========== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ==========
def test_method(name, func, *args, **kwargs):
    """Безопасно выполняет метод и выводит результат."""
    try:
        print(f"  ▶️ {name}...", end=" ")
        result = func(*args, **kwargs)
        print(f"✅ {result if result is not None else 'OK'}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

# ========== ТЕСТЫ ==========
print("\n" + "="*60)
print("🔍 ТЕСТИРОВАНИЕ МОДУЛЯ myrobot")
print("="*60)

# ========== 1. ВНУТРЕННИЕ МЕТОДЫ ==========
print("\n📦 1. ВНУТРЕННИЕ МЕТОДЫ")

test_method("_kill_oled()", robot._kill_oled)
test_method("_oled_init()", robot._oled_init)
test_method("_set_deflection(150, 90)", robot._set_deflection, 150, 90)
test_method("_move(90, 100)", robot._move, 90, 100)
# _start_flask_stream и _start_mjpg_streamer не тестируем (запускают серверы)
test_method("_get_openrouter_key()", robot._get_openrouter_key)
test_method("_get_qwen_key()", robot._get_qwen_key)

# ========== 2. ДВИЖЕНИЕ ==========
print("\n🏎️ 2. ДВИЖЕНИЕ")
test_method("forward(100)", robot.forward, 100)
time.sleep(0.3)
test_method("backward(100)", robot.backward, 100)
time.sleep(0.3)
test_method("left(100)", robot.left, 100)
time.sleep(0.3)
test_method("right(100)", robot.right, 100)
time.sleep(0.3)
test_method("stop()", robot.stop)
test_method("rotate_left(100)", robot.rotate_left, 100)
time.sleep(0.3)
test_method("rotate_right(100)", robot.rotate_right, 100)
time.sleep(0.3)
test_method("diagonal_left_forward(100)", robot.diagonal_left_forward, 100)
time.sleep(0.3)
test_method("diagonal_right_forward(100)", robot.diagonal_right_forward, 100)
time.sleep(0.3)
test_method("diagonal_left_backward(100)", robot.diagonal_left_backward, 100)
time.sleep(0.3)
test_method("diagonal_right_backward(100)", robot.diagonal_right_backward, 100)
time.sleep(0.3)
test_method("stop() (повторно)", robot.stop)

# ========== 3. КАМЕРА ==========
print("\n📷 3. КАМЕРА")
test_method("camera_center()", robot.camera_center)
time.sleep(0.3)
test_method("camera_left()", robot.camera_left)
time.sleep(0.3)
test_method("camera_right()", robot.camera_right)
time.sleep(0.3)
test_method("camera_up()", robot.camera_up)
time.sleep(0.3)
test_method("camera_down()", robot.camera_down)
time.sleep(0.3)
test_method("camera_set(1, 90)", robot.camera_set, 1, 90)
time.sleep(0.3)
test_method("camera_set(2, 45)", robot.camera_set, 2, 45)
time.sleep(0.3)
test_method("camera_center() (возврат)", robot.camera_center)

# ========== 4. RGB ==========
print("\n🎨 4. RGB")
test_method("rgb_color(0) красный", robot.rgb_color, 0)
time.sleep(0.3)
test_method("rgb_color(1) зелёный", robot.rgb_color, 1)
time.sleep(0.3)
test_method("rgb_color(2) синий", robot.rgb_color, 2)
time.sleep(0.3)
test_method("rgb_color(3) жёлтый", robot.rgb_color, 3)
time.sleep(0.3)
test_method("rgb_color(4) фиолетовый", robot.rgb_color, 4)
time.sleep(0.3)
test_method("rgb_color(5) голубой", robot.rgb_color, 5)
time.sleep(0.3)
test_method("rgb_color(6) белый", robot.rgb_color, 6)
time.sleep(0.3)
test_method("rgb_color(7) выключить", robot.rgb_color, 7)
test_method("rgb_off()", robot.rgb_off)
test_method("rgb_led(0, 0) красный", robot.rgb_led, 0, 0)
time.sleep(0.3)
test_method("rgb_led(0, 1) зелёный", robot.rgb_led, 0, 1)
time.sleep(0.3)
test_method("rgb_led(0, 2) синий", robot.rgb_led, 0, 2)
time.sleep(0.3)
test_method("rgb_led(0, 7) выкл", robot.rgb_led, 0, 7)

# ========== 5. БИПЕР ==========
print("\n🔊 5. БИПЕР")
test_method("beep(True)", robot.beep, True)
time.sleep(0.2)
test_method("beep(False)", robot.beep, False)
test_method("beep_short(1)", robot.beep_short, 1)
time.sleep(0.3)
test_method("beep_short(3)", robot.beep_short, 3)

# ========== 6. УЛЬТРАЗВУК ==========
print("\n📏 6. УЛЬТРАЗВУК")
dist = robot.get_distance()
print(f"  ▶️ get_distance()... {dist:.1f} см" if dist > 0 else "  ▶️ get_distance()... ❌ ошибка")

# ========== 7. OLED ==========
print("\n🖥️ 7. OLED")
test_method("oled_clear()", robot.oled_clear)
test_method("oled_show_text('Тест', 'Строка 2', 'Строка 3', 'Строка 4')", 
            robot.oled_show_text, "Тест", "Строка 2", "Строка 3", "Строка 4")
# oled_show_image требует файл, пропускаем если нет
if os.path.exists("/home/pi/logo.bmp"):
    test_method("oled_show_image('/home/pi/logo.bmp')", robot.oled_show_image, "/home/pi/logo.bmp")
else:
    print("  ⏭️ oled_show_image пропущен (нет файла logo.bmp)")

# ========== 8. ВИДЕО ==========
print("\n📸 8. ВИДЕО")
frame = robot.capture_frame()
print(f"  ▶️ capture_frame()... {'✅ кадр получен' if frame is not None else '❌ ошибка'}")
test_method("save_photo('/home/pi/test_photo.jpg')", robot.save_photo, "/home/pi/test_photo.jpg")
# start_stream и stop_stream не тестируем (запускают сервер)

# ========== 9. ГОЛОС ==========
print("\n🗣️ 9. ГОЛОС")
test_method("say('Привет!')", robot.say, "Привет!")

# ========== 10. РАСПОЗНАВАНИЕ РЕЧИ (требует микрофона) ==========
print("\n🎤 10. РАСПОЗНАВАНИЕ РЕЧИ (пропускаем, требует микрофона)")
# test_method("listen(2)", robot.listen, 2)  # раскомментировать при наличии микрофона

# ========== 11. AI: ЛИЦА ==========
print("\n🧑 11. AI: ЛИЦА")
result = robot.detect_faces()
print(f"  ▶️ detect_faces()... найдено лиц: {result['count']}")
if result['photo_path']:
    print(f"      Фото: {result['photo_path']}")

# ========== 12. AI: YOLO ==========
print("\n🎯 12. AI: YOLO (объекты)")
objects = robot.detect_objects_yolo()
print(f"  ▶️ detect_objects_yolo()... найдено объектов: {len(objects)}")
if objects:
    print(f"      {', '.join([obj['name'] for obj in objects[:5]])}")

# ========== 13. AI: QR ==========
print("\n📋 13. AI: QR")
qr_data = robot.detect_qr()
print(f"  ▶️ detect_qr()... {'✅ данные: ' + qr_data if qr_data else '❌ не найден'}")

# ========== 14. AI: ЦВЕТ ==========
print("\n🎨 14. AI: ЦВЕТ")
color = robot.detect_color()
print(f"  ▶️ detect_color()... {color}")

# ========== 15. Wi-Fi ==========
print("\n📶 15. Wi-Fi (пропускаем, требует сети)")
# test_method("switch_wifi('test', 'test')", robot.switch_wifi, "test", "test")

# ========== 16. ОПИСАНИЕ СЦЕНЫ ==========
print("\n🧠 16. ОПИСАНИЕ СЦЕНЫ (пропускаем, требует API-ключ)")
# desc = robot.describe_scene()
# print(f"  ▶️ describe_scene()... {desc[:100]}...")

# ========== 17. СИСТЕМНАЯ ИНФОРМАЦИЯ ==========
print("\n💻 17. СИСТЕМНАЯ ИНФОРМАЦИЯ")
print(f"  ▶️ get_ip()... {robot.get_ip()}")
print(f"  ▶️ get_cpu()... {robot.get_cpu()}")
print(f"  ▶️ get_ram()... {robot.get_ram()}")
print(f"  ▶️ get_disk()... {robot.get_disk()}")
print(f"  ▶️ get_temperature()... {robot.get_temperature()}")
print(f"  ▶️ get_battery()... {robot.get_battery()}%")

# ========== 18. РЕГИСТРАЦИЯ ЛИЦА ==========
print("\n🆕 18. РЕГИСТРАЦИЯ ЛИЦА (пропускаем, требует фото)")
# if os.path.exists("/home/pi/face.jpg"):
#     test_method("register_face('/home/pi/face.jpg')", robot.register_face, "/home/pi/face.jpg")

# ========== 19. ВОССТАНОВЛЕНИЕ ==========
print("\n🔄 19. ВОССТАНОВЛЕНИЕ")
test_method("restore()", robot.restore)

print("\n" + "="*60)
print("✅ ТЕСТ ЗАВЕРШЁН")
print("="*60)