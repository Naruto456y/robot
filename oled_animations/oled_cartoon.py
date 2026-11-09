#!/usr/bin/env python3
"""Мультик «Маленький робот и звезда» на OLED 128x32 со ТИХИМ звуком (USB-динамик).

Сюжет (≈ 24 с): робот катится под звёздным небом → замечает падающую звезду → ловит её →
радуется под мелодию → уезжает. Звук синтезируется кодом и проигрывается через aplay.

Запуск:  python3 oled_cartoon.py [громкость 0..1]   (по умолчанию 0.10 — тихо)
Пример:  python3 oled_cartoon.py 0.05   — ещё тише
"""
import math
import os
import random
import subprocess
import sys
import tempfile
import time
import wave

import numpy as np
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageFont

from oled_claude_anim import take_oled  # забрать OLED у стандартного экрана и вернуть при выходе

W, H = 128, 32
DURATION = 24.0
SR = 22050
AUDIO_DEV = "plughw:2,0"  # USB Audio Device (динамик)
GROUND = 29


# =============================== звук ===============================
def _env(n, attack=0.01, release=0.06):
    a = max(1, min(int(attack * SR), n // 2))     # у коротких звуков огибающая не длиннее самого звука
    r = max(1, min(int(release * SR), n // 2))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.minimum(e[-r:], np.linspace(1, 0, r))
    return e


def tone(freq, dur, vol=1.0, shape="sine"):
    n = int(dur * SR)
    ph = 2 * np.pi * freq * np.arange(n) / SR
    if shape == "square":
        w = np.sign(np.sin(ph)) * 0.5
    elif shape == "tri":
        w = 2 / np.pi * np.arcsin(np.sin(ph))
    else:
        w = np.sin(ph)
    return w * _env(n) * vol


def sweep(f0, f1, dur, vol=1.0, vibrato=0.0):
    n = int(dur * SR)
    f = np.linspace(f0, f1, n)
    if vibrato:
        f = f * (1 + vibrato * np.sin(2 * np.pi * 7 * np.arange(n) / SR))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env(n, 0.02, 0.1) * vol


NOTE = {"C4": 261.6, "E4": 329.6, "G4": 392.0, "C5": 523.3, "D5": 587.3, "E5": 659.3,
        "G5": 784.0, "A5": 880.0, "C6": 1046.5}


def build_audio(volume):
    buf = np.zeros(int((DURATION + 1) * SR))

    def put(t, snd):
        i = int(t * SR)
        buf[i:i + len(snd)] += snd[:len(buf) - i]

    # колёса: тихие «тики», пока робот едет к центру
    t = 0.3
    while t < 3.9:
        put(t, tone(700, 0.025, 0.35, "square")); t += 0.3
    # «?» — два вопросительных блупа
    put(4.2, sweep(380, 720, 0.18, 0.7)); put(4.55, sweep(420, 800, 0.2, 0.7))
    # падающая звезда: свист вниз с лёгким дрожанием
    put(6.0, sweep(1700, 520, 3.9, 0.45, vibrato=0.02))
    # прыжок и поимка
    put(10.05, sweep(280, 900, 0.3, 0.8))
    for k, n in enumerate(("C5", "E5", "G5", "C6")):
        put(11.2 + k * 0.1, tone(NOTE[n], 0.14, 0.8, "tri"))
    # весёлая мелодия, пока робот радуется
    tune = ["C5", "E5", "G5", "E5", "C5", "E5", "G5", "C6", "A5", "G5", "E5", "G5"]
    t = 12.0
    for i in range(12):
        put(t, tone(NOTE[tune[i]], 0.2, 0.7, "tri")); t += 0.5
    # колёса: уезжает
    t = 18.2
    while t < 21.0:
        put(t, tone(700, 0.025, 0.35, "square")); t += 0.25
    # финальный аккорд
    for n in ("C4", "E4", "G4"):
        put(21.3, tone(NOTE[n], 1.8, 0.5))

    peak = max(1e-6, np.max(np.abs(buf)))
    return (buf / peak * volume * 32767).astype(np.int16)  # volume = доля от максимума


def write_wav(path, data):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(data.tobytes())


# ============================ картинка ==============================
def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def robot_pos(t):
    """x центра робота и смещение по высоте (прыжок)."""
    if t < 4.0:
        x = -14 + 70 * ease(t / 4.0)
    elif t < 18.0:
        x = 56
    else:
        x = 56 + 90 * ease((t - 18.0) / 3.0)
    dy = 0
    if 10.0 <= t < 11.2:
        dy = -11 * math.sin((t - 10.0) / 1.2 * math.pi)
    elif 12.0 <= t < 18.0:
        dy = -2 * abs(math.sin((t - 12.0) * math.pi / 0.5)) if t % 0.5 < 0.25 else 0  # притопывает в такт
    return x, dy


def star(draw, cx, cy, r):
    pts = []
    for i in range(8):
        a = i * math.pi / 4
        rad = r if i % 2 == 0 else r * 0.38
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    draw.polygon(pts, fill="white")


def draw_robot(draw, x, dy, t):
    top = GROUND - 22 + dy                          # верх тела
    # колёса
    spin = int(t * 8) % 2
    for wx in (x - 6, x + 6):
        draw.ellipse((wx - 3, GROUND - 6 + dy, wx + 3, GROUND + dy), outline="white", fill="black")
        draw.point((wx + (1 if spin else -1), GROUND - 3 + dy), fill="white")
    # тело
    draw.rectangle((x - 9, top + 6, x + 9, GROUND - 5 + dy), fill="white")
    # антенна с мигающим шариком
    draw.line((x, top + 6, x, top + 1), fill="white")
    if int(t * 4) % 2 == 0 or t < 4:
        draw.ellipse((x - 1, top - 1, x + 1, top + 1), fill="white")
    # глаза: смотрят вверх, когда замечают звезду
    ey = top + 11
    look_up = 4.0 <= t < 10.0
    for ex in (x - 5, x + 3):
        if (t % 2.6) < 0.14 and not look_up:
            draw.line((ex, ey + 2, ex + 2, ey + 2), fill="black")                     # моргает
        else:
            draw.rectangle((ex, ey - (2 if look_up else 0), ex + 2, ey + 3 - (2 if look_up else 0)), fill="black")
    # улыбка, когда рад
    if t >= 11.2:
        draw.arc((x - 4, ey + 3, x + 4, ey + 10), 20, 160, fill="black")
    # руки: подняты вверх, когда держит звезду
    if 10.6 <= t < 18.0:
        draw.line((x - 9, top + 9, x - 12, top + 2), fill="white", width=2)
        draw.line((x + 9, top + 9, x + 12, top + 2), fill="white", width=2)
    return top


def draw_sky(draw, t):
    rnd = random.Random(7)
    for i in range(16):
        sx, sy = rnd.randrange(W), rnd.randrange(0, 20)
        if (int(t * 2) + i) % 3:
            draw.point((sx, sy), fill="white")
        else:
            draw.line((sx - 1, sy, sx + 1, sy), fill="white"); draw.line((sx, sy - 1, sx, sy + 1), fill="white")
    draw.line((0, GROUND + 1, W - 1, GROUND + 1), fill="white")


def frame(draw, t, f_big, f_mid):
    draw_sky(draw, t)
    x, dy = robot_pos(t)
    top = draw_robot(draw, x, dy, t)

    if 4.0 <= t < 6.0 and int(t * 4) % 2 == 0:
        draw.text((x + 12, top - 3), "?", font=f_big, fill="white")

    # падающая звезда
    if 6.0 <= t < 10.6:
        p = ease((t - 6.0) / 4.0)
        sx0, sy0, sx1, sy1 = 122, -4, x + 1, top - 5
        sx, sy = sx0 + (sx1 - sx0) * p, sy0 + (sy1 - sy0) * p
        for k in range(1, 6):                       # хвост
            draw.point((sx + k * 3.2, sy - k * 1.6), fill="white")
        star(draw, sx, sy, 4)
    elif 10.6 <= t < 18.0:                          # держит звезду над головой
        star(draw, x, top - 6 + (dy * 0), 5)
        if t >= 11.2:                               # искорки вокруг
            for k in range(6):
                a = t * 2 + k * 1.05
                draw.point((x + 15 * math.cos(a), top - 6 + 9 * math.sin(a)), fill="white")
    elif t >= 18.0 and t < 21.6:
        star(draw, x, top - 6, 5)

    if 12.0 <= t < 18.0 and int(t * 2) % 2 == 0:
        draw.text((3, 2), "Yay!", font=f_big, fill="white")
    if t >= 21.4:
        w = draw.textlength("THE END", font=f_mid)
        draw.text(((W - w) / 2, 10), "THE END", font=f_mid, fill="white")


def main():
    volume = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10
    volume = max(0.0, min(volume, 1.0))
    take_oled()
    time.sleep(0.3)
    dev = ssd1306(i2c(port=1, address=0x3C), width=W, height=H)
    for color in (1, 0):
        dev.display(Image.new("1", (W, H), color))
    try:
        f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 12)
        f_mid = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 11)
    except OSError:
        f_big = f_mid = ImageFont.load_default()

    tmp = tempfile.mkdtemp(prefix="_cartoon_")
    wav = os.path.join(tmp, "cartoon.wav")
    write_wav(wav, build_audio(volume))
    player = None
    try:
        player = subprocess.Popen(["aplay", "-q", "-D", AUDIO_DEV, wav])
        start = time.time()
        while time.time() - start < DURATION:
            with canvas(dev) as draw:
                frame(draw, time.time() - start, f_big, f_mid)
    except KeyboardInterrupt:
        pass
    finally:
        if player and player.poll() is None:
            player.terminate()
        dev.clear()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
