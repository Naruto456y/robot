#!/usr/bin/env python3
import cv2
import http.server
import socketserver
import threading
import time

# Глобальная переменная для последнего кадра
current_frame = None
cap = cv2.VideoCapture(0)

def capture_frames():
    global current_frame
    while True:
        ret, frame = cap.read()
        if ret:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                current_frame = jpeg.tobytes()
        time.sleep(0.05)  # ~20 fps

class MJPEGHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global current_frame
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            while True:
                if current_frame is not None:
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(b'Content-Length: ' + str(len(current_frame)).encode() + b'\r\n\r\n')
                    self.wfile.write(current_frame + b'\r\n')
                time.sleep(0.05)
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    threading.Thread(target=capture_frames, daemon=True).start()
    with socketserver.TCPServer(('0.0.0.0', 6001), MJPEGHandler) as httpd:
        print("MJPEG сервер запущен на порту 6001")
        httpd.serve_forever()