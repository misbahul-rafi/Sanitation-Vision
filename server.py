from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import time
import uvicorn

IMAGE_PATHS = {
    "indoor": r"C:/Users/MisbahulRafi/Desktop/SanitationVision/ignoregit/testimages/indoor-4-dirty.jpg",
    "outdoor": r"C:/Users/MisbahulRafi/Desktop/SanitationVision/ignoregit/testimages/outdoor-1.jpg"
}

app = FastAPI()
def fake_stream(image_path):
    with open(image_path, "rb") as f:
        frame = f.read()

    while True:
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
        time.sleep(0.1)

@app.get("/stream/indoor")
def stream_indoor():
    return StreamingResponse(
        fake_stream(IMAGE_PATHS["indoor"]),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.get("/stream/outdoor")
def stream_outdoor():
    return StreamingResponse(
        fake_stream(IMAGE_PATHS["outdoor"]),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=9000,
        reload=True
    )