#!/usr/bin/env python3
"""Мультик «Пишем код» на OLED 128x32 с тихим звуком (USB-динамик).

Сюжет (≈ 25 с):
  1. Ноутбук: на экране одна за другой появляются строки кода, слышны клавиши.
  2. Крупно редактор: печатается маленькая программа, в ней опечатка (нет закрывающей кавычки).
  3. Запуск (RUN): терминал, SyntaxError — тихий сигнал ошибки.
  4. Находим опечатку, вставляем кавычку, запускаем снова.
  5. Вывод «Hi!» и ✓ — мелодия успеха. Ноутбук улыбается.

Запуск:  python3 oled_coding.py [громкость 0..1]   (по умолчанию 0.10 — тихо)
"""
import math
import os
import random
import subprocess
import sys
import tempfile
import time

import numpy as np
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageFont

from oled_claude_anim import take_oled           # забрать OLED у стандартного экрана
from oled_cartoon import tone, NOTE, write_wav, SR, AUDIO_DEV  # синтез звука и вывод

W, H = 128, 32
DURATION = 25.0

# --- тайминги (секунды) ---
T_INTRO_END = 4.0       # ноутбук с «абстрактным» кодом
T_TYPE0, CHAR_DT = 4.4, 0.085   # начало печати и скорость (сек на символ)
T_RUN1 = 8.0            # нажали RUN в первый раз
T_ERR_END = 11.0        # конец показа ошибки
T_FIX = 11.4            # вставляем кавычку
T_RUN2 = 13.2           # запускаем снова
T_OK_END = 19.0         # конец показа успеха
T_END = 25.0

CODE_BUG = ["def hi():", '  print("Hi!)', "hi()"]
CODE_OK = ["def hi():", '  print("Hi!")', "hi()"]
FIX_LINE, FIX_COL = 1, 12   # куда вставляется «"»
TOTAL_CHARS = sum(len(s) for s in CODE_BUG)


# =============================== звук ===============================
def click(vol=1.0):
    n = int(0.012 * SR)
    return np.random.randn(n) * np.exp(-np.linspace(0, 6, n)) * vol


def build_audio(volume):
    rnd = np.random.RandomState(3)
    buf = np.zeros(int((DURATION + 1) * SR))

    def put(t, snd):
        i = int(t * SR)
        buf[i:i + len(snd)] += snd[:len(buf) - i]

    t = 0.3                                          # клавиши за ноутбуком
    while t < T_INTRO_END - 0.2:
        put(t, click(0.8)); t += rnd.uniform(0.12, 0.28)
    for k in range(TOTAL_CHARS):                     # печать кода
        put(T_TYPE0 + k * CHAR_DT, click(0.8))
    put(T_RUN1 - 0.1, tone(520, 0.05, 0.6, "square"))        # нажатие RUN
    put(T_RUN1 + 0.9, tone(170, 0.28, 0.7, "square"))        # ошибка: два низких сигнала
    put(T_RUN1 + 1.4, tone(150, 0.4, 0.7, "square"))
    put(T_FIX + 0.35, click(1.0)); put(T_FIX + 0.35, tone(900, 0.03, 0.5))   # вставили кавычку
    put(T_RUN2 - 0.1, tone(520, 0.05, 0.6, "square"))
    for k, n in enumerate(("C5", "E5", "G5", "C6")):                         # успех
        put(T_RUN2 + 1.6 + k * 0.12, tone(NOTE[n], 0.18, 0.8, "tri"))
    for k, n in enumerate(("G5", "E5", "G5", "C6", "G5", "C6")):             # весёлый хвост
        put(T_OK_END + 0.3 + k * 0.28, tone(NOTE[n], 0.2, 0.6, "tri"))
    for n in ("C4", "E4", "G4"):
        put(T_END - 3.2, tone(NOTE[n], 2.0, 0.45))
    peak = max(1e-6, np.max(np.abs(buf)))
    return (buf / peak * volume * 32767).astype(np.int16)


