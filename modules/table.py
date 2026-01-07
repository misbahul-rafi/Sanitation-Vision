import time
from collections import Counter
import logging

dirty_object = ["gelas", "piring", "asbak", "botol"]

logger = logging.getLogger("SanitationVision")

class Table:
    def __init__(self, table_id, area, items=None):
        try:
            if not isinstance(area, (list, tuple)) or len(area) != 4:
                raise ValueError(f"invalid area format for table {table_id}: {area}")

            self._id = table_id
            self._area = area
            self._status = "used"
            self._status_buffer = ["used"] * 6
            self._start_time = None
            self._last_alert = None
            self._items = items if isinstance(items, list) else []

            logger.info(f"Table {self._id} initialized with area={self._area}")

        except Exception as e:
            logger.critical(f"failed initializing Table {table_id}: {e}")
            raise

    def get_table_data(self):
        return {
            "id": self._id,
            "area": self._area,
            "status": self._status,
            "status_buffer": list(self._status_buffer),
            "start_time": self._start_time,
            "last_alert": self._last_alert,
            "items": list(self._items),
        }

    def get_id(self):
        return self._id
    
    def get_area(self):
        return self._area

    def get_status(self):
        return self._status

    def get_start_time(self):
        return self._start_time

    def get_last_alert(self):
        return self._last_alert

    def set_start_time(self):
        self._start_time = time.time()
        logger.debug(f"table {self._id} start_time set")

    def set_last_alert(self):
        self._last_alert = time.time()
        logger.debug(f"table {self._id} last_alert set")

    def insert_items(self, item_name):
        try:
            self._items.append(item_name)
        except Exception as e:
            logger.error(f"failed inserting item into table {self._id}: {e}")

    def clear_items(self):
        self._items = []
        
    def get_status_buffer(self):
        return self._status_buffer

    def update_status(self):
        try:
            has_customer = "pelanggan" in self._items
            has_dirty = any(obj in self._items for obj in dirty_object)
            if has_customer:
                current_status = "used"
            elif has_dirty:
                current_status = "dirty"
            else:
                current_status = "clean"

            self._status_buffer.append(current_status)
            if len(self._status_buffer) > 6:
                self._status_buffer.pop(0)

            if not self._status_buffer:
                logger.warning(f"table {self._id} status buffer empty, skipping update")
                return

            counts = Counter(self._status_buffer)
            new_status = counts.most_common(1)[0][0]

            if new_status != self._status:
                logger.info(
                    f"table {self._id} status changed from {self._status} to {new_status}"
                )
                self._status = new_status
                return True

        except Exception as e:
            logger.error(f"failed updating status table {self._id}: {e}")

        return False

    def reset_time(self):
        self._start_time = None
        self._last_alert = None

    def contains_point(self, x, y):
        try:
            x1, y1, x2, y2 = self._area
            inside = x1 <= x <= x2 and y1 <= y <= y2
            return inside
        except Exception as e:
            logger.error(f"failed checking point containment table {self._id}: {e}")
            return False
