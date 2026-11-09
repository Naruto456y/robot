#!/usr/bin/env python3
# record_mic.py – запись микрофона в MP3 через Python
import sounddevice as sd
import numpy as np
import wave
import os
import subprocess
import sys

# ===== НАСТРОЙКИ =====
DURATION = 10           # длительность записи в секундах
SAMPLE_RATE = 44100     # частота дискретизации
CHANNELS = 1            # 1 = моно, 2 = стерео
DEVICE_INDEX = 0        # индекс устройства (USB Audio Device)
WAV_PATH = "/tmp/record.wav"
MP3_PATH = "/home/pi/test_mic.mp3"


def list_devices():
    """Показать список устройств ввода."""
    print("🎤 Доступные устройства ввода:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            marker = " ← по умолчанию" if i == sd.default.device[0] else ""
            print(f"   [{i}] {dev['name']} (каналов: {dev['max_input_channels']}){marker}")


def record_audio():
    """Записывает аудио с микрофона в WAV."""
    print(f"🎤 Запись {DURATION} секунд... Говорите!")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16',
        device=DEVICE_INDEX
    )
    sd.wait()  # ждём окончания записи

    # Сохраняем в WAV
    with wave.open(WAV_PATH, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    print(f"✅ Запись сохранена: {WAV_PATH}")

    # Проверяем уровень сигнала
    amplitude = np.abs(audio).mean()
    print(f"📊 Средняя амплитуда: {amplitude:.1f} (0 = тишина, >100 = есть звук)")
    if amplitude < 10:
        print("⚠️ Микрофон почти не пишет — возможно, тишина или не тот device_index")
    else:
        print("✅ Микрофон улавливает звук")

    return audio


def convert_to_mp3():
    """Конвертирует WAV в MP3 через ffmpeg."""
    print("🔄 Конвертация в MP3...")
    cmd = [
        "ffmpeg", "-y",
        "-i", WAV_PATH,
        "-codec:a", "libmp3lame",
        "-qscale:a", "2",
        MP3_PATH
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size = os.path.getsize(MP3_PATH)
        print(f"✅ MP3 сохранён: {MP3_PATH} ({size} байт)")
    else:
        print(f"❌ Ошибка ffmpeg: {result.stderr}")


if __name__ == "__main__":
    print("=" * 50)
    print("🎤 ЗАПИСЬ МИКРОФОНА В MP3")
    print("=" * 50)

    list_devices()
    print()

    try:
        record_audio()
        convert_to_mp3()
        print("\n📥 Скачай файл на комп:")
        print(f"   scp pi@192.168.1.56:{MP3_PATH} C:\\Users\\Yusuf\\Desktop\\")
    except KeyboardInterrupt:
        print("\n🛑 Прервано")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)