# ============================ картинка ==============================
def laptop(draw, ox, oy, lines_shown, face=False, t=0.0):
    """Ноутбук 64x28 с левым верхним углом (ox, oy). Внутри — «код» полосками или смайлик."""
    draw.rectangle((ox + 6, oy, ox + 57, oy + 20), outline="white")
    draw.rectangle((ox + 7, oy + 1, ox + 56, oy + 19), outline="white")
    draw.rectangle((ox, oy + 22, ox + 63, oy + 24), fill="white")           # основание
    draw.line((ox + 24, oy + 22, ox + 39, oy + 22), fill="black")           # выемка
    draw.rectangle((ox + 2, oy + 25, ox + 61, oy + 26), fill="white")
    if face:
        cx, cy = ox + 32, oy + 10
        draw.rectangle((cx - 9, cy - 5, cx - 6, cy - 2), fill="white")
        draw.rectangle((cx + 6, cy - 5, cx + 9, cy - 2), fill="white")
        draw.arc((cx - 9, cy - 3, cx + 9, cy + 7), 25, 155, fill="white")
        return
    layout = ((9, 18), (13, 30), (13, 24), (9, 22), (13, 34))               # (отступ, длина) строк
    for i, (ind, ln) in enumerate(layout):
        if i < lines_shown:
            y = oy + 3 + i * 3
            draw.line((ox + 7 + ind - 3, y, ox + 7 + ind - 3 + ln, y), fill="white")
    if int(t * 3) % 2 == 0 and lines_shown < 6:                             # курсор
        i = min(lines_shown, 4)
        draw.rectangle((ox + 10, oy + 3 + i * 3 - 1, ox + 11, oy + 3 + i * 3 + 1), fill="white")


def scene_intro(draw, t, f_big, f_small):
    laptop(draw, 3, 2, int(t / 0.7), t=t)
    draw.text((74, 3), "CODE", font=f_big, fill="white")
    dots = "." * (1 + int(t * 3) % 3)
    draw.text((74, 19), "typing" + dots, font=f_small, fill="white")


def draw_code(draw, lines, f, cursor=None, hl=None):
    """Строки кода по 8 пикселей. cursor=(line, col) — мигающий блок; hl=(line,col) — подсветка символа."""
    for i, s in enumerate(lines):
        draw.text((2, i * 8), s, font=f, fill="white")
    if hl is not None:
        li, col = hl
        x0 = 2 + f.getlength(lines[li][:col])
        x1 = 2 + f.getlength(lines[li][:col + 1])
        draw.rectangle((x0, li * 8, x1, li * 8 + 7), fill="white")
        draw.text((x0, li * 8), lines[li][col], font=f, fill="black")
    elif cursor is not None and int(time.time() * 3) % 2 == 0:
        li, col = cursor
        x = 2 + f.getlength(lines[li][:col])
        draw.rectangle((x, li * 8, x + 4, li * 8 + 7), fill="white")


def status_bar(draw, f, run_pressed):
    draw.rectangle((0, 25, W - 1, H - 1), fill="white")
    draw.text((3, 24), "hi.py", font=f, fill="black")
    if run_pressed:
        draw.rectangle((90, 25, W - 1, H - 1), fill="black")
        draw.text((94, 24), "RUN", font=f, fill="white")
    else:
        draw.text((94, 24), "RUN", font=f, fill="black")
    draw.polygon([(84, 27), (84, 30), (88, 28.5)], fill="black" if not run_pressed else "white")


def scene_editor(draw, t, f_small):
    run_pressed = (T_RUN1 - 0.25 <= t < T_RUN1) or (T_RUN2 - 0.25 <= t < T_RUN2)
    if t < T_FIX:                                    # печатаем код с опечаткой
        n = max(0, min(TOTAL_CHARS, int((t - T_TYPE0) / CHAR_DT)))
        lines, rem, cur_li = [], n, 0
        for i, s in enumerate(CODE_BUG):
            lines.append(s[:max(0, rem)])
            if rem > 0:
                cur_li = i                           # курсор — на последней строке, куда уже печатали
            rem -= len(s)
        draw_code(draw, lines, f_small, cursor=(cur_li, len(lines[cur_li])))
    else:                                            # исправили: кавычка подсвечена
        hl = (FIX_LINE, FIX_COL) if t < T_FIX + 1.2 and t >= T_FIX + 0.35 else None
        lines = CODE_OK if t >= T_FIX + 0.35 else CODE_BUG
        draw_code(draw, lines, f_small, cursor=None if hl else (FIX_LINE, 12), hl=hl)
    status_bar(draw, f_small, run_pressed)


