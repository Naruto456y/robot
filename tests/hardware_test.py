from Raspbot_Lib import Raspbot
import time

bot = Raspbot()
print("🚀 Запуск полного теста робота...")

# --- 1. Тест камеры (PTZ) ---
print("📷 Тест поворота камеры...")
try:
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 55)
    time.sleep(1)
    print("  Вправо")
    bot.Ctrl_Servo(1, 150)
    time.sleep(1)
    print("  Влево")
    bot.Ctrl_Servo(1, 30)
    time.sleep(1)
    print("  Вверх")
    bot.Ctrl_Servo(2, 80)
    time.sleep(1)
    print("  Вниз")
    bot.Ctrl_Servo(2, 20)
    time.sleep(1)
    bot.Ctrl_Servo(1, 90)
    bot.Ctrl_Servo(2, 55)
    time.sleep(1)
    print("✅ Камера: OK")
except Exception as e:
    print(f"⚠️ Ошибка камеры: {e}")

# --- 2. Тест RGB-ленты (перебор разных вариантов) ---
print("💡 Тест RGB-ленты...")
rgb_ok = False
# Вариант A: Ctrl_WQ2812_ALL с двумя аргументами (яркость и цвет?)
try:
    print("  Вариант A: Ctrl_WQ2812_ALL(100, 0)")
    bot.Ctrl_WQ2812_ALL(100, 0)
    time.sleep(1)
    bot.Ctrl_WQ2812_ALL(0, 0)
    rgb_ok = True
except:
    pass

# Вариант B: Ctrl_WQ2812_ALL с одним аргументом (номер цвета)
if not rgb_ok:
    try:
        print("  Вариант B: Ctrl_WQ2812_ALL(1)")
        bot.Ctrl_WQ2812_ALL(1)
        time.sleep(1)
        bot.Ctrl_WQ2812_ALL(0)
        rgb_ok = True
    except:
        pass

# Вариант C: Ctrl_WQ2812_ALL с тремя аргументами (R,G,B)
if not rgb_ok:
    try:
        print("  Вариант C: Ctrl_WQ2812_ALL(255,0,0)")
        bot.Ctrl_WQ2812_ALL(255, 0, 0)
        time.sleep(1)
        bot.Ctrl_WQ2812_ALL(0, 0, 0)
        rgb_ok = True
    except:
        pass

# Вариант D: Ctrl_WQ2812_ALL с четырьмя аргументами (индекс, R,G,B) - для всей ленты может быть индекс=0
if not rgb_ok:
    try:
        print("  Вариант D: Ctrl_WQ2812_ALL(0, 255, 0, 0)")
        bot.Ctrl_WQ2812_ALL(0, 255, 0, 0)
        time.sleep(1)
        bot.Ctrl_WQ2812_ALL(0, 0, 0, 0)
        rgb_ok = True
    except:
        pass

if rgb_ok:
    print("✅ RGB-лента: OK")
else:
    print("⚠️ RGB-лента: ни один вариант не сработал. Попробуй Ctrl_WQ2812_Alone или ручные команды.")

# --- 3. Тест зуммера ---
print("🔊 Тест зуммера...")
try:
    bot.Ctrl_BEEP_Switch(1)
    time.sleep(0.5)
    bot.Ctrl_BEEP_Switch(0)
    time.sleep(0.5)
    print("✅ Зуммер: OK")
except Exception as e:
    print(f"⚠️ Ошибка зуммера: {e}")

# --- 4. Тест моторов (на холостом ходу) ---
print("🛞 Тест моторов (поднимите робота!)")
time.sleep(2)
try:
    print("  Вперёд")
    bot.Ctrl_Car(0x01, 100, 100)
    time.sleep(1)
    bot.Ctrl_Car(0x00, 0, 0)
    time.sleep(0.5)
    
    print("  Назад")
    bot.Ctrl_Car(0x02, 100, 100)
    time.sleep(1)
    bot.Ctrl_Car(0x00, 0, 0)
    time.sleep(0.5)
    
    print("  Влево")
    bot.Ctrl_Car(0x03, 100, 100)
    time.sleep(1)
    bot.Ctrl_Car(0x00, 0, 0)
    time.sleep(0.5)
    
    print("  Вправо")
    bot.Ctrl_Car(0x04, 100, 100)
    time.sleep(1)
    bot.Ctrl_Car(0x00, 0, 0)
    time.sleep(0.5)
    
    print("✅ Моторы: OK")
except Exception as e:
    print(f"⚠️ Ошибка моторов: {e}")

# --- 5. Финальное выключение ---
print("🔌 Завершение теста...")
try:
    bot.Ctrl_WQ2812_ALL(0, 0, 0)
except:
    pass
try:
    bot.Ctrl_Car(0x00, 0, 0)
except:
    pass
del bot
print("✅ Тест завершён.")
