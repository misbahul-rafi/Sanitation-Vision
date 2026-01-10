from .camera import Camera
from .notifier import Notifier
from .yolo_model import YOLOModel
import asyncio
import time
from datetime import datetime
import os
import logging


logger = logging.getLogger("SanitationVision")


class SanitationManager:
    def __init__(
        self,
        notifier: Notifier,
        cameras: list[Camera],
        status=True,
    ):
        self.notifier = notifier
        self.cameras = cameras
        self._status = status
        self._model = YOLOModel()

        self._open_hour = datetime.strptime(os.getenv("OPEN_HOUR"), "%H:%M").time()
        self._close_hour = datetime.strptime(os.getenv("CLOSE_HOUR"), "%H:%M").time()
        self._predict_interval = int(os.getenv("PREDICT_INTERVAL", 10))
        self._alert_interval = int(os.getenv("ALERT_INTERVAL", 10))
        self._base_dir = os.getenv("BASE_DIR")

    def get_manager_status(self):
        return self._status

    async def _is_operational_time(self):
        if self._open_hour <= datetime.now().time() <= self._close_hour:
            self._status = True
        else:
            if self._status:
                message = f"=====Daily Report=====\n"
                message += f"Date: {datetime.now().strftime("%d-%b-%Y")}\n\n"
                for camera in self.cameras:
                    message += camera.daily_report()
                await self.notifier.send_message(message)
                self._status = False
        return self._status

    async def run(self, shutdown_event: asyncio.Event):
        logger.info("SanitationVision started")
        while not shutdown_event.is_set():
            start_loop = time.time()
            if await self._is_operational_time():
                for camera in self.cameras:
                    camera_name = camera.get_name()
                    if camera.get_status():
                        image = camera.get_snapshot()
                        if image is None:
                            continue
                        objects = self._model.predict(
                            image=image, set_annotated=camera.set_annotated
                        )
                        camera.set_is_update(True)
                        camera.group_items_in_table(objects)
                        for table in camera.get_tables():
                            table.update_status()
                            if table.get_status() == "dirty":
                                if table.get_start_time() != None:
                                    if (
                                        time.time() - table.get_last_alert()
                                        > self._alert_interval
                                    ):
                                        table.set_last_alert()
                                        logger.info(
                                            f"send alert for table {table.get_id()}"
                                        )
                                        await self.notifier.send_alert(
                                            table_id=table.get_id(),
                                            camera_name=camera_name,
                                            time_dirtied=round(
                                                (time.time() - table.get_start_time())
                                                / 60
                                            ),
                                            image=camera.get_annotated(),
                                        )
                                    else:
                                        continue
                                else:
                                    logger.info(
                                        f"area {camera_name} table {table.get_id()} set time"
                                    )
                                    table.set_start_time()
                                    table.set_last_alert()
                                    logger.debug(
                                        f"area {camera_name} table {table.get_id()} start_time and last_alert is setted"
                                    )
                                    logger.info(
                                        f"{camera_name} table {table.get_id()} is {table.get_status()} for {time.time() - table.get_start_time()} second"
                                    )
                                    await self.notifier.send_alert(
                                        table_id=table.get_id(),
                                        camera_name=camera_name,
                                        image=camera.get_annotated(),
                                        time_dirtied=1,
                                    )
                            else:
                                logger.debug(f"{table.get_id()} = {table.get_status()}")
                                table.reset_time()
                    else:
                        logger.info(f"camera {camera_name} is terminated")
                logger.info(f"Time for 1 loop = {time.time() - start_loop}")
                await asyncio.sleep(self._predict_interval)
            else:
                logger.info("SanitationManager stopped")
                await asyncio.sleep(60)