def draw_x(draw, cx, cy, r):
    draw.line((cx - r, cy - r, cx + r, cy + r), fill="white", width=2)
    draw.line((cx - r, cy + r, cx + r, cy - r), fill="white", width=2)


def draw_check(draw, cx, cy, r):
    draw.line((cx - r, cy, cx - r // 3, cy + r), fill="white", width=2)
    draw.line((cx - r // 3, cy + r, cx + r, cy - r), fill="white", width=2)


def type_cmd(draw, f, t):
    cmd = "$ python hi.py"
    n = min(len(cmd), int(t / 0.06))
    draw.text((2, 0), cmd[:n], font=f, fill="white")
    return n == len(cmd)


def scene_error(draw, t, f_small):
    t0 = t - (T_RUN1 + 0.1)
    if t0 < 0:
        return
    if type_cmd(draw, f_small, t0) and t0 > 1.0:
        blink = int(t0 * 4) % 2 == 0
        draw.rectangle((0, 10, W - 1, 21), fill="white" if blink else "black", outline="white")
        draw.text((18, 11), "SyntaxError!", font=f_small, fill="black" if blink else "white")
        draw_x(draw, 9, 15, 4) if not blink else None
        draw.text((2, 23), "EOL while scanning", font=f_small, fill="white")


def scene_success(draw, t, f_big, f_small):
    t0 = t - (T_RUN2 + 0.1)
    if t0 < 0:
        return
    if type_cmd(draw, f_small, t0) and t0 > 1.0:
        draw.text((2, 11), "Hi!", font=f_big, fill="white")
        if t0 > 1.6:
            draw_check(draw, 52, 18, 7)
            draw.text((66, 13), "done", font=f_small, fill="white")


def scene_finale(draw, t, f_big, f_small):
    laptop(draw, 3, 2, 5, face=True, t=t)
    draw.text((74, 3), "IT", font=f_big, fill="white")
    draw.text((74, 17), "WORKS!", font=f_big, fill="white")
    rnd = random.Random(int(t * 6))                  # искорки
    for _ in range(5):
        draw.point((rnd.randrange(70, 128), rnd.randrange(0, 32)), fill="white")


def main():
    volume = float(sys.argv[1]) if len(sys.argv) > 1 else 0.10
    volume = max(0.0, min(volume, 1.0))
    take_oled()
    time.sleep(0.3)
    dev = ssd1306(i2c(port=1, address=0x3C), width=W, height=H)
    for color in (1, 0):                             # стираем остатки прежнего кадра
        dev.display(Image.new("1", (W, H), color))
    base = "/usr/share/fonts/truetype/dejavu/"
    try:
        f_big = ImageFont.truetype(base + "DejaVuSansMono-Bold.ttf", 12)
        f_small = ImageFont.truetype(base + "DejaVuSansMono.ttf", 8)
    except OSError:
        f_big = f_small = ImageFont.load_default()

    tmp = tempfile.mkdtemp(prefix="_coding_")
    wav = os.path.join(tmp, "coding.wav")
    write_wav(wav, build_audio(volume))
    player = None
    try:
        player = subprocess.Popen(["aplay", "-q", "-D", AUDIO_DEV, wav])
        start = time.time()
        while time.time() - start < DURATION:
            t = time.time() - start
            with canvas(dev) as draw:
                if t < T_INTRO_END:
                    scene_intro(draw, t, f_big, f_small)
                elif t < T_RUN1 + 0.1:
                    scene_editor(draw, t, f_small)
                elif t < T_ERR_END:
                    scene_error(draw, t, f_small)
                elif t < T_RUN2 + 0.1:
                    scene_editor(draw, t, f_small)
                elif t < T_OK_END:
                    scene_success(draw, t, f_big, f_small)
                else:
                    scene_finale(draw, t, f_big, f_small)
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
