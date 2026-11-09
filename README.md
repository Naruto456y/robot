# 🤖 Raspbot V2 — управление роботом на Python

Код для робота **Yahboom Raspbot V2 Superior** на **Raspberry Pi 5**: удобная обёртка над железом, веб-панель управления, AI-функции и анимации на OLED-дисплее.

## ✨ Главное — модуль `myrobot.py`

Один класс `Robot` даёт доступ ко всему железу робота. Про I2C, сервоприводы и порядок инициализации думать не нужно.

```python
from myrobot import Robot

r = Robot()                       # отключает стандартный экран, ставит камеру в центр
r.oled_show_text("Привет!", "Я робот")
r.rgb_effect_river(duration=3)
r.forward(150); time.sleep(1); r.stop()
print(r.get_distance(), "см")
r.say("Вижу препятствие")
r.restore()                       # вернуть всё как было (срабатывает и по Ctrl+C)
```

| Группа | Методы |
|---|---|
| 🚗 Движение (меканум-колёса) | `forward`, `backward`, `left`, `right`, `rotate_left/right`, `diagonal_*`, `stop` |
| 📷 Камера и сервоприводы | `camera_center/left/right/up/down`, `camera_set`, `capture_frame`, `save_photo`, `start_stream` |
| 💡 RGB и звук | `rgb_color`, `rgb_led`, `rgb_effect_*` (river, breathing, gradient…), `beep`, `beep_short` |
| 🖥 OLED 128×32 | `oled_show_text`, `oled_show_image`, `oled_clear` |
| 📏 Датчики | `get_distance` (ультразвук), `is_key_pressed`, `get_battery` |
| 🗣 Голос | `say` (edge-tts), `play_mp3`, `listen` (распознавание речи), `record_mic_mp3` |
| 🧠 Компьютерное зрение | `detect_faces`, `register_face`, `detect_objects_yolo`, `detect_qr`, `detect_color` |
| 👁 Мультимодальный AI | `describe_scene` — робот фотографирует и описывает словами, что видит (OpenRouter) |
| ⚙️ Система | `get_ip`, `get_cpu`, `get_ram`, `get_disk`, `get_temperature`, `switch_wifi` |

При выходе робот сам восстанавливает исходное состояние (`atexit` + обработчик сигналов): моторы стоят, камера в центре, стандартный экран вернулся.

## 🌐 Веб-панель — `robot_web_final.py`

Flask-сервер на порту **8180**: управление с телефона или ноутбука прямо в браузере.

- видео с камеры в реальном времени, фото, запись видео, галерея;
- движение, камера, RGB, сигнал, показания ультразвука, статус батареи и системы;
- озвучка текста, загрузка и проигрывание mp3, запись с микрофона, распознавание речи;
- «Что ты видишь?»: описание сцены через AI;
- встроенный редактор кода `/cod` и выполнение команд. Эти эндпоинты закрыты токеном `ROBOT_TOKEN`.

```bash
export ROBOT_TOKEN="придумай-длинный-токен"
python3 robot_web_final.py      # затем открыть http://<IP-робота>:8180
```

## 🍥 OLED-анимации — `oled_animations/`

Покадровые анимации для дисплея 128×32 на `luma.oled`:

- **Наруто**: лицо, расенган, сюрикен, Коноха;
- **Чидори**: три печати и молния;
- **Мультик**: маленький робот и звезда, со звуком;
- **Пишем код**: ошибка → исправление → успех.

```bash
./oled_animations/play.sh          # меню
./oled_animations/play.sh naruto   # сразу запустить
```

## 📁 Структура проекта

```
myrobot.py              ядро: класс Robot
robot_web_final.py      веб-панель (+ robot_web_html.html, code_editor.html)
oled_animations/        анимации на OLED
examples/
  vision/               лица (регистрация, распознавание, сканер), пальцы, анализ и AI-описание сцены
  voice/                голосовое управление, распознавание речи (Vosk), запись микрофона
  oled/                 дальномер, системная информация и рисунки на OLED
  stream/               MJPEG-стриминг камеры
  fun/                  расенган, поздравление с днём рождения и другие приколы
tools/                  батарея, мониторинг процессов, кнопка, автостарт, скачивание аудио
tests/                  проверки железа и модуля myrobot
telebot/                Telegram-бот и игры для него
study/                  учебные опыты: PID, слежение за лицом, YOLO, SSD
project_demo/           демо-примеры Yahboom (код производителя)
software/oled_yahboom/  стандартный экран OLED
```

Скрипты из подпапок импортируют `myrobot` напрямую: путь к корню проекта лежит в `myrobot.pth` в site-packages.

## 🔧 Железо и зависимости

- Yahboom Raspbot V2 Superior, Raspberry Pi 5, Python 3.11.
- Голосовой модуль CSK4002: 2 микрофона и динамик.
- `Raspbot_Lib` (библиотека Yahboom), `luma.oled`, `opencv-python`, `numpy`, `Pillow`, `edge-tts`, `flask`.

## 🔐 Ключи

В коде нет ни одного ключа: все берутся из переменных окружения.

| Переменная | Для чего |
|---|---|
| `ROBOT_TOKEN` | доступ к опасным эндпоинтам веб-панели |
| `OPENROUTER_KEY` | `describe_scene` |
| `WIFI_AI_SSID`, `WIFI_AI_PASS`, `WIFI_HOME_SSID`, `WIFI_HOME_PASS` | `describe_scene.py` переключает Wi-Fi |
