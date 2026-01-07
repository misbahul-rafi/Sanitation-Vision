from .camera import Camera
from .notifier import Notifier
from .yolo_model import YOLOModel
import asyncio
import time
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

load_dotenv()
open_hour = int(os.getenv("OPEN_HOUR", 10))
close_hour = int(os.getenv("CLOSE_HOUR", 24))
predict_interval = int(os.getenv("PREDICT_INTERVAL", 10))
alert_interval = int(os.getenv("ALERT_INTERVAL", 10))
logger = logging.getLogger("SanitationVision")

class SanitationManager:
    def __init__(
        self,
        notifier: Notifier,
        cameras: list[Camera],
        predict,
        status=True,
    ):
        self.notifier = notifier
        self.cameras = cameras
        self.status = status
        self.predict = predict

    def system_off(self, duration):
        if duration:
            self.status = False

    def stop(self):
        self.status = False

    async def run(self):
        logger.info("SanitationVision started")
        while True:
            if open_hour <= datetime.now().hour <= close_hour and self.status:
                logger.info("starting predic...")
                for camera in self.cameras:
                    camera_name = camera.get_name()
                    if camera.get_status():
                        image = camera.get_snapshot()
                        if image is None:
                            continue
                        objects = self.predict(
                            image=image, set_annotated=camera.set_annotated
                        )
                        
                        camera.set_is_update(True)
                        camera.group_items_in_table(objects)
                        for table in camera.get_tables():
                            table.update_status()
                            if table.get_status() == "dirty":
                                if table.get_start_time() != None:
                                    if time.time() - table.get_last_alert() > alert_interval:
                                        table.set_last_alert()
                                        logger.info(f'send alert for table {table.get_id()}')
                                        await self.notifier.send_alert(
                                            table_id=table.get_id(),
                                            camera_name=camera_name,
                                            time_dirtied=1,
                                            image=camera.get_annotated(),
                                        )
                                    else:
                                        continue
                                else:
                                    logger.info(f'area {camera_name} table {table.get_id()} set time')
                                    table.set_start_time()
                                    table.set_last_alert()
                                    logger.debug(f'area {camera_name} table {table.get_id()} start_time and last_alert is setted')
                                    logger.info(f"{camera_name} table {table.get_id()} is {table.get_status()} for {time.time() - table.get_start_time()} second")
                                    await self.notifier.send_alert(
                                        table_id=table.get_id(),
                                        camera_name=camera_name,
                                        image=camera.get_annotated(),
                                        time_dirtied=round(
                                            (time.time() - table.get_start_time()) / 60
                                        ),
                                    )     
                            else:
                                logger.debug(f'{table.get_id()} = {table.get_status()}')
                                table.reset_time()
                    else:
                        logger.info(f'camera {camera_name} is terminated')
                await asyncio.sleep(predict_interval)
            else:
                logger.info("SanitationManager stopped")
                await asyncio.sleep(60)
