from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()
base_dir = os.getenv("BASE_DIR")

templates = Jinja2Templates(directory=f"{base_dir}/templates")

app.mount("/static", StaticFiles(directory=f'{base_dir}/static/images'), name="static")

CURRENT_STATUS = {
    "indoor": "clean",
    "outdoor": "clean"
}


import asyncio
from fastapi import Request


async def fake_stream(camera: str, request: Request):

    while True:

        if await request.is_disconnected():
            print(f"{camera} disconnected")
            break

        status = CURRENT_STATUS[camera]

        image_path = os.path.join(
            base_dir,
            "static",
            "images",
            f"{camera}-{status}.jpg"
        )

        with open(image_path, "rb") as image:
            frame = image.read()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame +
            b"\r\n"
        )

        await asyncio.sleep(1)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Sanitation Control",
            "status": CURRENT_STATUS
        }
    )


@app.get("/set/{camera}/{value}")
async def set_status(camera: str, value: str):

    if camera in CURRENT_STATUS:
        CURRENT_STATUS[camera] = value

    return RedirectResponse("/", status_code=303)


@app.get("/stream/{camera}")
async def stream(camera: str, request: Request):

    return StreamingResponse(
        fake_stream(camera, request),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
    
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
    )