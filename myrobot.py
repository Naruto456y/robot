#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 Модуль для управления Yahboom Raspbot V2
====================================================================
Этот модуль предоставляет универсальный интерфейс для управления
всеми компонентами робота: двигатели, камера, RGB, звук, OLED,
ультразвук, видео, AI-функции (распознавание лиц, объектов, QR, цвет),
голосовое управление, синтез речи, системная информация, переключение Wi-Fi,
описание сцены через мультимодальные AI-модели (OpenRouter / Qwen).

Все методы имеют подробные описания на русском языке с указанием
параметров, возвращаемых значений и примеров использования.

Автоматически управляет состоянием робота: при инициализации отключает
стандартный OLED, ставит камеру в центр и останавливает моторы.
При завершении работы (даже при Ctrl+C) восстанавливает всё в исходное состояние.

Версия: 2.2 (исправлена камера, QR, порядок инициализации, stop, RGB)
"""

import os
import sys
import time
import math
import socket
import subprocess
import threading
import signal
import atexit
import cv2
import numpy as np
import edge_tts
import asyncio
import tempfile

# ====================================================================
# Базовые импорты для железа и OLED
# ====================================================================
from Raspbot_Lib import Raspbot, LightShow

# OLED – используем luma.oled, так как Adafruit_SSD1306 несовместим с Pi 5
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# ====================================================================
# Вспомогательные функции (скрытые)
# ====================================================================

def _get_ip() -> str:
    """Возвращает текущий IP-адрес робота в локальной сети."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

