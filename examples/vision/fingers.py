#!/usr/bin/env python3
import cv2
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False,
                       max_num_hands=1,
                       min_detection_confidence=0.7,
                       min_tracking_confidence=0.5)

mp_draw = mp.solutions.drawing_utils

def count_fingers(landmarks, side_label):
    """Подсчёт поднятых пальцев для одной руки"""
    fingers = []
    # Большой палец (отдельно)
    if side_label == "Right":
        if landmarks[4].x > landmarks[3].x:
            fingers.append(1)
        else:
            fingers.append(0)
    else:  # Left
        if landmarks[4].x < landmarks[3].x:
            fingers.append(1)
        else:
            fingers.append(0)
    # Остальные 4 пальца
    for tip, base in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        if landmarks[tip].y < landmarks[base].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return sum(fingers)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Камера не доступна")
    exit(1)

print("🖐️ Покажите руку в кадр. Нажмите Ctrl+C для выхода.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)
        if result.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks,
                                                  result.multi_handedness):
                # Определяем сторону
                side = handedness.classification[0].label  # "Left" или "Right"
                # Считаем пальцы
                count = count_fingers(hand_landmarks.landmark, side)
                print(f"✋ {side} рука: {count} пальцев")
                # Рисуем разметку на кадре (без GUI, только для сохранения)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                # Добавляем текст с числом
                cv2.putText(frame, f"Fingers: {count}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                # Сохраняем фото при обнаружении
                cv2.imwrite("/home/pi/gesture_last.jpg", frame)
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\n👋 Завершено")
finally:
    cap.release()
    print("🏁 Камера освобождена")