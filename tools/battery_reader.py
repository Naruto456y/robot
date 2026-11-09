#!/usr/bin/env python3
import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 921600, timeout=1)

while True:
    header = ser.read(2)
    if len(header) < 2:
        continue
    if header[0] == 0xAA and header[1] == 0x55:
        length_byte = ser.read(1)
        if not length_byte:
            continue
        length = length_byte[0]
        packet = ser.read(length - 2)
        if len(packet) == length - 2:
            print(f"Пакет длина {length}:")
            print(packet.hex())
            # Если пакет достаточно длинный, пробуем извлечь напряжение
            if length >= 7:
                # Пробуем разные смещения
                for offset in [3, 4, 5, 6]:
                    v_raw = packet[offset] | (packet[offset+1] << 8)
                    v = v_raw / 1000.0
                    print(f"  offset {offset}: {v:.2f} В")
    time.sleep(0.01)