#!/bin/bash
# Восстанавливает OLED и камеру — только один раз

# Проверяем, не запущен ли уже процесс восстановления
if [ -f /tmp/restore.lock ]; then
    exit 0
fi

# Создаём блокировку
touch /tmp/restore.lock

# Убиваем все процессы, которые могут занимать OLED
pkill -f "yahboom_oled.py" 2>/dev/null
pkill -f "oled_system.py" 2>/dev/null
pkill -f "ultrasonic_oled.py" 2>/dev/null
pkill -f "face_scan" 2>/dev/null

# Запускаем стандартный OLED (если есть)
if [ -f "/home/pi/software/oled_yahboom/yahboom_oled.py" ]; then
    python3 /home/pi/software/oled_yahboom/yahboom_oled.py &
elif [ -f "/home/pi/examples/oled/oled_system.py" ]; then
    python3 /home/pi/examples/oled/oled_system.py &
fi

# Ставим камеру в центр
python3 -c "from Raspbot_Lib import Raspbot; bot=Raspbot(); bot.Ctrl_Servo(1, 95); bot.Ctrl_Servo(2, 25); bot.Ctrl_WQ2812_ALL(0, 0)" 2>/dev/null

# echo "🔄 OLED и камера восстановлены"

# Удаляем блокировку через 2 секунды
(sleep 2 && rm -f /tmp/restore.lock) &