def _get_cpu_temp() -> str:
    """Возвращает температуру процессора в виде строки."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return f"{int(f.read())/1000:.1f}°C"
    except:
        return "N/A"

def _get_battery() -> int:
    """Возвращает приблизительный уровень заряда батареи (0–100%)."""
    try:
        val = int(subprocess.check_output(
            ["sudo", "i2cget", "-y", "1", "0x2B", "0x10"],
            text=True
        ).strip(), 16)
        return int(val * 100 / 256)
    except:
        return 0

# ====================================================================
# ОСНОВНОЙ КЛАСС
# ====================================================================

class Robot:
    """
    🦾 Главный класс управления роботом.

    При создании объекта автоматически:
        - Отключает стандартный OLED-скрипт Yahboom.
        - Ставит камеру в центр (горизонталь 95°, вертикаль 25°).
        - Останавливает все моторы.
        - Регистрирует обработчики для автоматического восстановления
          при завершении программы (включая Ctrl+C и закрытие терминала).

    Рекомендуется использовать внутри контекстного менеджера `with Robot() as r:`.
    """

    def __init__(self, center_h: int = 95, center_v: int = 25):
        """
        Инициализация робота.

        :param center_h: угол горизонтали для центра камеры (0–180°), по умолчанию 95°
        :param center_v: угол вертикали для центра камеры (0–90°), по умолчанию 25°
        """
        self.bot = Raspbot()
        self.center_h = center_h
        self.center_v = center_v
        self.camera_pos_h = center_h          
        self.camera_pos_v = center_v
        self._restored = False
        self._video_process = None
        self._flask_thread = None
        self._oled_killed = False             
        self._kill_oled()                 

        # Отключаем стандартный OLED-скрипт (если запущен)
        # os.system("sudo pkill -f yahboom_oled.py")
        # os.system("sudo pkill -f oled_system.py")

        # Ставим камеру в центр
        self.camera_center()

        # Останавливаем моторы
        self.stop()

        # Регистрируем восстановление при любом завершении
        atexit.register(self.restore)
        signal.signal(signal.SIGINT, lambda s, f: (self.restore(), sys.exit(0)))
        signal.signal(signal.SIGTERM, lambda s, f: (self.restore(), sys.exit(0)))

        # Инициализируем OLED (для вывода текста и изображений)
        self._oled_init()

        # print("✅ Робот инициализирован, OLED отключён, камера в центре, моторы остановлены")

    # ====================================================================
    # ВОССТАНОВЛЕНИЕ
    # ====================================================================

    def restore(self) -> None:
        """
        🔄 Восстанавливает стандартное состояние робота:
            - Останавливает все моторы.
            - Убивает свои процессы.
            - Запускает стандартный OLED-скрипт (если существует).
            - Ставит камеру в центр.

        Вызывается автоматически при завершении программы.
        """
        if self._restored:
            return
        self._restored = True
        # print("🔄 Восстановление...")

        self.stop()
        os.system("pkill -f myrobot.py 2>/dev/null")
        os.system("pkill -f stream_works.py 2>/dev/null")

        if os.path.exists("/home/pi/software/oled_yahboom/yahboom_oled.py"):
            os.system("python3 /home/pi/software/oled_yahboom/yahboom_oled.py &")

        self.camera_center()
        self.rgb_off()
        # print("✅ Восстановлено (моторы остановлены)")

    # ====================================================================
    # OLED (дисплей)
    # ====================================================================

    def _oled_init(self) -> None:
        """Инициализирует OLED-дисплей (128×64) через luma.oled."""
        try:
            self._oled_serial = i2c(port=1, address=0x3C)
            # На роботе стоит OLED 128x32 (так его инициализирует и стандартный скрипт Yahboom)
            self._oled_device = ssd1306(self._oled_serial, width=128, height=32, rotate=0)
            # Пытаемся загрузить шрифт с поддержкой кириллицы
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
            for p in font_paths:
                if os.path.exists(p):
                    self._oled_font = ImageFont.truetype(p, 8)
                    break
            else:
                self._oled_font = ImageFont.load_default()
        except Exception as e:
            print(f"⚠️ Ошибка инициализации OLED: {e}")
            self._oled_device = None
            self._oled_font = ImageFont.load_default()

    def _kill_oled(self):
        """Убивает стандартный OLED-скрипт (если ещё не убит)."""
        if not self._oled_killed:
            os.system("sudo pkill -f yahboom_oled.py")
            os.system("sudo pkill -f oled_system.py")
            self._oled_killed = True

    def oled_show_text(self, line1: str = "", line2: str = "", line3: str = "", line4: str = "") -> None:
        """
        🖥️ Выводит до 4 строк текста на OLED (128×32, строки по 8 пикселей).

        :param line1: первая строка
        :param line2: вторая строка
        :param line3: третья строка
        :param line4: четвёртая строка

        Пример:
            r.oled_show_text("IP: 192.168.1.56", "CPU: 12%", "RAM: 45%", "Robot OK")
        """
        if self._oled_device is None:
            print("❌ OLED не инициализирован")
            return
        with canvas(self._oled_device) as draw:
            draw.rectangle((0, 0, 127, 31), outline="black", fill="black")
            y = 0
            line_height = 8
            for text in [line1, line2, line3, line4]:
                if text:
                    draw.text((0, y), text, font=self._oled_font, fill="white")
                y += line_height

    def oled_clear(self) -> None:
        """🧹 Очищает OLED-дисплей."""
        self.oled_show_text()

    def oled_show_image(self, image_path: str) -> None:
        """
        🖼️ Выводит изображение на OLED (автоматически подгоняет под размер).

        :param image_path: путь к файлу (BMP, PNG, JPG). Изображение должно быть чёрно-белым или будет преобразовано.

        Пример:
            r.oled_show_image("/home/pi/logo.bmp")
        """
        if self._oled_device is None:
            print("❌ OLED не инициализирован")
            return
        img = Image.open(image_path).convert("1")
        img = img.resize((self._oled_device.width, self._oled_device.height))
        self._oled_device.display(img)

    # ====================================================================
    # МОТОРЫ (меканум-колёса)
    # ====================================================================

    def _set_deflection(self, speed: int, deflection: int) -> tuple:
        """Внутренняя функция для расчёта скоростей колёс."""
        if speed > 255:
            speed = 255
        if speed < 0:
            speed = 0
        rad = math.pi / 180
        vx = speed * math.cos(deflection * rad)
        vy = speed * math.sin(deflection * rad)
        l1 = int(vy + vx)
        l2 = int(vy - vx)
        r1 = int(vy - vx)
        r2 = int(vy + vx)
        return l1, l2, r1, r2

    def _move(self, deflection: int, speed: int = 150) -> None:
        """Внутренняя функция для движения в заданном направлении."""
        l1, l2, r1, r2 = self._set_deflection(speed, deflection)
        self.bot.Ctrl_Muto(0, l1)
        self.bot.Ctrl_Muto(1, l2)
        self.bot.Ctrl_Muto(2, r1)
        self.bot.Ctrl_Muto(3, r2)

    def forward(self, speed: int = 150) -> None:
        """
        🏎️ Движение вперёд.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(90, speed)

    def backward(self, speed: int = 150) -> None:
        """
        🔙 Движение назад.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(270, speed)

    def left(self, speed: int = 150) -> None:
        """
        ⬅️ Движение влево (поперечное смещение).

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(180, speed)

    def right(self, speed: int = 150) -> None:
        """
        ➡️ Движение вправо.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(0, speed)

    def stop(self) -> None:
        """
        ⏹️ Останавливает все моторы (повторяет 3 раза для надёжности).
        """
        for _ in range(3):
            self.bot.Ctrl_Car(0, 0, 0)   # <-- ИСПРАВЛЕНО: останавливает первый мотор
            self.bot.Ctrl_Car(1, 0, 0)   # второй
            self.bot.Ctrl_Car(2, 0, 0)   # третий
            self.bot.Ctrl_Car(3, 0, 0)   # четвёртый
            time.sleep(0.05)

    def rotate_left(self, speed: int = 150) -> None:
        """
        🔄 Поворот на месте влево (разворот).

        :param speed: скорость (0–255), по умолчанию 150
        """
        l1, l2, r1, r2 = self._set_deflection(speed, 180)
        self.bot.Ctrl_Muto(0, l1)
        self.bot.Ctrl_Muto(1, -l2)
        self.bot.Ctrl_Muto(2, r1)
        self.bot.Ctrl_Muto(3, abs(r2))

    def rotate_right(self, speed: int = 150) -> None:
        """
        🔄 Поворот на месте вправо (разворот).

        :param speed: скорость (0–255), по умолчанию 150
        """
        l1, l2, r1, r2 = self._set_deflection(speed, 0)
        self.bot.Ctrl_Muto(0, l1)
        self.bot.Ctrl_Muto(1, abs(l2))
        self.bot.Ctrl_Muto(2, r1)
        self.bot.Ctrl_Muto(3, -r2)

    def diagonal_left_forward(self, speed: int = 150) -> None:
        """
        ↗️ Движение по диагонали влево-вперёд.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(135, speed)

    def diagonal_right_forward(self, speed: int = 150) -> None:
        """
        ↗️ Движение по диагонали вправо-вперёд.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(45, speed)

    def diagonal_left_backward(self, speed: int = 150) -> None:
        """
        ↙️ Движение по диагонали влево-назад.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(225, speed)

    def diagonal_right_backward(self, speed: int = 150) -> None:
        """
        ↙️ Движение по диагонали вправо-назад.

        :param speed: скорость (0–255), по умолчанию 150
        """
        self._move(315, speed)

    # ====================================================================
    # КАМЕРА (сервоприводы) — ИСПРАВЛЕНО
    # ====================================================================

    def camera_center(self) -> None:
        """
        📷 Устанавливает камеру в центр (горизонталь и вертикаль по заданным углам).
        """
        self.camera_pos_h = self.center_h
        self.camera_pos_v = self.center_v
        self.bot.Ctrl_Servo(1, self.center_h)
        self.bot.Ctrl_Servo(2, self.center_v)

    def camera_left(self) -> None:
        """
        👈 Поворачивает камеру влево на 15° от текущего положения.
        """
        self.camera_pos_h = min(180, self.camera_pos_h + 15)
        self.bot.Ctrl_Servo(1, self.camera_pos_h)

    def camera_right(self) -> None:
        """
        👉 Поворачивает камеру вправо на 15° от текущего положения.
        """
        self.camera_pos_h = max(0, self.camera_pos_h - 15)
        self.bot.Ctrl_Servo(1, self.camera_pos_h)

    def camera_up(self) -> None:
        """
        👆 Поднимает камеру вверх на 10° от текущего положения.
        """
        self.camera_pos_v = min(90, self.camera_pos_v + 10)
        self.bot.Ctrl_Servo(2, self.camera_pos_v)

    def camera_down(self) -> None:
        """
        👇 Опускает камеру вниз на 10° от текущего положения.
        """
        self.camera_pos_v = max(0, self.camera_pos_v - 10)
        self.bot.Ctrl_Servo(2, self.camera_pos_v)

    def camera_set(self, axis: int, angle: int) -> None:
        """
        🎛️ Устанавливает угол сервопривода.

        :param axis: 1 – горизонталь, 2 – вертикаль
        :param angle: угол (0–180 для горизонтали, 0–90 для вертикали)

        Пример:
            r.camera_set(1, 45)  # горизонталь влево
        """
        if axis == 1:
            self.camera_pos_h = max(0, min(180, angle))
            self.bot.Ctrl_Servo(1, self.camera_pos_h)
        elif axis == 2:
            self.camera_pos_v = max(0, min(90, angle))
            self.bot.Ctrl_Servo(2, self.camera_pos_v)

    # ====================================================================
    # RGB-ЛЕНТА
    # ====================================================================

    def _init_lights(self):
        if not hasattr(self, '_lights'):
            self._lights = LightShow()
            self._light_show_active = False
            self._light_thread = None

    def rgb_effect(self, effect_name: str, duration=None, speed: float = 0.1, option: int = -1) -> None:
        """
        🌈 Запускает световой RGB-эффект в фоновом режиме.
        """
        self._init_lights()
        if self._light_show_active:
            self._lights.stop()
            if self._light_thread and self._light_thread.is_alive():
                self._light_thread.join(timeout=0.5)
            self._light_show_active = False

        if duration is None:
            duration = self._lights.MAX_TIME

        self._light_show_active = True

        def run_effect():
            try:
                self._lights.execute_effect(effect_name, duration, speed, option)
            except Exception as e:
                print(f"❌ Ошибка эффекта {effect_name}: {e}")
            finally:
                self._light_show_active = False
                self._lights.turn_off_all_lights()

        self._light_thread = threading.Thread(target=run_effect, daemon=True)
        self._light_thread.start()
        print(f"✨ Эффект {effect_name} запущен (speed={speed})")

    # Простые обёртки для популярных эффектов (оставь, они удобны)
    def rgb_effect_starlight(self, speed: float = 0.1, duration=None):
        self.rgb_effect('starlight', duration=duration, speed=speed, option=-1)

    def rgb_effect_river(self, speed: float = 0.01, duration=None):
        self.rgb_effect('river', duration=duration, speed=speed, option=-1)

    def rgb_effect_random_running(self, speed: float = 0.1, duration=None):
        self.rgb_effect('random_running', duration=duration, speed=speed, option=-1)

    def rgb_effect_gradient(self, speed: float = 0.03, duration=None):
        self.rgb_effect('gradient', duration=duration, speed=speed, option=-1)

    def rgb_effect_breathing(self, speed: float = 0.01, duration=None):
        self.rgb_effect('breathing', duration=duration, speed=speed, option=0)

    def rgb_off(self) -> None:
        """
        💡 Полностью выключает RGB-ленту.
        - Если запущен световой эффект, останавливает его.
        - Выключает все светодиоды (аппаратно).
        - Сбрасывает состояние ручного управления (rgb_color).
        """
        # 1. Остановка эффекта, если активен
        if hasattr(self, '_lights') and self._light_show_active:
            self._lights.stop()                     # прервать execute_effect
            self._light_show_active = False
            if self._light_thread and self._light_thread.is_alive():
                self._light_thread.join(timeout=0.5)
            print("🛑 Эффект остановлен")

        # 2. Аппаратное выключение всех светодиодов
        self.bot.Ctrl_WQ2812_ALL(0, 0)

        # Дополнительно на всякий случай, если есть отдельный метод turn_off_all_lights:
        if hasattr(self, '_lights'):
            try:
                self._lights.turn_off_all_lights()
            except:
                pass

    # rgb_color теперь не мешает эффектам (просто вызовет rgb_off сначала)
    def rgb_color(self, color: int) -> None:
        """
        🎨 Включает RGB-ленту заданным цветом.
        Перед этим выключает любой активный эффект.
        """
        self.rgb_off()   # сначала всё выключим
        if 0 <= color <= 6:
            self.bot.Ctrl_WQ2812_ALL(1, color)
        else:
            self.bot.Ctrl_WQ2812_ALL(0, 0)

    # rgb_led теперь тоже безопасен (выключает эффект)
    def rgb_led(self, index: int, color: int) -> None:
        """
        💡 Управляет отдельным светодиодом.
        Перед этим выключает любой активный эффект.
        """
        # self.rgb_off()
        if 0 <= color <= 6:
            self.bot.Ctrl_WQ2812_Alone(index, True, color)
        else:
            self.bot.Ctrl_WQ2812_Alone(index, False, 0)

    # ====================================================================
    # БИПЕР
    # ====================================================================

    def beep(self, on: bool = True) -> None:
        """
        🔊 Включает или выключает звуковой сигнал (зуммер).

        :param on: True – включить, False – выключить
        """
        self.bot.Ctrl_BEEP_Switch(1 if on else 0)

    def beep_short(self, times: int = 1) -> None:
        """
        🔊 Издаёт короткие звуковые сигналы.

        :param times: количество сигналов (по умолчанию 1)

        Пример:
            r.beep_short(3)  # три коротких писка
        """
        for _ in range(times):
            self.beep(True)
            time.sleep(0.2)
            self.beep(False)
            time.sleep(0.1)

    # ====================================================================
    # УЛЬТРАЗВУК
    # ====================================================================

    def get_distance(self) -> float:
        """
        📏 Измеряет расстояние с помощью ультразвукового датчика (HC-SR04).

        :return: расстояние в сантиметрах или -1 при ошибке

        Пример:
            dist = r.get_distance()
            if dist > 0:
                print(f"Расстояние: {dist:.1f} см")
        """
        try:
            self.bot.Ctrl_Ulatist_Switch(1)
            time.sleep(0.05)
            diss_H = self.bot.read_data_array(0x1b, 1)[0]
            diss_L = self.bot.read_data_array(0x1a, 1)[0]
            dis_mm = (diss_H << 8) | diss_L
            if dis_mm == 0:
                return -1.0
            return dis_mm / 10.0
        except Exception:
            return -1.0

    # ====================================================================
    # КНОПКА KEY
    # ====================================================================

    def is_key_pressed(self) -> bool:
        """
        🔘 Проверяет, нажата ли кнопка KEY на драйвере.

        :return: True, если кнопка нажата, иначе False
        """
        try:
            val = self.bot.read_data_array(0x0D, 1)[0]
            return val == 0x01
        except Exception:
            return False

    # ====================================================================
    # ВИДЕО (захват, фото, трансляция)
    # ====================================================================

    def capture_frame(self) -> np.ndarray:
        """
        📸 Захватывает текущий кадр с камеры.

        :return: кадр (numpy array) или None, если не удалось

        Пример:
            frame = r.capture_frame()
            if frame is not None:
                cv2.imwrite("photo.jpg", frame)
        """
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None

    def save_photo(self, filename: str = "/home/pi/photo.jpg") -> bool:
        """
        📸 Сохраняет фото с камеры в файл.

        :param filename: путь для сохранения (по умолчанию /home/pi/photo.jpg)
        :return: True, если сохранено успешно, иначе False
        """
        frame = self.capture_frame()
        if frame is not None:
            cv2.imwrite(filename, frame)
            return True
        return False

    def start_stream(self, port: int = 5000, resolution: tuple = (320, 240),
                     fps: int = 30, method: str = "flask") -> None:
        """
        📡 Запускает видеотрансляцию.

        :param port: порт для веб-сервера (по умолчанию 5000)
        :param resolution: кортеж (ширина, высота), по умолчанию (320, 240)
        :param fps: кадров в секунду (реально до 30)
        :param method: "flask" (простой) или "mjpg" (быстрее, требует установки mjpg_streamer)

        Пример:
            r.start_stream(port=8080, resolution=(640, 480), method='flask')
        """
        if method == "flask":
            self._start_flask_stream(port, resolution, fps)
        elif method == "mjpg":
            self._start_mjpg_streamer(port, resolution, fps)
        else:
            raise ValueError("method must be 'flask' or 'mjpg'")

    def _start_flask_stream(self, port, resolution, fps):
        from flask import Flask, Response
        app = Flask(__name__)

        def gen():
            cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            cap.set(cv2.CAP_PROP_FPS, fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue
                ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ret:
                    continue
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       jpeg.tobytes() + b'\r\n')
            cap.release()

        @app.route('/video')
        def video_feed():
            return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

        def run():
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

        self._flask_thread = threading.Thread(target=run)
        self._flask_thread.daemon = True
        self._flask_thread.start()
        print(f"📡 Flask-стрим запущен на http://192.168.1.56:{port}/video")

    def _start_mjpg_streamer(self, port, resolution, fps):
        cmd = [
            "/usr/local/bin/mjpg_streamer",
            "-i", f"input_uvc.so -d /dev/video0 -r {resolution[0]}x{resolution[1]} -f {fps} -n",
            "-o", f"output_http.so -p {port} -w /usr/local/share/mjpg-streamer/www"
        ]
        self._video_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        print(f"📡 mjpg_streamer запущен на http://192.168.1.56:{port}/?action=stream")

    def stop_stream(self) -> None:
        """
        🛑 Останавливает видеотрансляцию.
        """
        if self._video_process:
            self._video_process.terminate()
            self._video_process = None
        if self._flask_thread:
            os.system("pkill -f stream_fast.py")
            self._flask_thread = None
        print("📡 Трансляция остановлена")

    # ====================================================================
    # ГОЛОС (синтез речи)
    # ====================================================================

    def say(self, text: str, voice: str = "ru-RU-DmitryNeural", rate: str = "+0%", volume: str = "+0%") -> None:
        """
        🗣️ Синтез речи через Microsoft Edge TTS (бесплатно, без API-ключей).

        :param text:   текст для озвучивания (поддерживается кириллица)
        :param voice:  голос (по умолчанию ru-RU-DmitryNeural — мужской русский)
        :param rate:   скорость речи, например "+10%", "-20%"
        :param volume: громкость, например "+10%", "-20%"

        Доступные русские голоса:
            - ru-RU-DmitryNeural  (мужской)
            - ru-RU-SvetlanaNeural (женский)

        Пример:
            r.say("Привет, я робот!")
            r.say("Медленная речь", rate="-30%")
            r.say("Громче!", volume="+20%")
        """
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                output_file = tmp.name

            async def generate():
                communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
                await communicate.save(output_file)

            asyncio.run(generate())

            if os.system("which mpg123 > /dev/null 2>&1") == 0:
                os.system(f'mpg123 -q "{output_file}"')
            else:
                os.system(f'aplay "{output_file}" 2>/dev/null')

            os.unlink(output_file)

        except Exception as e:
            print(f"❌ Ошибка TTS: {e}")
            # Fallback на espeak
            os.system(f'espeak -v ru "{text}" 2>/dev/null')

    # ====================================================================
    # ДИНАМИК (воспроизведение MP3)
    # ====================================================================

    def play_mp3(self, filepath: str, volume: int = 50000) -> None:
        """
        🎵 Воспроизводит MP3-файл через mpg123 с усилением.

        :param filepath: путь к MP3-файлу
        :param volume: множитель громкости (по умолчанию 50000, даёт громкий звук)

        Пример:
            r.play_mp3("/home/pi/music.mp3")
        """
        os.system(f'mpg123 -f {volume} "{filepath}" &')

    def stop_audio(self) -> None:
        """
        ⏹️ Немедленно останавливает любое текущее воспроизведение (TTS, MP3, системные звуки).
        После этого можно сразу запустить новый звук.
        """
        os.system("pkill -f mpg123 2>/dev/null")
        os.system("pkill -f aplay 2>/dev/null")
        os.system("pkill -f espeak 2>/dev/null")
        # Если используешь mplayer, добавь:
        # os.system("pkill -f mplayer 2>/dev/null")
    
    # ====================================================================
    # МИКРОФОН (запись аудио)
    # ====================================================================

    def _clean_audio(self, src: str, dst: str, strength: float = 0.35) -> bool:
        """
        Очистка записи: убирает постоянный шум (вентилятор), добавляет «студийный» тембр.

        Профиль шума берётся из самого тихого полусекундного куска записи.
        Нужны sox и ffmpeg. При любой ошибке dst не создаётся.

        :param src: исходный WAV
        :param dst: куда сохранить очищенный WAV
        :param strength: сила подавления шума sox noisered (0.2–0.6)
        """
        import wave
        tmp = tempfile.mkdtemp(prefix="_clean_")
        try:
            with wave.open(src) as w:
                rate = w.getframerate()
                data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
            win = rate // 2
            if len(data) < win * 2:
                return False
            # самый тихий кусок = только шум вентилятора
            best_s, best_e = 0, None
            for s in range(0, len(data) - win, win // 4):
                e = float(np.mean(data[s:s + win] ** 2))
                if best_e is None or e < best_e:
                    best_s, best_e = s, e
            noise = os.path.join(tmp, "noise.wav")
            prof = os.path.join(tmp, "noise.prof")
            dn = os.path.join(tmp, "dn.wav")
            subprocess.run(["sox", src, noise, "trim", f"{best_s / rate:.2f}", "0.5"], check=True)
            subprocess.run(["sox", noise, "-n", "noiseprof", prof], check=True)
            subprocess.run(["sox", src, dn, "noisered", prof, str(strength)], check=True)
            af = ("highpass=f=90,afftdn=nr=25:nf=-40:tn=1,"
                  "equalizer=f=200:t=q:w=1:g=3,equalizer=f=3500:t=q:w=1:g=3,"
                  "equalizer=f=8000:t=h:w=4000:g=2,"
                  "acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=4,"
                  "alimiter=limit=0.9,loudnorm=I=-16:TP=-1.5")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", dn, "-af", af,
                            "-ar", str(rate), dst], check=True)
            return os.path.exists(dst)
        except Exception as e:
            print(f"❌ Ошибка очистки звука: {e}")
            return False
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    def listen_audio(self, duration: int = 3, filename: str = "/home/pi/recording.wav",
                     clean: bool = False) -> bool:
        """
        🎤 Записывает аудио с микрофона в WAV-файл.

        :param duration: длительность записи в секундах
        :param filename: путь для сохранения (по умолчанию /home/pi/recording.wav)
        :param clean: True — убрать шум вентилятора и улучшить звук (нужны sox и ffmpeg;
                      в записи должна быть хотя бы пауза без речи ~0.5 с)
        :return: True, если запись успешна, иначе False

        Пример:
            if r.record_audio(5, "speech.wav"):
                print("Запись сохранена")
        """
        try:
            import pyaudio
            import wave
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                            input=True, frames_per_buffer=CHUNK)
            frames = []
            for _ in range(0, int(RATE / CHUNK * duration)):
                frames.append(stream.read(CHUNK, exception_on_overflow=False))
            stream.stop_stream(); stream.close(); p.terminate()
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS); wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE); wf.writeframes(b''.join(frames)); wf.close()
            if clean:
                cleaned = filename + ".clean.wav"
                if self._clean_audio(filename, cleaned):
                    os.replace(cleaned, filename)
                else:
                    print("⚠️ Очистка не удалась, сохранена исходная запись")
            return True
        except Exception as e:
            print(f"❌ Ошибка записи: {e}")
            return False

    def record_mic_mp3(self, duration: int = 5, filename: str = "/home/pi/mic_test.mp3",
               device: str = "plughw:2,0", clean: bool = False) -> bool:
        """
        🎤 Записывает звук с микрофона в MP3.

        :param duration: длительность записи в секундах
        :param filename: путь для сохранения MP3
        :param device: ALSA-устройство (по умолчанию USB-микрофон plughw:2,0)
        :param clean: True — убрать шум вентилятора и улучшить звук перед сохранением
        :return: True, если запись успешна
        """
        wav = "/tmp/_mic_record.wav"
        result = os.system(f'arecord -D {device} -d {duration} -f cd -t wav {wav}')
        if result == 0 and clean:
            cleaned = "/tmp/_mic_record_clean.wav"
            if self._clean_audio(wav, cleaned):
                os.replace(cleaned, wav)
            else:
                print("⚠️ Очистка не удалась, сохранена исходная запись")
        if result == 0:
            result = os.system(
                f'ffmpeg -y -loglevel error -i {wav} -codec:a libmp3lame -qscale:a 2 {filename}')
        if os.path.exists(wav):
            os.remove(wav)
        if result == 0 and os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ Записано: {filename} ({size} байт)")
            return True
        print("❌ Ошибка записи")
        return False

    # ====================================================================
    # РАСПОЗНАВАНИЕ РЕЧИ (Google Speech)
    # ====================================================================

    def listen(self, duration: int = 3, language: str = "ru-RU", device_index: int = 0) -> str:
        """
        🎤 Распознавание речи через Google Speech (бесплатно, требует интернета).

        :param duration: длительность прослушивания в секундах
        :param language: язык (по умолчанию русский "ru-RU")
        :param device_index: индекс микрофона (0 – USB Audio Device)
        :return: распознанный текст в нижнем регистре или пустая строка при ошибке

        Пример:
            text = r.listen(4)
            if text:
                print(f"Вы сказали: {text}")
        """
        import speech_recognition as sr
        stderr_orig = sys.stderr
        sys.stderr = open(os.devnull, 'w')

        try:
            recognizer = sr.Recognizer()
            with sr.Microphone(device_index=device_index) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                sys.stderr = stderr_orig
                print("🎤 Говорите...")
                sys.stderr = open(os.devnull, 'w')
                audio = recognizer.listen(source, timeout=duration + 1, phrase_time_limit=duration)
        except sr.WaitTimeoutError:
            sys.stderr = stderr_orig
            return ""
        except Exception as e:
            sys.stderr = stderr_orig
            print(f"❌ Ошибка микрофона: {e}")
            return ""
        finally:
            sys.stderr = stderr_orig

        try:
            text = recognizer.recognize_google(audio, language=language)
            return text.strip().lower()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("❌ Ошибка сети (интернет)")
            return ""

    # ====================================================================
    # AI: ОБНАРУЖЕНИЕ ЛИЦ (однократное и потоковое)
    # ====================================================================

    def detect_faces(self, save_dir: str = "/home/pi/faces/",
                     draw_boxes: bool = True, save_photo: bool = True,
                     confidence: float = 0.5) -> dict:
        """
        📷 Однократный захват кадра, обнаружение лиц, сохранение фото с рамками.

        :param save_dir: папка для сохранения фото (создаётся, если нет)
        :param draw_boxes: рисовать зелёные рамки вокруг лиц на фото
        :param save_photo: сохранять фото при обнаружении
        :param confidence: порог уверенности (0.0–1.0)
        :return: словарь с ключами:
            - 'faces': список координат лиц (x, y, w, h)
            - 'count': количество лиц
            - 'photo_path': путь к сохранённому фото или None
            - 'frame': кадр (numpy array) или None

        Пример:
            result = r.detect_faces()
            print(f"Найдено лиц: {result['count']}")
        """
        import mediapipe as mp
        os.makedirs(save_dir, exist_ok=True)

        mp_face = mp.solutions.face_detection
        face_detection = mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=confidence
        )

        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not cap.isOpened():
            print("❌ Камера не доступна")
            return {'faces': [], 'count': 0, 'photo_path': None, 'frame': None}

        ret, frame = cap.read()
        cap.release()

        if not ret:
            print("❌ Не удалось захватить кадр")
            return {'faces': [], 'count': 0, 'photo_path': None, 'frame': None}

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(rgb)

        faces = []
        if results.detections:
            h, w, _ = frame.shape
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                faces.append((x, y, width, height))
                if draw_boxes:
                    cv2.rectangle(frame, (x, y), (x+width, y+height), (0, 255, 0), 2)

        photo_path = None
        if save_photo and faces:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            photo_path = os.path.join(save_dir, f"faces_{timestamp}.jpg")
            cv2.imwrite(photo_path, frame)
            print(f"📸 Фото с {len(faces)} лицом(ами) сохранено: {photo_path}")

        return {
            'faces': faces,
            'count': len(faces),
            'photo_path': photo_path,
            'frame': frame
        }

    def detect_faces_stream(self,
                            save_photo: bool = True,
                            draw_boxes: bool = True,
                            rgb_on: bool = True,
                            beep_on: bool = True,
                            say_text: str = "Обнаружено лицо",
                            confidence: float = 0.5,
                            save_dir: str = "/home/pi/faces/",
                            detect_known: bool = False,
                            known_encoding=None,
                            known_name: str = "Известное лицо") -> None:
        """
        🎥 Потоковое распознавание лиц с камеры (бесконечный цикл).

        :param save_photo: сохранять фото при обнаружении
        :param draw_boxes: рисовать зелёные рамки на фото
        :param rgb_on: включать RGB (зелёный при обнаружении, красный в ожидании)
        :param beep_on: издавать звуковой сигнал при обнаружении
        :param say_text: текст для озвучивания (None – не говорить)
        :param confidence: порог уверенности (0.0–1.0)
        :param save_dir: папка для сохранения фото
        :param detect_known: True – сравнивать с эталоном, False – любое лицо
        :param known_encoding: энкодинг эталона (из face_recognition)
        :param known_name: имя для вывода, если detect_known=True

        Пример:
            r.detect_faces_stream(say_text="Привет!", rgb_on=True)
        """
        import mediapipe as mp
        import time
        from datetime import datetime
        os.makedirs(save_dir, exist_ok=True)

        mp_face = mp.solutions.face_detection
        face_detection = mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=confidence
        )

        if detect_known and known_encoding is None:
            print("⚠️ Для detect_known=True нужно передать known_encoding")
            return

        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not cap.isOpened():
            print("❌ Камера не доступна")
            return

        if rgb_on:
            self.rgb_color(0)  # красный – ожидание

        print(f"👀 Запуск детекции лиц (порог: {confidence})")
        print("   Нажмите Ctrl+C для остановки")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)

                if results.detections:
                    matched = False
                    if detect_known:
                        try:
                            import face_recognition
                            face_locations = face_recognition.face_locations(frame)
                            if face_locations:
                                encodings = face_recognition.face_encodings(frame, face_locations)
                                for enc in encodings:
                                    matches = face_recognition.compare_faces([known_encoding], enc, tolerance=0.5)
                                    if matches[0]:
                                        matched = True
                                        break
                        except ImportError:
                            print("⚠️ Установите face_recognition для detect_known=True")
                            detect_known = False
                            matched = True
                    else:
                        matched = True

                    if matched:
                        if draw_boxes:
                            h, w, _ = frame.shape
                            for detection in results.detections:
                                bbox = detection.location_data.relative_bounding_box
                                x = int(bbox.xmin * w)
                                y = int(bbox.ymin * h)
                                width = int(bbox.width * w)
                                height = int(bbox.height * h)
                                cv2.rectangle(frame, (x, y), (x+width, y+height), (0, 255, 0), 2)
                                if detect_known and known_name:
                                    cv2.putText(frame, known_name, (x, y-10),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

                        if save_photo:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = os.path.join(save_dir, f"face_{timestamp}.jpg")
                            cv2.imwrite(filename, frame)
                            print(f"📸 Фото сохранено: {filename}")

                        if rgb_on:
                            self.rgb_color(1)  # зелёный
                        if beep_on:
                            self.beep_short()
                        if say_text:
                            self.say(say_text)

                        time.sleep(2)  # пауза, чтобы не спамить
                    else:
                        if rgb_on:
                            self.rgb_color(0)
                        time.sleep(0.1)
                else:
                    if rgb_on:
                        self.rgb_color(0)
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n👋 Остановка пользователем")
        finally:
            cap.release()
            self.rgb_off()
            self.restore()

    # ====================================================================
    # AI: РЕГИСТРАЦИЯ ЛИЦА ИЗ ФАЙЛА
    # ====================================================================

    def register_face(self, image_path: str,
                      output_path: str = "/home/pi/known_face.pkl",
                      detect_multiple: bool = False) -> bool:
        """
        🆕 Регистрирует лицо с фотографии и сохраняет энкодинг в файл (для последующего сравнения).

        :param image_path: путь к файлу с изображением (JPG, PNG и др.)
        :param output_path: путь для сохранения энкодинга (по умолчанию /home/pi/known_face.pkl)
        :param detect_multiple: если True, регистрирует первое найденное лицо;
                                если False, сообщает об ошибке при нескольких лицах.
        :return: True, если лицо успешно зарегистрировано, иначе False

        Пример:
            if r.register_face("/home/pi/photo.jpg"):
                print("Лицо сохранено. Теперь можно использовать распознавание.")
        """
        try:
            import face_recognition
            import pickle
        except ImportError:
            print("❌ Установите face_recognition: pip install face_recognition")
            return False

        if not os.path.exists(image_path):
            print(f"❌ Файл {image_path} не найден")
            return False

        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Не удалось загрузить изображение: {image_path}")
            return False

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)

        if not boxes:
            print("❌ Лицо не найдено на изображении")
            return False

        if len(boxes) > 1 and not detect_multiple:
            print(f"❌ Найдено {len(boxes)} лиц. Используйте detect_multiple=True для регистрации первого лица")
            return False

        enc = face_recognition.face_encodings(rgb, boxes)[0]

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(enc, f)

        print(f"✅ Лицо зарегистрировано и сохранено в {output_path}")
        return True

    # ====================================================================
    # AI: YOLO, QR, ЦВЕТ (QR — ИСПРАВЛЕН НА pyzbar)
    # ====================================================================

    def detect_objects_yolo(self, image_path: str = None,
                            model_name: str = 'yolov8n.pt',
                            confidence: float = 0.3) -> list:
        """
        🎯 Детекция объектов на изображении с помощью YOLO.

        :param image_path: путь к изображению (если None, делает фото с камеры)
        :param model_name: имя модели YOLO (по умолчанию yolov8n.pt)
        :param confidence: минимальная уверенность для вывода
        :return: список словарей с полями {'name': str, 'confidence': float}

        Пример:
            objects = r.detect_objects_yolo()
            for obj in objects:
                print(f"{obj['name']} ({obj['confidence']:.2f})")
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            print("❌ Установите ultralytics: pip install ultralytics")
            return []

        if image_path is None:
            frame = self.capture_frame()
            if frame is None:
                return []
            temp_path = "/tmp/yolo_frame.jpg"
            cv2.imwrite(temp_path, frame)
            image_path = temp_path

        model = YOLO(model_name)
        results = model(image_path, verbose=False)
        objects = []
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if conf >= confidence:
                        objects.append({'name': model.names[cls], 'confidence': conf})
        return objects

    def detect_qr(self, frame=None) -> str:
        """
        📋 Распознаёт QR-код на кадре с помощью pyzbar (надёжнее, чем cv2).

        :param frame: кадр (numpy array). Если None, делает фото с камеры.
        :return: данные QR-кода (строка) или None

        Пример:
            data = r.detect_qr()
            if data:
                print(f"QR: {data}")
        """
        try:
            from pyzbar.pyzbar import decode
        except ImportError:
            print("⚠️ Установите pyzbar: sudo apt install libzbar0 -y && pip install pyzbar")
            # fallback на cv2
            if frame is None:
                frame = self.capture_frame()
                if frame is None:
                    return None
            detector = cv2.QRCodeDetector()
            data, bbox, _ = detector.detectAndDecode(frame)
            return data if data else None

        if frame is None:
            frame = self.capture_frame()
            if frame is None:
                return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decoded = decode(gray)
        if decoded:
            return decoded[0].data.decode('utf-8')
        return None

    def detect_color(self, frame=None) -> str:
        """
        🎨 Определяет доминирующий цвет в центре кадра.

        :param frame: кадр (numpy array). Если None, делает фото с камеры.
        :return: название цвета (строка) или "Неизвестно"

        Пример:
            color = r.detect_color()
            print(f"Цвет в центре: {color}")
        """
        if frame is None:
            frame = self.capture_frame()
            if frame is None:
                return "Неизвестно"
        h, w, _ = frame.shape
        center = frame[h//2-10:h//2+10, w//2-10:w//2+10]
        avg = np.mean(center, axis=(0,1))
        color_name = "Неизвестно"
        if avg[1] > 80 and avg[2] > 80:
            hsv = cv2.cvtColor(np.uint8([[avg]]), cv2.COLOR_BGR2HSV)[0][0]
            h_val = hsv[0]
            if h_val < 10: color_name = "Красный"
            elif h_val < 30: color_name = "Оранжевый"
            elif h_val < 60: color_name = "Жёлтый"
            elif h_val < 100: color_name = "Зелёный"
            elif h_val < 130: color_name = "Голубой"
            elif h_val < 170: color_name = "Синий"
            else: color_name = "Фиолетовый"
        return color_name

    # ====================================================================
    # Wi-Fi ПЕРЕКЛЮЧЕНИЕ
    # ====================================================================

    def switch_wifi(self, ssid: str, password: str) -> bool:
        """
        📶 Переключает Wi-Fi на указанную сеть (без лишних логов).

        :param ssid: имя сети
        :param password: пароль
        :return: True, если переключение успешно

        Пример:
            if r.switch_wifi("МояСеть", "пароль"):
                print("Подключено к VPN-роутеру")
        """
        try:
            subprocess.run(
                ["sudo", "nmcli", "device", "disconnect", "wlan0"],
                capture_output=True,
                check=False
            )
            time.sleep(1)
            result = subprocess.run(
                ["sudo", "nmcli", "device", "wifi", "connect", ssid, "password", password],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                time.sleep(2)
                return True
            else:
                print(f"❌ Ошибка подключения к {ssid}")
                return False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return False

    # ====================================================================
    # ОПИСАНИЕ СЦЕНЫ (OpenRouter / Qwen)
    # ====================================================================

    def _get_openrouter_key(self) -> str:
        """Внутренний метод для получения API-ключа OpenRouter."""
        try:
            # Если ключ лежит в API_KEY.py
            sys.path.append('/home/pi/project_demo/09.AI_Big_Model/')
            from API_KEY import openAI_KEY
            return openAI_KEY
        except:
            try:
                return os.environ.get("OPENROUTER_KEY", "ключ_не_найден")
            except:
                return ""

    def _get_qwen_key(self) -> str:
        """Внутренний метод для получения API-ключа Qwen."""
        try:
            sys.path.append('/home/pi/project_demo/09.AI_Big_Model/')
            from API_KEY import TONYI_key
            return TONYI_key
        except:
            return "dummy"

    def describe_scene(self, prompt: str = "Опиши, что ты видишь, на русском языке.",
                   model: str = "dots-studio/dots-3-note-preview:free",
                   use_openrouter: bool = True,
                   frame=None) -> str:   # 👈 добавили frame=None
        """
        🧠 Описывает сцену перед роботом с помощью мультимодальной AI-модели.

        Делает фото с камеры, отправляет его в модель (OpenRouter или Qwen)
        и возвращает текстовое описание.

        :param prompt: текстовый запрос к модели (по умолчанию "Опиши, что ты видишь, на русском языке.")
        :param model: имя модели (для OpenRouter, например "openai/gpt-4o-mini" или "qwen/qwen-vl-plus")
        :param use_openrouter: True – использовать OpenRouter, False – использовать Qwen (dashscope)
        :param frame: готовый кадр (numpy array). Если None, то будет сделан новый снимок с камеры.
        :return: текстовое описание или сообщение об ошибке

        Пример:
            desc = r.describe_scene()
            print(desc)
        """
        import base64
        import requests
        import json

        # 1. Захват кадра (если не передан)
        if frame is None:
            frame = self.capture_frame()
            if frame is None:
                return "❌ Не удалось получить кадр с камеры"

        temp_path = "/tmp/scene.jpg"
        cv2.imwrite(temp_path, frame)

        with open(temp_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # 2. Отправка запроса
        if use_openrouter:
            key = self._get_openrouter_key()
            if not key:
                return "❌ Не найден API-ключ OpenRouter."
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]}
                ]
            }
            try:
                resp = requests.post(url, headers=headers, json=data, timeout=30)
                if resp.status_code == 200:
                    return resp.json()['choices'][0]['message']['content']
                else:
                    return f"❌ Ошибка API ({resp.status_code}): {resp.text}"
            except Exception as e:
                return f"❌ Ошибка запроса: {e}"
        else:
            # Qwen (dashscope)
            try:
                import dashscope
                from dashscope import MultiModalConversation
                key = self._get_qwen_key()
                if not key:
                    return "❌ Не найден API-ключ Qwen."
                dashscope.api_key = key
                messages = [{
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{img_b64}"},
                        {"text": prompt}
                    ]
                }]
                response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
                if response.status_code == 200:
                    return response.output.choices[0].message.content[0]['text']
                else:
                    return f"❌ Ошибка Qwen: {response.message}"
            except ImportError:
                return "❌ Установите dashscope: pip install dashscope"
            except Exception as e:
                return f"❌ Ошибка Qwen: {e}"

    # ====================================================================
    # СИСТЕМНАЯ ИНФОРМАЦИЯ
    # ====================================================================

    def get_ip(self) -> str:
        """🌐 Возвращает текущий IP-адрес робота."""
        return _get_ip()

    def get_cpu(self) -> str:
        """💻 Возвращает загрузку CPU в процентах (строка)."""
        try:
            import psutil
            return f"{psutil.cpu_percent():.1f}%"
        except ImportError:
            return "N/A"

    def get_ram(self) -> str:
        """🧠 Возвращает информацию об использовании RAM."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return f"{mem.percent:.1f}% ({mem.used//1024//1024}MB)"
        except ImportError:
            return "N/A"

    def get_disk(self) -> str:
        """💾 Возвращает информацию о свободном месте на SD-карте."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return f"{disk.percent:.1f}% ({disk.free//1024//1024}MB свободно)"
        except ImportError:
            return "N/A"

    def get_temperature(self) -> str:
        """🌡️ Возвращает температуру CPU."""
        return _get_cpu_temp()

    def get_battery(self) -> int:
        """🔋 Возвращает приблизительный уровень заряда батареи (0–100)."""
        return _get_battery()

    # ====================================================================
    # КОНТЕКСТНЫЙ МЕНЕДЖЕР
    # ====================================================================

    def __enter__(self):
        """Поддерживает конструкцию `with Robot() as r:`."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """При выходе из контекста останавливает моторы и восстанавливает состояние."""
        self.stop()
        self.restore()

# ====================================================================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# ====================================================================

if __name__ == "__main__":
    with Robot() as r:
        r.forward(150)
        time.sleep(2)
        r.stop()
        r.say("Привет, я робот!")
        r.oled_show_text("Тест", "Работает!")
        time.sleep(2)