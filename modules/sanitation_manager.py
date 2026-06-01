from .camera import Camera
from .notifier import Notifier
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
    ):
        self.notifier = notifier
        self.cameras = cameras
        self._status = False

        self._open_hour = datetime.strptime(os.getenv("OPEN_HOUR"), "%H:%M").time()
        self._close_hour = datetime.strptime(os.getenv("CLOSE_HOUR"), "%H:%M").time()
        self._predict_interval = int(os.getenv("PREDICT_INTERVAL", 10))
        self._alert_interval = int(os.getenv("ALERT_INTERVAL", 10))
        self._base_dir = os.getenv("BASE_DIR")

    def get_manager_status(self):
        return self._status
    
    async def send_daily_report(self):
        for camera in self.cameras:
            for table in camera.get_tables():
                if table.get_start_time() is not None:
                    logger.info(
                        f"finalizing table {table.get_id()} before daily report"
                    )
                    table.insert_record()
                    table.reset_time()

        message = "=====Daily Report=====\n"
        message += f"Date: {datetime.now().strftime('%d-%b-%Y')}\n\n"

        for camera in self.cameras:
            message += camera.daily_report()

        await self.notifier.send_message(message)

    async def _is_operational_time(self):
        if self._open_hour <= datetime.now().time() <= self._close_hour:
            self._status = True
        else:
            if self._status:
                await self._send_daily_report()
                self._status = False
        return self._status
    
    def _time_now(self):
        return time.time()
    
    async def handle_table(self, table, camera_name, get_annotated, now):
        current_status, buffer_status = table.update_status()
        start_time = table.get_start_time()
        last_alert = table.get_last_alert()
        match(current_status, buffer_status):
            case("dirty", "dirty"):
                if start_time != None:
                    if (now - last_alert > self._alert_interval):
                        table.set_last_alert(now)
                        logger.info(
                            f"send alert for table {table.get_id()}"
                        )
                        await self.notifier.send_alert(
                            table_id=table.get_id(),
                            camera_name=camera_name,
                            time_dirtied=round(
                                (now - table.get_start_time())
                                / 60
                            ),
                            image=get_annotated(),
                        )
                else:
                    logger.info(f"area {camera_name} table {table.get_id()} set time")
                    table.set_start_time(now)
                    table.set_last_alert(now)
                    logger.debug(f"area {camera_name} table {table.get_id()} start_time and last_alert is setted")
                    logger.info(f"{camera_name} table {table.get_id()} is {table.get_status()} for {time.time() - table.get_start_time()} second")
                    await self.notifier.send_alert(
                        table_id=table.get_id(),
                        camera_name=camera_name,
                        image=get_annotated(),
                        time_dirtied=1,)
            case(_, "dirty"):
                return
            case _:
                table.reset_time()

    async def run(self, shutdown_event: asyncio.Event):
        logger.info("SanitationVision started")
        while not shutdown_event.is_set():
            start_loop = self._time_now()
            if await self._is_operational_time():
                for camera in self.cameras:
                    camera_name = camera.get_name()
                    if camera.get_status():
                        image = camera.get_snapshot()
                        if image is None:
                            continue
                        objects = camera.predict(image, camera.set_annotated)
                        end_predict = self._time_now()
                        camera.set_is_update(True)
                        camera.group_items_in_table(objects)
                        for table in camera.get_tables():
                            await self.handle_table(table=table, camera_name=camera_name, get_annotated=camera.get_annotated,
                            now=end_predict
                            )
                    else:
                        logger.info(f"camera {camera_name} is terminated")
                logger.info(f"Time count in this loop = {self._time_now() - start_loop}")
                await asyncio.sleep(self._predict_interval)
            else:
                logger.info("SanitationManager stopped")
                await asyncio.sleep(60)
