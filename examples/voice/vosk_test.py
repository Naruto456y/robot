#!/usr/bin/env python3
import pyaudio
import wave
import json
from vosk import Model, KaldiRecognizer
import os

os.environ['VOSK_LOG_LEVEL'] = '0'  # отключаем логи Vosk

model = Model("/home/pi/model")
recognizer = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4000)

print("🎤 Говорите...")
try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            if text:
                print(f"✅ Распознано: {text}")
            else:
                print("❌ Пусто")
        else:
            # Промежуточные результаты не выводим, чтобы не засорять
            pass
except KeyboardInterrupt:
    print("👋 Выход")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()