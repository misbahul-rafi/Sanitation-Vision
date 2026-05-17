import time, os, csv
from collections import Counter, deque
import logging
from datetime import datetime

logger = logging.getLogger("SanitationVision")

class Table:
    def __init__(self, table_id, area, items=None):
        try:
            if not isinstance(area, (list, tuple)) or len(area) != 4:
                raise ValueError(f"invalid area format for table {table_id}: {area}")
            self._id = table_id
            self._area = area
            self._status = "used"
            self._status_buffer = deque(["used"] * 6, maxlen=6)
            self._start_time = None
            self._last_alert = None
            self._items = items if isinstance(items, list) else []
            self._daily_records = []
            self._base_dir = os.getenv("BASE_DIR")
            self._log_path = os.path.join(self._base_dir, "logs")
            os.makedirs(self._log_path, exist_ok=True)
            self._history_path = os.path.join(self._log_path, "history.csv")
            if not os.path.exists(self._history_path):
                with open(self._history_path, "w", newline="", encoding="utf-8") as f:
                    fieldnames = ["table_id", "start_time", "clean_time", "duration_seconds"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
            logger.info(f"Table {self._id} initialized with area={self._area}")
        except Exception as e:
            logger.critical(f"failed initializing Table {table_id}: {e}")
            raise
    def get_id(self):
        return self._id
    def get_area(self):
        return self._area
    def get_status(self):
        return self._status
    def get_status_buffer(self):
        return self._status_buffer
    def get_start_time(self):
        return self._start_time
    def set_start_time(self, now):
        self._start_time = now
    def get_last_alert(self):
        return self._last_alert
    def set_last_alert(self, now):
        self._last_alert = now
    def clear_data(self):
        self._status = "clean"
        self._status_buffer = ["clean"] * 6
        self._daily_records = []
        self.clear_items()
        self.reset_time()
    def get_daily_record(self):
        return self._daily_records

    def convert_time(self, datetime_format):
        return datetime.fromisoformat(datetime_format).strftime("%H:%M:%S")

    def get_table_data(self):
        return {
            "id": self._id,
            "status": self._status,
        }
    def insert_items(self, item_name):
        try:
            self._items.append(item_name)
        except Exception as e:
            logger.error(f"failed inserting item into table {self._id}: {e}")

    def clear_items(self):
        self._items = []
    def reset_time(self):
        self._start_time = None
        self._last_alert = None
        
    def insert_record(self):
        try:
            if(self._start_time is None):
                return
            now = time.time()
            record = {
                "table_id": self._id,
                "start_time": datetime.fromtimestamp(self._start_time).isoformat(),
                "clean_time": datetime.fromtimestamp(now).isoformat(),
                "duration_seconds": round(now - self._start_time)
            }
            self._daily_records.append(record)
            with open(self._history_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["table_id","start_time","clean_time","duration_seconds"])
                writer.writerow(record)
            logger.info(f"Inserted Table {self._id} record into CSV: {self._history_path}")
        except Exception as e:
            logger.error(f"Gagal insert CSV untuk Table {self._id}: {e}")
    def generate_report_message(self):
        message = f"Meja {self._id}\n"
        if not self._daily_records:
            message += "- Tidak ada aktivitas\n"
        for record in self._daily_records:
            message += f"- Mulai: {self.convert_time(record['start_time'])} - {self.convert_time(record['clean_time'])} = {record['duration_seconds'] / 60:.1f}menit\n"
        self.clear_data()
        return message

    def update_status(self):
        dirty_object = ["gelas", "piring", "asbak", "botol"]
        customer_object = ["pelanggan", "handphone", "laptop"]
        try:
                current_status = ""
                has_customer = any(obj in self._items for obj in customer_object)
                has_dirty = any(obj in self._items for obj in dirty_object)
                if has_customer:
                    current_status = "used"
                elif has_dirty:
                    current_status = "dirty"
                else:
                    current_status = "clean"
                self._status_buffer.append(current_status)
                counts = Counter(self._status_buffer)
                final_status = counts.most_common(1)[0][0]
                if final_status != self._status and final_status != "dirty":
                    self.insert_record()
                self._status = final_status
                return current_status, self._status
        except Exception as e:
                logger.error(f"failed updating status table {self._id}: {e}")

    def contains_point(self, x, y):
        try:
            x1, y1, x2, y2 = self._area
            inside = x1 <= x <= x2 and y1 <= y <= y2
            return inside
        except Exception as e:
            logger.error(f"failed checking point containment table {self._id}: {e}")
            return False