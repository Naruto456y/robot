#!/usr/bin/env python3
"""Анимация маленького «Claude Code» на OLED 128x32 (luma.oled, SSD1306, I2C).

Человечек ходит по экрану, моргает, потом садится и «печатает» в терминале.
Скрипт сам останавливает стандартный экран (yahboom-oled.service) и возвращает его при выходе.

Запуск:  python3 oled_claude_anim.py [секунд]   (по умолчанию работает до Ctrl+C)

Внимание: на роботе стоит OLED 128x32 (так его инициализирует и стандартный скрипт).
"""
import atexit
import os
import signal
import subprocess
import sys
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageFont

W, H = 128, 32
S = 2  # масштаб «пикселя» спрайта


def px(draw, x, y, w, h, fill="white"):
    """Прямоугольник в клетках спрайта (масштаб S)."""
    draw.rectangle((x * S, y * S, (x + w) * S - 1, (y + h) * S - 1), fill=fill)


def draw_clawd(draw, ox, oy, blink=False, step=0, happy=False):
    """Рисует человечка: тело 9x4 клетки, руки, глаза, четыре ножки (всего 9x6 клеток)."""
    px(draw, ox + 1, oy, 7, 4)          # тело
    px(draw, ox, oy + 1, 1, 2)          # руки
    px(draw, ox + 8, oy + 1, 1, 2)
    if blink:                            # прикрытые глаза
        px(draw, ox + 2, oy + 2, 1, 1, "black")
        px(draw, ox + 6, oy + 2, 1, 1, "black")
    elif happy:                          # глаза + улыбка
        px(draw, ox + 2, oy + 1, 1, 1, "black")
        px(draw, ox + 6, oy + 1, 1, 1, "black")
        px(draw, ox + 3, oy + 3, 3, 1, "black")
    else:                                # обычные глаза
        px(draw, ox + 2, oy + 1, 1, 2, "black")
        px(draw, ox + 6, oy + 1, 1, 2, "black")
    up = step % 2                        # ножки шагают поочерёдно
    px(draw, ox + 1, oy + 4, 1, 1 if up else 2)
    px(draw, ox + 3, oy + 4, 1, 2 if up else 1)
    px(draw, ox + 5, oy + 4, 1, 1 if up else 2)
    px(draw, ox + 7, oy + 4, 1, 2 if up else 1)


def _raspbot_pids():
    """PID процессов приложения Yahboom (raspbot.pyc). Он импортирует yahboom_oled.py,
    и цикл стандартного экрана крутится внутри него: каждые 2 с он перерисовывает дисплей."""
    pids = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open(f"/proc/{d}/cmdline", "rb") as f:
                argv = f.read().split(b"\0")
        except OSError:
            continue
        if len(argv) >= 2 and argv[1].endswith(b"/raspbot.pyc"):
            pids.append(int(d))
    return pids


def take_oled():
    """Освобождает OLED от стандартного экрана и вернёт его при выходе."""
    subprocess.run(["sudo", "systemctl", "stop", "yahboom-oled.service"], check=False)
    for name in ("yahboom_oled.py", "oled_system.py", "ultrasonic_oled.py"):
        subprocess.run(["sudo", "pkill", "-f", name], check=False)
    # приостанавливаем (не убиваем!) приложение Yahboom, чтобы оно не рисовало поверх
    frozen = _raspbot_pids()
    for pid in frozen:
        subprocess.run(["sudo", "kill", "-STOP", str(pid)], check=False)

    def restore():
        for pid in frozen:
            subprocess.run(["sudo", "kill", "-CONT", str(pid)], check=False)
        subprocess.run(["sudo", "systemctl", "start", "yahboom-oled.service"], check=False)

    atexit.register(restore)
    # SIGTERM/SIGHUP (закрыли терминал, kill) тоже должны вернуть всё как было
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, lambda *_: sys.exit(0))


def main():
    limit = float(sys.argv[1]) if len(sys.argv) > 1 else None
    take_oled()
    time.sleep(0.3)
    dev = ssd1306(i2c(port=1, address=0x3C), width=W, height=H)
    # luma шлёт на дисплей только изменившуюся часть кадра и считает, что экран чёрный.
    # Остатки стандартного экрана в памяти дисплея так бы и остались — забиваем всё явно.
    for color in (1, 0):
        dev.display(Image.new("1", (W, H), color))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    except OSError:
        font = ImageFont.load_default()

    start = time.time()
    try:
        while limit is None or time.time() - start < limit:
            # анимация по реальному времени (16 «тиков» в секунду), а не по числу кадров
            t = int((time.time() - start) * 16)
            phase = (t // 48) % 2  # 0 — гуляет, 1 — печатает
            with canvas(dev) as draw:
                if phase == 0:
                    span = W - 9 * S
                    p = (t * 2) % (span * 2)
                    x = p if p < span else span * 2 - p
                    draw_clawd(draw, x // S, 0, blink=(t % 25 < 2), step=t // 3)
                    draw.text((26, 17), "Claude Code", font=font, fill="white")
                else:
                    draw_clawd(draw, 1, 3, blink=(t % 20 < 2), happy=(t % 48 > 32))
                    draw.rectangle((24, 0, W - 1, H - 1), outline="white")
                    typed = "> hello, Pi!"
                    n = min(len(typed), (t % 48) // 2)
                    draw.text((28, 8), typed[:n], font=font, fill="white")
                    if (t // 4) % 2 == 0:
                        cx = 28 + n * 7
                        draw.rectangle((cx, 8, cx + 5, 22), fill="white")
    except KeyboardInterrupt:
        pass
    finally:
        dev.clear()


if __name__ == "__main__":
    main()
