#!/usr/bin/env python3
"""Анимация «Наруто» на OLED 128x32 (luma.oled, SSD1306, I2C). Рисуется кодом, без картинок.

Четыре сцены по 5 секунд, по кругу:
  1. Лицо Наруто (колючие волосы, повязка, «усы» на щеках) + надпись NARUTO
  2. Расенган — вращающаяся сфера растёт и вспыхивает
  3. Летящий сюрикен со шлейфом и надпись «Dattebayo!»
  4. Символ Скрытого Листа (Konoha) — вращающаяся спираль

Запуск:  python3 oled_naruto.py [секунд]   (по умолчанию до Ctrl+C)
Стандартный экран и приложение Yahboom на это время приостанавливаются и потом возвращаются.
"""
import math
import random
import sys
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageFont

from oled_claude_anim import take_oled  # общая логика «забрать OLED и вернуть при выходе»

W, H = 128, 32
SCENE = 5.0  # секунд на сцену


def font(size, bold=False):
    name = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except OSError:
        return ImageFont.load_default()


def spiral(draw, cx, cy, rmax, turns, rot, width=1):
    """Спираль Архимеда, повёрнутая на rot радиан."""
    pts = []
    n = 60
    for i in range(n + 1):
        th = turns * 2 * math.pi * i / n
        r = rmax * i / n
        pts.append((cx + r * math.cos(th + rot), cy + r * math.sin(th + rot)))
    draw.line(pts, fill="white", width=width)


# ---------------- сцена 1: лицо ----------------
def scene_face(draw, t, f_big, f_small):
    cx, cy = 30, 19
    # колючие волосы (белые треугольники над головой)
    for dx, h in ((-13, 8), (-8, 12), (-3, 9), (3, 12), (8, 9), (13, 8)):
        draw.polygon([(cx + dx - 4, cy - 9), (cx + dx, cy - 9 - h), (cx + dx + 4, cy - 9)], fill="white")
    # голова
    draw.ellipse((cx - 14, cy - 12, cx + 14, cy + 12), fill="white")
    # повязка: чёрная лента с белой пластиной
    draw.rectangle((cx - 14, cy - 9, cx + 14, cy - 4), fill="black")
    draw.rectangle((cx - 6, cy - 9, cx + 6, cy - 4), fill="white")
    draw.rectangle((cx - 4, cy - 8, cx + 4, cy - 5), outline="black")
    draw.line((cx - 2, cy - 6, cx + 2, cy - 7), fill="black")
    # глаза (иногда моргает)
    blink = (t % 2.4) < 0.15
    for ex in (-6, 5):
        if blink:
            draw.line((cx + ex - 1, cy - 1, cx + ex + 2, cy - 1), fill="black")
        else:
            draw.rectangle((cx + ex, cy - 3, cx + ex + 1, cy + 0), fill="black")
    # «усы» — по три чёрточки на щеках
    for side in (-1, 1):
        for k in (-2, 0, 2):
            draw.line((cx + side * 9, cy + 3 + k, cx + side * 13, cy + 2 + k * 2), fill="black")
    # улыбка
    draw.arc((cx - 6, cy + 1, cx + 6, cy + 9), 20, 160, fill="black")
    # надпись справа
    draw.text((52, 1), "NARUTO", font=f_big, fill="white")
    draw.text((52, 20), "UZUMAKI", font=f_small, fill="white")


# ---------------- сцена 2: расенган ----------------
def scene_rasengan(draw, t, f_big, f_small):
    cx, cy = 64, 16
    p = min(t / 3.6, 1.0)                    # 0→1: сфера растёт
    r = 3 + 12 * p
    spin = t * 14
    for k in range(4):                       # вращающиеся дуги
        rr = r * (1 - k * 0.2)
        if rr < 2:
            continue
        a0 = math.degrees(spin * (1 if k % 2 == 0 else -1)) + k * 90
        draw.arc((cx - rr, cy - rr, cx + rr, cy + rr), a0, a0 + 140, fill="white")
        draw.arc((cx - rr, cy - rr, cx + rr, cy + rr), a0 + 180, a0 + 300, fill="white")
    draw.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill="white")
    # искры по орбите
    rnd = random.Random(int(t * 12))
    for _ in range(6):
        ang = rnd.uniform(0, 2 * math.pi)
        d = r + rnd.uniform(2, 9)
        x, y = cx + d * math.cos(ang), cy + d * math.sin(ang) * 0.9
        draw.point((x, y), fill="white")
    if t > 1.0:
        draw.text((2, 11), "RASEN", font=f_small, fill="white")
    if t > 2.2:
        draw.text((94, 11), "GAN!", font=f_small, fill="white")
    if t > 4.6:                              # вспышка
        if int(t * 20) % 2 == 0:
            draw.rectangle((0, 0, W - 1, H - 1), fill="white")


# ---------------- сцена 3: сюрикен ----------------
def star(draw, cx, cy, r, rot):
    pts = []
    for i in range(8):
        ang = rot + i * math.pi / 4
        rad = r if i % 2 == 0 else r * 0.35
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill="white")
    draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill="black")


def scene_shuriken(draw, t, f_big, f_small):
    x = -10 + (t / 3.0) * (W + 30)
    y = 16 + 3 * math.sin(t * 4)
    for k in range(1, 6):                    # шлейф
        draw.line((x - 8 - k * 7, y - 3 + k % 2 * 3, x - 14 - k * 7, y - 3 + k % 2 * 3), fill="white")
    star(draw, x, y, 9, t * 18)
    if t > 1.6:
        draw.text((10, 1), "Dattebayo!", font=f_big, fill="white")
    if t > 3.2 and int(t * 4) % 2 == 0:
        draw.text((10, 22), "BELIEVE IT!", font=f_small, fill="white")


# ---------------- сцена 4: символ Конохи ----------------
def scene_leaf(draw, t, f_big, f_small):
    cx, cy = 22, 17
    spiral(draw, cx, cy, 13, 2.2, t * 2.5, width=2)
    draw.polygon([(cx - 2, cy - 15), (cx, cy - 20), (cx + 2, cy - 15)], fill="white")  # кончик листа
    draw.text((46, 3), "KONOHA", font=f_big, fill="white")
    draw.text((46, 20), "Hidden Leaf", font=f_small, fill="white")


SCENES = (scene_face, scene_rasengan, scene_shuriken, scene_leaf)


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
            now = time.time() - start
            idx = int(now // SCENE) % len(SCENES)
            t = now % SCENE
            with canvas(dev) as draw:
                SCENES[idx](draw, t, f_big, f_small)
    except KeyboardInterrupt:
        pass
    finally:
        dev.clear()


if __name__ == "__main__":
    main()
