import subprocess
import threading
from datetime import datetime
import time
import os
import signal
import logging
import select

# =========================
# GLOBAL CONTROL
# =========================
stop_event = threading.Event()

def handle_signal(signum, frame):
    logging.info(f"Received signal {signum}, stopping...")
    stop_event.set()

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

# =========================
# LOGGING SETUP
# =========================
LOG_FILE = "/home/sanitation/uji-fps/fps-monitor.log"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# =========================
# CORE FUNCTION
# =========================
def run_ffmpeg(name, url, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # create header if file not exist
    if not os.path.exists(output_file):
        with open(output_file, "w") as f:
            f.write("camera,timestamp,out_time,fps\n")

    while not stop_event.is_set():
        logging.info(f"{name}: starting ffmpeg")

        cmd = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", url,
            "-f", "null",
            "-",
            "-progress", "pipe:1",
            "-nostats"
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        current = {}
        last_progress_time = time.time()

        try:
            with open(output_file, "a") as f:

                while not stop_event.is_set():
                    # NON-BLOCKING READ (anti hang)
                    reads = [process.stdout]
                    readable, _, _ = select.select(reads, [], [], 1)

                    if readable:
                        line = process.stdout.readline().strip()

                        if "=" in line:
                            key, value = line.split("=", 1)
                            current[key] = value

                            if key == "progress":
                                last_progress_time = time.time()

                                if "out_time" in current and "fps" in current:
                                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    f.write(f"{name},{now},{current['out_time']},{current['fps']}\n")
                                    f.flush()

                                current = {}

                    # WATCHDOG: kalau tidak ada progress 10 detik → restart
                    if time.time() - last_progress_time > 10:
                        logging.warning(f"{name}: no progress >10s, restarting ffmpeg")
                        break

                    # kalau process mati sendiri
                    if process.poll() is not None:
                        logging.warning(f"{name}: ffmpeg exited with code {process.returncode}")
                        break

        finally:
            # kill ffmpeg cleanly
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

            # log stderr (penting untuk debugging)
            try:
                err = process.stderr.read()
                if err:
                    logging.error(f"{name} stderr:\n{err.strip()}")
            except Exception:
                pass

        if not stop_event.is_set():
            logging.info(f"{name}: restarting in 3s...")
            time.sleep(3)

    logging.info(f"{name}: stopped")

# =========================
# CAMERA CONFIG
# =========================
cam1 = "rtsp://admin:admin12345@192.168.100.254:554/cam/realmonitor?channel=1&subtype=0"
cam2 = "rtsp://admin:admin12345@192.168.100.254:554/cam/realmonitor?channel=2&subtype=0"

# =========================
# THREAD START
# =========================
t1 = threading.Thread(target=run_ffmpeg, args=("cam1", cam1, "/home/sanitation/uji-fps/fps_cam1.csv"))
t2 = threading.Thread(target=run_ffmpeg, args=("cam2", cam2, "/home/sanitation/uji-fps/fps_cam2.csv"))

t1.start()
t2.start()

# wait threads
t1.join()
t2.join()

logging.info("All threads stopped. Exiting...")