#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Робот-сайт (Flask) для Raspbot.

Токен для опасных эндпоинтов (/cod, /api/command, /api/files, /api/file*):
    export ROBOT_TOKEN="свой-длинный-секрет"
Если переменная не задана, токен генерируется при каждом запуске и печатается в консоль.
Открыть редактор: http://<ip>:8080/cod?token=<токен> (токен уйдёт в cookie).
"""

import atexit
import hmac
import os
import secrets
import subprocess
import tempfile
import threading
import time
import uuid
from functools import wraps
from queue import Full, Queue

import cv2
from flask import (Flask, Response, jsonify, make_response, redirect, request,
                   send_from_directory, url_for)
from werkzeug.utils import secure_filename

from myrobot import Robot

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    sr = None
    SR_AVAILABLE = False

# ====== Настройки ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.realpath("/home/pi")
STATIC_DIR = os.path.join(ROOT_DIR, "static")
PHOTOS_DIR = os.path.join(STATIC_DIR, "photos")
VIDEOS_DIR = os.path.join(STATIC_DIR, "videos")
PORT = 8180

MAX_UPLOAD_MB = 20
MAX_RECORD_SEC = 60
MAX_EDIT_FILE_BYTES = 2 * 1024 * 1024
VIDEO_FPS = 20.0
RESULT_TTL_SEC = 600  # сколько хранить результаты AI-задач

for _d in (STATIC_DIR, PHOTOS_DIR, VIDEOS_DIR):
    os.makedirs(_d, exist_ok=True)

# static_folder=None: свой маршрут /static/... ниже, без конфликта со встроенным
app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
robot = Robot()

# ====== Авторизация ======
TOKEN = os.environ.get("ROBOT_TOKEN")
TOKEN_GENERATED = TOKEN is None
if TOKEN_GENERATED:
    TOKEN = secrets.token_urlsafe(12)


def token_ok():
    supplied = request.headers.get("X-Token") or request.cookies.get("robot_token") or ""
    return hmac.compare_digest(supplied.encode(), TOKEN.encode())


def require_token(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not token_ok():
            return jsonify({"error": "Нужен токен (заголовок X-Token или cookie)"}), 401
        return fn(*args, **kwargs)
    return wrapper


def safe_path(path):
    """Реальный путь, если он внутри ROOT_DIR, иначе None (защита от ../ и симлинков)."""
    if not path or not isinstance(path, str):
        return None
    real = os.path.realpath(path)
    if real == ROOT_DIR or real.startswith(ROOT_DIR + os.sep):
        return real
    return None


# ====== Захват кадров (поток) ======
current_frame = None
frame_lock = threading.Lock()
capture_stop = threading.Event()


def find_camera():
    for i in range(6):
        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                return i
    return None


def capture_loop():
    global current_frame
    print("capture_loop запущен")
    cam_index = None
    while not capture_stop.is_set():
        if cam_index is None:
            cam_index = find_camera()
            if cam_index is None:
                print("Камера не найдена, повтор через 2 сек...")
                capture_stop.wait(2)
                continue
            print(f"Используется камера /dev/video{cam_index}")

        cap = cv2.VideoCapture(cam_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            print("Не удалось открыть камеру, повтор через 2 сек...")
            cam_index = None
            capture_stop.wait(2)
            continue

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        while not capture_stop.is_set():
            ret, frame = cap.read()  # read() сам ждёт следующий кадр, лишний sleep не нужен
            if not ret:
                print("Ошибка чтения кадра, переподключение...")
                break
            with frame_lock:
                current_frame = frame
        cap.release()
        with frame_lock:
            current_frame = None  # не показываем «замёрзший» кадр после отключения
        capture_stop.wait(1)
    print("Поток захвата остановлен")


capture_thread = threading.Thread(target=capture_loop, daemon=True)
capture_thread.start()


def get_last_frame():
    with frame_lock:
        if current_frame is not None:
            return current_frame.copy()
    return None


atexit.register(capture_stop.set)


def gen_frames():
    """Генератор MJPEG. Завершается сам, когда клиент отключился (GeneratorExit)."""
    idle = 0.0
    while True:
        frame = get_last_frame()
        if frame is None:
            time.sleep(0.05)
            idle += 0.05
            if idle > 30:  # камеры нет слишком долго: не держим поток впустую
                return
            continue
        idle = 0.0
        ok, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        if not ok:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.04)


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_stop')
def video_stop():
    # Оставлено для совместимости с фронтендом: поток останавливается при закрытии соединения.
    return jsonify({'status': 'ok'})


# ====== Описание сцены (AI) ======
task_queue = Queue(maxsize=5)
task_results = {}
results_lock = threading.Lock()


def set_result(task_id, **data):
    with results_lock:
        task_results[task_id] = dict(data, ts=time.time())


def prune_results():
    now = time.time()
    with results_lock:
        old = [k for k, v in task_results.items() if now - v.get('ts', now) > RESULT_TTL_SEC]
        for k in old:
            del task_results[k]


def ai_worker():
    while True:
        task_id, prompt, frame = task_queue.get()
        try:
            desc = robot.describe_scene(prompt=prompt, frame=frame)
            set_result(task_id, status='done', description=desc)
        except Exception as e:
            set_result(task_id, status='error', error=str(e))


threading.Thread(target=ai_worker, daemon=True).start()


@app.route('/api/describe_scene', methods=['POST'])
def api_describe_scene():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', 'Опиши, что ты видишь, на русском языке.')
    frame = get_last_frame()
    if frame is None:
        return jsonify({"error": "Нет кадра"}), 503
    prune_results()
    task_id = uuid.uuid4().hex[:8]
    set_result(task_id, status='pending')
    try:
        task_queue.put_nowait((task_id, prompt, frame))
    except Full:
        set_result(task_id, status='error', error='Очередь занята, попробуй позже')
        return jsonify({"error": "Очередь занята, попробуй позже"}), 429
    return jsonify({'task_id': task_id})


@app.route('/api/task_status/<task_id>')
def task_status(task_id):
    with results_lock:
        res = task_results.get(task_id)
    if not res:
        return jsonify({'status': 'unknown'})
    return jsonify({k: v for k, v in res.items() if k != 'ts'})


# ====== Распознавание речи ======
speech_active = threading.Event()
latest_speech_text = ""
speech_error = None
speech_lock = threading.Lock()
speech_start_lock = threading.Lock()
mic_lock = threading.Lock()  # микрофон одновременно: либо распознавание, либо запись
speech_thread = None


def continuous_speech_recognition():
    global latest_speech_text, speech_error
    try:
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
    except Exception as e:
        speech_error = f"Микрофон недоступен: {e}"
        print(speech_error)
        return
    speech_error = None

    while True:
        if not speech_active.is_set():
            time.sleep(0.5)
            continue
        try:
            with mic_lock:
                with mic as source:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
            text = recognizer.recognize_google(audio, language='ru-RU')
            with speech_lock:
                latest_speech_text = text
            time.sleep(0.2)
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            pass
        except sr.RequestError as e:
            print(f"Распознавание речи: нет связи с сервисом Google: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Распознавание речи: ошибка {e}")
            time.sleep(1)


def start_speech_thread():
    global speech_thread
    with speech_start_lock:
        if speech_thread is None or not speech_thread.is_alive():
            speech_thread = threading.Thread(target=continuous_speech_recognition, daemon=True)
            speech_thread.start()


@app.route('/api/toggle_speech', methods=['POST'])
def toggle_speech():
    data = request.get_json(silent=True) or {}
    active = bool(data.get('active', False))
    if active:
        if not SR_AVAILABLE:
            return jsonify({'status': 'error', 'error': 'Модуль speech_recognition не установлен'}), 503
        speech_active.set()
        start_speech_thread()
    else:
        speech_active.clear()
    return jsonify({'status': 'ok', 'active': active})


@app.route('/api/latest_speech')
def latest_speech():
    with speech_lock:
        return jsonify({'text': latest_speech_text, 'error': speech_error})


# ====== Аудио (запись, загрузка, воспроизведение) ======
@app.route('/api/record_audio', methods=['POST'])
def record_audio():
    data = request.get_json(silent=True) or {}
    try:
        duration = int(data.get('duration', 5))
    except (TypeError, ValueError):
        return jsonify({'error': 'duration должен быть числом'}), 400
    duration = max(1, min(duration, MAX_RECORD_SEC))

    filename = f"record_{int(time.time())}.mp3"
    filepath = os.path.join(STATIC_DIR, filename)

    was_active = speech_active.is_set()
    speech_active.clear()
    try:
        with mic_lock:  # ждём, пока распознавание отпустит микрофон
            with tempfile.TemporaryDirectory() as tmp:
                wav = os.path.join(tmp, "rec.wav")
                r = subprocess.run(
                    ["arecord", "-q", "-d", str(duration), "-f", "cd", "-t", "wav", wav],
                    capture_output=True, text=True, timeout=duration + 10)
                if r.returncode != 0:
                    return jsonify({'error': f'arecord: {r.stderr.strip()}'}), 500
                r = subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
                     "-codec:a", "libmp3lame", "-qscale:a", "2", filepath],
                    capture_output=True, text=True, timeout=60)
                if r.returncode != 0:
                    return jsonify({'error': f'ffmpeg: {r.stderr.strip()}'}), 500
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return jsonify({'error': f'Запись не удалась: {e}'}), 500
    finally:
        if was_active:
            speech_active.set()

    return jsonify({'status': 'ok', 'filename': filename, 'url': f'/static/{filename}'})


@app.route('/api/play_mp3', methods=['POST'])
def play_mp3():
    data = request.get_json(silent=True) or {}
    filename = os.path.basename(str(data.get('filename') or ''))  # без ../
    if not filename:
        return jsonify({'error': 'No filename'}), 400
    filepath = os.path.join(STATIC_DIR, filename)
    if not os.path.isfile(filepath):
        return jsonify({'error': 'File not found'}), 404
    try:
        robot.play_mp3(filepath)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'ok'})


@app.route('/api/upload_mp3', methods=['POST'])
def upload_mp3():
    file = request.files.get('file')
    if file is None:
        return jsonify({'error': 'No file part'}), 400
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.mp3'):
        return jsonify({'error': 'Разрешены только .mp3'}), 400
    file.save(os.path.join(STATIC_DIR, filename))
    return jsonify({'status': 'ok', 'filename': filename, 'url': f'/static/{filename}'})


@app.route('/static/<path:filename>')
def static_files(filename):
    # send_from_directory сам защищает от выхода за STATIC_DIR; photos/ и videos/ тоже тут
    return send_from_directory(STATIC_DIR, filename)


# ====== Движение ======
MOVES = {
    'forward': robot.forward,
    'backward': robot.backward,
    'left': robot.left,
    'right': robot.right,
    'rotate_left': robot.rotate_left,
    'rotate_right': robot.rotate_right,
}


@app.route('/api/move', methods=['POST'])
def api_move():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    cmd = data.get('cmd')
    try:
        speed = int(data.get('speed', 150))
    except (TypeError, ValueError):
        return jsonify({'error': 'speed должен быть числом'}), 400
    speed = max(0, min(255, speed))

    if cmd == 'stop':
        robot.stop()
    elif cmd in MOVES:
        MOVES[cmd](speed)
    else:
        return jsonify({'error': f'Неизвестная команда: {cmd}'}), 400
    return jsonify({'status': 'ok'})


# ====== Камера (сервоприводы) ======
CAMERA_ACTIONS = {
    'left': robot.camera_left,
    'right': robot.camera_right,
    'up': robot.camera_up,
    'down': robot.camera_down,
    'center': robot.camera_center,
}


@app.route('/api/camera', methods=['POST'])
def api_camera():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    action = CAMERA_ACTIONS.get(data.get('direction'))
    if action is None:
        return jsonify({'error': 'Неизвестное направление'}), 400
    action()
    return jsonify({'status': 'ok'})


# ====== RGB (эффекты и светодиоды) ======
@app.route('/api/rgb', methods=['POST'])
def api_rgb():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    if data.get('state', False):
        robot.rgb_color(data.get('color', 0))
    else:
        robot.rgb_off()
    return jsonify({'status': 'ok'})


@app.route('/api/rgb_effect', methods=['POST'])
def api_rgb_effect():
    data = request.get_json(silent=True) or {}
    effect = data.get('effect', 'starlight')
    speed = data.get('speed', 0.1)
    duration = data.get('duration', None)
    try:
        robot.rgb_effect(effect, duration=duration, speed=speed)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/rgb_off', methods=['POST'])
def api_rgb_off():
    robot.rgb_off()
    return jsonify({'status': 'ok'})


@app.route('/api/rgb_led', methods=['POST'])
def api_rgb_led():
    data = request.get_json(silent=True) or {}
    try:
        index = int(data.get('index', 1))  # 1-13
    except (TypeError, ValueError):
        return jsonify({'error': 'index должен быть числом'}), 400
    if not 1 <= index <= 13:
        return jsonify({'error': 'index вне диапазона 1-13'}), 400
    robot.rgb_led(index, data.get('color', -1))
    return jsonify({'status': 'ok'})


# ====== Бипер ======
@app.route('/api/beep', methods=['POST'])
def api_beep():
    data = request.get_json(silent=True) or {}
    if 'state' in data:
        robot.beep(data['state'])
    else:
        robot.beep_short()
    return jsonify({'status': 'ok'})


# ====== Ультразвук ======
@app.route('/api/ultrasonic')
def api_ultrasonic():
    try:
        return jsonify({'distance': robot.get_distance()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ====== Фото (сохраняется в галерею) ======
@app.route('/api/photo', methods=['POST'])
def api_photo():
    frame = get_last_frame()
    if frame is None:
        return jsonify({'status': 'error', 'message': 'No frame'}), 503
    name = f"photo_{int(time.time())}.jpg"
    if not cv2.imwrite(os.path.join(PHOTOS_DIR, name), frame):
        return jsonify({'status': 'error', 'message': 'Не удалось сохранить фото'}), 500
    return jsonify({'status': 'ok', 'filename': name, 'url': f'/static/photos/{name}'})


# ====== Голос (TTS) ======
@app.route('/api/say', methods=['POST'])
def api_say():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    text = data.get('text', '')
    if not text:
        return jsonify({'status': 'error', 'message': 'No text'}), 400
    try:
        robot.say(text)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    return jsonify({'status': 'ok'})


# ====== QR ======
@app.route('/api/qr', methods=['POST'])
def api_qr():
    frame = get_last_frame()
    if frame is None:
        return jsonify({'error': 'No frame'}), 503
    try:
        return jsonify({'qr': robot.detect_qr(frame) or None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ====== Статус ======
@app.route('/api/status')
def api_status():
    try:
        return jsonify({'ip': robot.get_ip(), 'cpu': robot.get_cpu(), 'ram': robot.get_ram()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ====== Запись видео ======
class VideoRecorder:
    """Writer создаётся, пишется и закрывается в одном потоке: гонок с release() нет."""

    def __init__(self):
        self._lock = threading.Lock()
        self._stop = None
        self._thread = None
        self._filename = None

    def _running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        with self._lock:
            if self._running():
                return None, 'Already recording'
            frame = get_last_frame()
            if frame is None:
                return None, 'No frame'
            height, width = frame.shape[:2]
            path = os.path.join(VIDEOS_DIR, f"video_{int(time.time())}.avi")
            writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'XVID'), VIDEO_FPS, (width, height))
            if not writer.isOpened():
                return None, 'Не удалось открыть VideoWriter'
            self._stop = threading.Event()
            self._filename = os.path.basename(path)
            self._thread = threading.Thread(
                target=self._run, args=(writer, self._stop, width, height), daemon=True)
            self._thread.start()
            return self._filename, None

    @staticmethod
    def _run(writer, stop, width, height):
        interval = 1.0 / VIDEO_FPS
        next_t = time.monotonic()
        try:
            while not stop.is_set():
                f = get_last_frame()
                if f is not None:
                    if f.shape[1] != width or f.shape[0] != height:
                        f = cv2.resize(f, (width, height))
                    writer.write(f)
                next_t += interval  # ровный темп, чтобы длительность видео совпадала с реальной
                delay = next_t - time.monotonic()
                if delay > 0:
                    stop.wait(delay)
                else:
                    next_t = time.monotonic()
        finally:
            writer.release()

    def stop(self):
        with self._lock:
            if not self._running():
                return None
            self._stop.set()
            self._thread.join(timeout=5)
            name = self._filename
            self._thread = self._stop = self._filename = None
            return name


recorder = VideoRecorder()
atexit.register(recorder.stop)


@app.route('/api/record_video_start', methods=['POST'])
def api_record_video_start():
    name, err = recorder.start()
    if err:
        return jsonify({'status': 'error', 'message': err}), 409
    return jsonify({'status': 'recording', 'filename': name})


@app.route('/api/record_video_stop', methods=['POST'])
def api_record_video_stop():
    name = recorder.stop()
    if name is None:
        return jsonify({'status': 'error', 'message': 'Not recording'}), 409
    return jsonify({'status': 'stopped', 'filename': name})


# ====== Галерея ======
@app.route('/api/gallery')
def api_gallery():
    files = []
    for folder, url_dir, type_label in [(PHOTOS_DIR, 'photos', 'image'),
                                        (VIDEOS_DIR, 'videos', 'video')]:
        for f in sorted(os.listdir(folder)):
            if os.path.isfile(os.path.join(folder, f)):
                files.append({'name': f, 'url': f'/static/{url_dir}/{f}', 'type': type_label})
    return jsonify({'files': files})


# ====== РЕДАКТОР КОДА (только с токеном) ======
@app.route('/api/files')
@require_token
def api_files():
    """Список файлов в папке внутри /home/pi."""
    base = safe_path(request.args.get('base', ROOT_DIR)) or ROOT_DIR
    items = []
    try:
        for entry in os.listdir(base):
            if entry.startswith('.'):
                continue
            full = os.path.join(base, entry)
            items.append({'name': entry, 'path': full,
                          'type': 'folder' if os.path.isdir(full) else 'file'})
    except OSError as e:
        return jsonify({'error': str(e)}), 500
    items.sort(key=lambda x: (x['type'] != 'folder', x['name']))
    return jsonify({'path': base, 'items': items})


@app.route('/api/file')
@require_token
def api_file_get():
    real = safe_path(request.args.get('path', ''))
    if real is None or not os.path.isfile(real):
        return jsonify({'error': 'Неверный путь'}), 404
    try:
        if os.path.getsize(real) > MAX_EDIT_FILE_BYTES:
            return jsonify({'error': 'Файл слишком большой для редактора'}), 413
        with open(real, 'r', encoding='utf-8') as f:
            return jsonify({'content': f.read(), 'path': real})
    except UnicodeDecodeError:
        return jsonify({'error': 'Файл не в UTF-8 (бинарный?)'}), 415
    except OSError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/save', methods=['POST'])
@require_token
def api_file_save():
    data = request.get_json(silent=True) or {}
    content = data.get('content', '')
    real = safe_path(data.get('path', ''))
    if real is None or not isinstance(content, str):
        return jsonify({'error': 'Неверный путь'}), 400
    if os.path.isdir(real) or not os.path.isdir(os.path.dirname(real)):
        return jsonify({'error': 'Неверный путь'}), 400
    try:
        with open(real, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({'status': 'ok'})
    except OSError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/command', methods=['POST'])
@require_token
def api_command():
    """Терминал (с таймаутом 10 с). Только с токеном: это полный доступ к Pi."""
    data = request.get_json(silent=True) or {}
    cmd = data.get('cmd', '')
    if not isinstance(cmd, str) or not cmd.strip():
        return jsonify({'output': ''})
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                timeout=10, cwd=ROOT_DIR)
        return jsonify({'output': result.stdout + result.stderr})
    except subprocess.TimeoutExpired:
        return jsonify({'output': 'Команда превысила время ожидания'})
    except Exception as e:
        return jsonify({'output': str(e)})


# ====== Страницы ======
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, "robot_web_html.html")  # читается с диска при каждом запросе


@app.route('/cod')
def code_editor():
    supplied = request.args.get('token')
    if supplied is not None:
        if hmac.compare_digest(supplied.encode(), TOKEN.encode()):
            resp = make_response(redirect(url_for('code_editor')))  # убираем токен из адресной строки
            resp.set_cookie('robot_token', TOKEN, httponly=True, samesite='Strict',
                            max_age=7 * 24 * 3600)
            return resp
        return "Неверный токен", 403
    if not token_ok():
        return "Нужен токен: откройте /cod?token=ВАШ_ТОКЕН", 401
    return send_from_directory(BASE_DIR, "code_editor.html")


if __name__ == '__main__':
    try:
        ip = robot.get_ip()
    except Exception:
        ip = "<ip робота>"
    print(f"Робот-сайт запущен на http://{ip}:{PORT}")
    if TOKEN_GENERATED:
        print(f"Токен сгенерирован на этот запуск (задай ROBOT_TOKEN, чтобы он был постоянным): {TOKEN}")
        print(f"Редактор: http://{ip}:{PORT}/cod?token={TOKEN}")
    else:
        print(f"Редактор: http://{ip}:{PORT}/cod?token=<ROBOT_TOKEN>")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
