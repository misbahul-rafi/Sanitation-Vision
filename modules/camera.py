import cv2
import requests
import numpy as np
from .table import Table
import logging
from collections import Counter
import json

logger = logging.getLogger("SanitationVision")


class Camera:
    def __init__(self, name, source, tables: list[Table]):
        self._name = name
        self._tables = tables
        self._source = source
        self._annotated = None
        self._status = True
        self._is_update = False

    def get_camera_data(self):
        return {
            "name": self._name,
            "status": self._status,
            "is_update": self._is_update,
            "status_counts": self.get_status_count(),
            "tables": [table.get_table_data() for table in self._tables],
        }

    def set_is_update(self, value):
        self._is_update = value

    def get_is_update(self):
        return self._is_update

    def get_name(self):
        return self._name
    
    def set_camera_status(self, action):
        self._status = action

    def get_status(self):
        return self._status
    
    def draw_area(self, image):
        try:
            for table in self._tables:
                x1, y1, x2, y2 = table.get_area()

                status = table.get_status()
                if status == "clean":
                    color = (0, 255, 0)
                elif status == "dirty":
                    color = (0, 0, 255)
                else:
                    color = (0, 255, 255)

                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)

                label = f"Table {table.get_id()} [{status}]"
                cv2.putText(
                    image,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                    cv2.LINE_AA,
                )
        except Exception as e:
            logger.error(f"failed drawing table areas on {self._name}: {e}")


    def set_annotated(self, image):
        try:
            logger.debug(f"resizing annotated image for camera {self._name}")
            # self.draw_area(image)
            target_width = 800
            h, w = image.shape[:2]

            if w > target_width:
                scale = target_width / w
                new_size = (int(w * scale), int(h * scale))
                image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

            self._annotated = image

        except Exception as e:
            logger.error(f"failed to process annotated image on {self._name}: {e}")
            self._annotated = None

    def get_annotated(self):
        return self._annotated

    def get_tables(self):
        return self._tables

    def get_snapshot(self):
        try:
            logger.debug(f"taking snapshot from camera {self._name}")
            response = requests.get(
                self._source, timeout=5, headers={"Cache-Control": "no-cache"}
            )

            if response.status_code != 200:
                logger.error(
                    f"failed to take snapshot in Camera {self._name}: "
                    f"HTTP {response.status_code} URL={self._source}"
                )
                return None

            if not response.content or len(response.content) < 50:
                logger.error(
                    f"snapshot content is empty or corrupted for camera {self._name}"
                )
                return None

            try:
                img_array = np.frombuffer(response.content, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            except Exception as e:
                logger.error(
                    f"OpenCV failed decoding image for camera {self._name}: {e}"
                )
                return None

            if img is None:
                logger.error(f"decoded image is None for camera {self._name}")
                return None

            return img

        except requests.exceptions.Timeout:
            logger.error(f"snapshot timeout for camera {self._name}")
            return None

        except requests.exceptions.ConnectionError:
            logger.error(f"connection error while accessing camera {self._name}\n{self._source}")
            return None

        except Exception as e:
            logger.error(f"unexpected error getting snapshot from {self._name}: {e}")
            return None

    def group_items_in_table(self, objects):
        try:
            logger.debug(f"grouping items in camera {self._name}")
            for table in self._tables:
                table.clear_items()

            if objects is None or not hasattr(objects, "boxes"):
                logger.warning(f"YOLO result invalid or empty for camera {self._name}")
                return
            

            if objects.boxes is None or len(objects.boxes) == 0:
                logger.debug(f"no detection found on camera {self._name}")
                return


            for box, cls in zip(objects.boxes.xyxy, objects.boxes.cls):
                try:
                    x1, y1, x2, y2 = box.cpu().numpy()
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2

                    item_name = (
                        objects.names[int(cls)]
                        if hasattr(objects, "names")
                        else str(int(cls))
                    )

                    for table in self._tables:
                        if table.contains_point(cx, cy):
                            table.insert_items(item_name)

                except Exception as e:
                    logger.error(
                        f"failed processing detection box on camera {self._name}: {e}"
                    )
                    continue

        except Exception as e:
            logger.critical(f"fatal error grouping items on camera {self._name}: {e}")


    def get_status_count(self):
        status_list = [table.get_status() for table in self._tables]
        counts = Counter(status_list)
        all_status = ["clean", "used", "dirty"]
        status_counts = {status: counts.get(status, 0) for status in all_status}

        return status_counts
    
    def daily_report(self):
        message = ""
        for table in self._tables:
            message += table.generate_report_message()
        return message