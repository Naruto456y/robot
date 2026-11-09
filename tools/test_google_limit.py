#!/usr/bin/env python3
import speech_recognition as sr
import time
import numpy as np
import audioop

def generate_silence(duration=1.5, sample_rate=16000):
    """Генерирует аудио-тишину (полезно для тестов)"""
    samples = np.zeros(int(sample_rate * duration), dtype=np.int16)
    return samples.tobytes()

print("🔬 Проверяем лимит Google Speech. 60 автоматических запросов.")
print("Сейчас пошлём тишину — это не считается спамом, т.к. данные реальные.\n")

r = sr.Recognizer()
success = 0
fail = 0
limit_reached = False

for i in range(1, 61):
    print(f"📞 Запрос #{i}")
    # Создаём аудио-данные (тишина 1.5 сек)
    audio_data = generate_silence(duration=1.5)
    # Упаковываем в объект AudioData (имитация записи)
    audio = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)
    try:
        text = r.recognize_google(audio, language='ru-RU')
        print(f"✅ Успех: {text}")
        success += 1
    except sr.UnknownValueError:
        print("❌ Не распознано (тишина)")
        fail += 1
    except sr.RequestError as e:
        print(f"🚫 Ошибка API: {e}")
        fail += 1
        if "quota" in str(e).lower() or "limit" in str(e).lower():
            print("⚠️ Лимит достигнут!")
            limit_reached = True
            break
    except Exception as e:
        print(f"⚠️ Другая ошибка: {e}")
        fail += 1
    time.sleep(0.2)  # пауза, чтобы не перегружать

print("\n📊 Результаты:")
print(f"✅ Успешных: {success}")
print(f"❌ Неудачных: {fail}")
print(f"🚫 Лимит достигнут: {'ДА' if limit_reached else 'НЕТ (выполнено 60)'}")