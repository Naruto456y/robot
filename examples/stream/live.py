import subprocess
import time

def start_mjpg_streamer(port=6001, resolution="640x480", fps=60):
    cmd = [
        "mjpg_streamer",
        "-i", f"input_uvc.so -d /dev/video0 -r {resolution} -f {fps} -n",
        "-o", f"output_http.so -p {port} -w /usr/local/share/mjpg-streamer/www"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)  # даём время запуститься
    return proc

def stop_mjpg_streamer(proc):
    proc.terminate()
    proc.wait()