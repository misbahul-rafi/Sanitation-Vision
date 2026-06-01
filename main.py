from modules import Camera, Notifier, Resmon, SanitationManager, SystemAPI, Table
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
        
        self.app = FastAPI(lifespan=self._lifespan)
        
        self._camera_indoor = os.getenv("SOURCE_CAMERA_INDOOR")
        self._camera_outdoor = os.getenv("SOURCE_CAMERA_OUTDOOR")
        self._app_host = os.getenv("APP_HOST")
        self._app_port = int(os.getenv("APP_PORT"))
        self._logger_stream = os.getenv("LOGGER_STREAM") == "true"
        
        self._shutdown_event = asyncio.Event()
        
        self._cameras = self._create_cameras()
        self._notifier = Notifier()
        self._resmon = Resmon()
        self.manager = SanitationManager(
            self._notifier,
            self._cameras,
        )
        self.system_api = SystemAPI(
            shutdown_is_set=self._shutdown_event.is_set,
            cameras=self._cameras,
            get_resmon=self._resmon.snapshot,
            manager_status = self.manager.get_manager_status,
            send_daily_report = self.manager.send_daily_report
        )
        self._setup_routes()
        self._setup_cors()
        self._logger = self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger("SanitationVision")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")
            file_handler = logging.FileHandler("logs/sanitation.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            if self._logger_stream:
                stream_handler = logging.StreamHandler()
                stream_handler.setFormatter(formatter)
                logger.addHandler(stream_handler)
        return logger

    def _create_cameras(self):
        return [
                Camera("indoor", self._camera_indoor, [
                Table(1, [283, 172, 450, 358]),
                Table(2, [95, 413, 314, 656]),
                Table(3, [100, 661, 441, 1077]),
                Table(4, [490, 311, 908, 823]),
            ]),
                Camera("outdoor", self._camera_outdoor, [
                Table(5, [102, 618, 402, 1035]),
                Table(6, [408, 328, 580, 596]),
                Table(7, [670, 396, 845, 786]),
                Table(8, [551, 203, 674, 331]),
                Table(9, [743, 224, 885, 394]),
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
        self._camera_tasks = []
        for cam in self._cameras:
            task = asyncio.create_task(cam.stream(self._shutdown_event))
            self._camera_tasks.append(task)

        manager_task = asyncio.create_task(
            self.manager.run(self._shutdown_event)
        )

        resmon_task = asyncio.create_task(
            self._resmon.run(self._shutdown_event)
        )
        yield
        self._shutdown_event.set()
        await self._notifier.stop()
        # for camera in self._cameras:
        #     await camera.stop()
        await asyncio.gather(
            *self._camera_tasks,
            manager_task,
            resmon_task,
            return_exceptions=True
        )
        
sanitation_app = SanitationApp()
app = sanitation_app.app
if __name__ == "__main__":
    uvicorn.run(app, host=sanitation_app._app_host, port=sanitation_app._app_port, access_log=False)