from modules import Camera, ColorFormatter, Notifier, Resmon, SanitationManager, SystemAPI, Table
import logging
import os
import asyncio
from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

class SanitationApp:
    def __init__(self):
        load_dotenv()
        self._shutdown_event = asyncio.Event()
        self._logger = self._setup_logger()
        
        self._camera_indoor = os.getenv("SOURCE_CAMERA_INDOOR")
        self._camera_outdoor = os.getenv("SOURCE_CAMERA_OUTDOOR")
        self._app_host = os.getenv("APP_HOST")
        self._app_port = int(os.getenv("APP_PORT"))


        self._cameras = self._create_cameras()
        self._notifier = Notifier()
        self._resmon = Resmon()

        self.manager = SanitationManager(
            self._notifier,
            self._cameras,
            status=True,
            
        )

        self.system_api = SystemAPI(
            shutdown_is_set=self._shutdown_event.is_set,
            cameras=self._cameras,
            get_resmon=self._resmon.snapshot,
            manager_status = self.manager.get_manager_status
        )

        self.app = FastAPI(lifespan=self._lifespan)
        self._setup_routes()
        self._setup_cors()

    def _setup_logger(self):
        logger = logging.getLogger("SanitationVision")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(ColorFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(handler)
            file_handler = logging.FileHandler("logs/sanitation.log", encoding="utf-8")
            file_handler.setFormatter(ColorFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(file_handler)
        return logger


    def _create_cameras(self):
        return [
            Camera("indoor", self._camera_indoor, [
            Table(1, [272, 145, 465, 430]),
            Table(2, [1, 204, 319, 689]),
            Table(3, [536, 317, 960, 959]),
            Table(4, [1, 620, 495, 1080]),
        ]),
            Camera("outdoor", self._camera_outdoor, [
            Table(7, [1, 558, 442, 1063]),
            Table(8, [385, 206, 665, 552]),
            Table(9, [665, 255, 955, 787]),
        ]),
        ]

    def _setup_routes(self):
        self.app.include_router(self.system_api.router)

    def _setup_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        await self._notifier.initialize()
        manager_task = asyncio.create_task(
            self.manager.run(self._shutdown_event)
        )
        resmon_task = asyncio.create_task(
            self._resmon.run(self._shutdown_event)
        )
        yield
        self._shutdown_event.set()
        await self._notifier.stop()
        await asyncio.gather(
            manager_task,
            resmon_task,
            return_exceptions=True
        )
        
sanitation_app = SanitationApp()
app = sanitation_app.app
if __name__ == "__main__":
    uvicorn.run(app, host=sanitation_app._app_host, port=sanitation_app._app_port)