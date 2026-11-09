#!/usr/bin/env python3
"""Анимация «Чидори» на OLED 128x32: руки складывают три печати, потом молния в руке.

Печати: 1 USHI (Вол) → 2 U (Заяц) → 3 SARU (Обезьяна) → CHIDORI!
Руки схематичные (на 128x32 иначе не нарисовать), каждая печать подписана.
Всё рисуется кодом. Цикл ≈ 11 секунд.

Запуск:  python3 oled_chidori.py [секунд]   (по умолчанию до Ctrl+C)
"""
import math
import random
import sys
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageFont

from oled_claude_anim import take_oled  # забрать OLED у стандартного экрана и вернуть при выходе

W, H = 128, 32
CX = 88            # центр рук по горизонтали (слева место под подпись)
SEAL_T = 1.9       # секунд на одну печать
CHIDORI_T = 4.6    # секунд на финальную вспышку
CYCLE = SEAL_T * 3 + CHIDORI_T


def font(size, bold=False):
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except OSError:
        return ImageFont.load_default()


def rot(points, ang, cx, cy):
    """Поворот точек на ang градусов вокруг (cx, cy)."""
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in points]


def hand(draw, x, y, ang=0, mirror=False, fingers=4, finger_len=8, palm=(10, 11)):
    """Схематичная ладонь: прямоугольник-ладонь + пальцы вверх (до поворота).
    (x, y) — центр основания ладони. mirror зеркалит по горизонтали."""
    pw, ph = palm
    sgn = -1 if mirror else 1
    pts = [(x - pw / 2, y - ph), (x + pw / 2, y - ph), (x + pw / 2, y), (x - pw / 2, y)]
    draw.polygon(rot(pts, ang * sgn, x, y), fill="white", outline="white")
    gap = pw / fingers
    for i in range(fingers):
        fx = x - pw / 2 + gap * i + 0.5
        fl = finger_len + (2 if i in (1, 2) else 0)  # средние пальцы длиннее
        f = [(fx, y - ph - fl), (fx + gap - 1.4, y - ph - fl), (fx + gap - 1.4, y - ph + 1), (fx, y - ph + 1)]
        draw.polygon(rot(f, ang * sgn, x, y), fill="white")


def ease(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


# ---------- печати ----------
def seal_ushi(draw, t):
    """Вол: ладони вместе, пальцы вверх, два указательных вытянуты."""
    k = ease(t / 0.45)
    off = (1 - k) * 34
    hand(draw, CX - 6 - off, 30, 0, False, fingers=4, finger_len=9)
    hand(draw, CX + 6 + off, 30, 0, True, fingers=4, finger_len=9)
    if k >= 1:
        draw.rectangle((CX - 1, 9, CX, 30), fill="black")  # щель между ладонями


def seal_u(draw, t):
    """Заяц: ладони скрещены крестом, пальцы вверх."""
    k = ease(t / 0.45)
    off = (1 - k) * 34
    hand(draw, CX - 8 - off, 31, 28, False, fingers=4, finger_len=8)
    hand(draw, CX + 8 + off, 31, 28, True, fingers=4, finger_len=8)
    if k >= 1:
        draw.line((CX - 6, 30, CX + 4, 14), fill="black")  # граница перекрытия


def seal_saru(draw, t):
    """Обезьяна: одна ладонь плашмя сверху, вторая кулаком снизу."""
    k = ease(t / 0.45)
    off = (1 - k) * 34
    hand(draw, CX - 4 - off, 17, 90, False, fingers=4, finger_len=9, palm=(9, 12))      # плашмя
    draw.rounded_rectangle((CX - 10 + off, 18, CX + 10 + off, 30), radius=3, fill="white")  # кулак
    if k >= 1:
        for i in range(1, 4):
            draw.line((CX - 10 + i * 5, 20, CX - 10 + i * 5, 24), fill="black")  # костяшки
        draw.line((CX - 9, 17, CX + 9, 17), fill="black")


SEALS = (("1 USHI", "Ox", seal_ushi), ("2 U", "Hare", seal_u), ("3 SARU", "Monkey", seal_saru))


# ---------- Чидори ----------
def bolt(draw, rnd, x0, y0, ang, length, depth=0):
    """Ломаная молния с ответвлениями."""
    x, y = x0, y0
    segs = max(3, int(length / 3))
    for _ in range(segs):
        ang += rnd.uniform(-0.9, 0.9)
        step = rnd.uniform(2.5, 4.5)
        nx, ny = x + step * math.cos(ang), y + step * math.sin(ang)
        draw.line((x, y, nx, ny), fill="white")
        if depth < 1 and rnd.random() < 0.22:
            bolt(draw, rnd, nx, ny, ang + rnd.choice((-1, 1)) * 0.9, length * 0.4, depth + 1)
        x, y = nx, ny


def scene_chidori(draw, t, f_big, f_small):
    fx, fy = CX, 17
    rnd = random.Random(int(t * 25))               # молнии «трещат» — новый узор каждый кадр
    # предплечье (из правого нижнего угла) и кулак
    draw.line((W - 4, H + 2, fx + 6, fy + 5), fill="white", width=5)
    draw.ellipse((fx - 6, fy - 6, fx + 6, fy + 6), fill="white")
    n = 9 + int(t * 2)
    for i in range(n):
        ang = (2 * math.pi * i / n) + rnd.uniform(-0.25, 0.25)
        bolt(draw, rnd, fx, fy, ang, rnd.uniform(11, 20))
    draw.ellipse((fx - 3, fy - 3, fx + 3, fy + 3), fill="black")
    draw.ellipse((fx - 1, fy - 1, fx + 1, fy + 1), fill="white")
    if int(t * 12) % 7 == 0:                       # короткая вспышка
        draw.rectangle((0, 0, W - 1, H - 1), fill="white")
        return
    draw.text((1, 1), "CHIDORI!", font=f_big, fill="white")
    draw.text((1, 20), "1000 BIRDS", font=f_small, fill="white")


def main():
    limit = float(sys.argv[1]) if len(sys.argv) > 1 else None
    take_oled()
    time.sleep(0.3)
    dev = ssd1306(i2c(port=1, address=0x3C), width=W, height=H)
    for color in (1, 0):  # стираем остатки прежнего кадра (luma шлёт только изменения)
        dev.display(Image.new("1", (W, H), color))
    f_big, f_small = font(13, bold=True), font(8)

    start = time.time()
    try:
        while limit is None or time.time() - start < limit:
            now = (time.time() - start) % CYCLE
            with canvas(dev) as draw:
                if now < SEAL_T * 3:
                    i = int(now // SEAL_T)
                    t = now - i * SEAL_T
                    name, sub, fn = SEALS[i]
                    draw.text((1, 2), name, font=f_big, fill="white")
                    draw.text((1, 20), sub, font=f_small, fill="white")
                    for d in range(3):                          # прогресс: ●●○
                        x = 44 + d * 8
                        draw.ellipse((x, 26, x + 4, 30), fill="white" if d <= i else None, outline="white")
                    fn(draw, t)
                else:
                    scene_chidori(draw, now - SEAL_T * 3, f_big, f_small)
    except KeyboardInterrupt:
        pass
    finally:
        dev.clear()


if __name__ == "__main__":
    main()
