import json
import time
from vosk import Model, KaldiRecognizer
import pyaudio
from Raspbot_Lib import Raspbot

MODEL_PATH = "model"
bot = Raspbot()

try:
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)
    print("🎤 Кеша слушает...")
except Exception as e:
    print(f"Ошибка модели: {e}")
    exit()

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4000)

COMMANDS = {
    "вперёд": lambda: bot.Ctrl_Car(0x01, 150, 150),
    "назад": lambda: bot.Ctrl_Car(0x02, 150, 150),
    "влево": lambda: bot.Ctrl_Car(0x03, 150, 150),
    "вправо": lambda: bot.Ctrl_Car(0x04, 150, 150),
    "стоп": lambda: bot.Ctrl_Car(0x00, 0, 0),
}

def execute(text):
    for cmd, action in COMMANDS.items():
        if cmd in text:
            action()
            print(f"✅ {cmd}")
            return
    print(f"❓ {text}")

print("Говори: вперёд, назад, влево, вправо, стоп")
try:
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").lower().strip()
            if text:
                execute(text)
except KeyboardInterrupt:
    print("\n👋 Кеша выключен")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    bot.Ctrl_Car(0x00, 0, 0)
