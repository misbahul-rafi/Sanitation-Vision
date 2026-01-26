import cv2
import os
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

IMAGE_DIR = "images"
DISPLAY_DURATION = 30  # detik per gambar
FPS = 10               # fps stream (beban ringan)

app = FastAPI()

image_files = sorted([
    os.path.join(IMAGE_DIR, f)
    for f in os.listdir(IMAGE_DIR)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
])

if not image_files:
    raise RuntimeError("Folder images kosong")

def generate_frames():
    while True:
        for image_path in image_files:
            frame = cv2.imread(image_path)
            if frame is None:
                continue

            start_time = time.time()

            while time.time() - start_time < DISPLAY_DURATION:
                ret, buffer = cv2.imencode(".jpg", frame)
                if not ret:
                    break

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + buffer.tobytes()
                    + b"\r\n"
                )

                time.sleep(1 / FPS)

@app.get("/stream")
def stream():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
