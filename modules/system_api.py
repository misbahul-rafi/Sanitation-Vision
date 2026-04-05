from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse, Response, JSONResponse
import asyncio
import json
import cv2
import logging
import time
import os
from .camera import Camera

logger = logging.getLogger("SanitationVision")
predict_interval = int(os.getenv("PREDICT_INTERVAL", 10))

class SystemAPI:
    def __init__(
        self,
        shutdown_is_set,
        get_resmon,
        cameras: list[Camera],
        manager_status
    ):
        logger.debug("Inisialisasi SystemAPI")
        self.router = APIRouter()
        self._cameras = cameras
        self.shutdown_is_set = shutdown_is_set
        self.get_resmon = get_resmon
        self._manager_status = manager_status
        self._setup_routes()

        
    def _get_camera_by_name(self, camera_name: str) -> Camera | None:
        logger.debug(f"Mencari kamera dengan nama: {camera_name}")
        for camera in self._cameras:
            if camera.get_name() == camera_name:
                logger.debug(f"Kamera ditemukan: {camera_name}")
                return camera
        logger.warning(f"Kamera {camera_name} tidak ditemukan")
        return None

    def _setup_routes(self):
        @self.router.get("/stream")
        async def stream():
            logger.info("Client connected to endpoint /stream")
            async def events():
                try:
                    while not self.shutdown_is_set():
                        try:
                            payload = {
                                "system": self.get_resmon(),
                                "manager": self._manager_status(),
                                "cameras": [camera.get_camera_data() for camera in self._cameras]
                            }
                            logger.debug("Sending SSE update to client")
                            yield f"data: {json.dumps(payload)}\n\n"

                            for camera in self._cameras:
                                if camera.get_is_update():
                                    camera.set_is_update(False)
                                    
                        except Exception as e:
                            logger.error(f"Error during loop SSE: {e}")
                            yield "event: error\ndata: internal error\n\n"
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    logger.info("SSE connection canceled by client")
                    return
            return StreamingResponse(events(), media_type="text/event-stream")

        @self.router.get("/camera/{camera_name}")
        async def get_camera_image(camera_name: str):
            logger.debug(f"Request image camera: {camera_name}")
            camera = self._get_camera_by_name(camera_name)
            if not camera:
                logger.warning(f"Request image failed. camera {camera_name} not found")
                raise HTTPException(status_code=404, detail=f"Camera '{camera_name}' not found")
            annotated = camera.get_annotated()
            if annotated is None:
                logger.warning(f"Image kamera {camera_name} belum siap")
                raise HTTPException(status_code=404, detail="Image not ready")
            try:
                success, buffer = cv2.imencode(".jpg", annotated)
                if not success:
                    logger.error(f"Gagal encode image kamera {camera_name}")
                    raise HTTPException(status_code=500, detail="Failed to encode image")
            except Exception as e:
                logger.error(f"Exception saat encoding image kamera {camera_name}: {e}")
                raise HTTPException(status_code=500, detail="Image processing error")
            logger.debug(f"Berhasil mengembalikan image kamera {camera_name}")
            return Response(
                content=buffer.tobytes(),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Pragma": "no-cache",
                    "Expires": "0",
                }
            )
            
        @self.router.get("/camera/control/status/{camera_name}")
        def get_camera_control(camera_name: str, action: bool):
            camera = self._get_camera_by_name(camera_name)
            if camera:
                camera.set_camera_status(action)
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "camera": camera_name,
                        "action": action,
                        "status": "success"
                    }
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera '{camera_name}' not found"
            )
            
        @self.router.get("/camera/control/draw/{camera_name}")
        def get_camera_draw(camera_name: str, action: bool):
            camera = self._get_camera_by_name(camera_name)
            if camera:
                camera.set_is_draw(action)
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "camera": camera_name,
                        "action": action,
                        "status": "success"
                    }
                )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera '{camera_name}' not found"
            )
            