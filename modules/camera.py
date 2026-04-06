import cv2, asyncio, logging, numpy as np
from .table import Table
from collections import Counter

logger = logging.getLogger("SanitationVision")

class Camera:
    def __init__(self, name, source, tables: list[Table]):
        self._name = name
        self._source = source
        self._status = True
        self._is_update = False
        self._is_draw = False
        self._last_frame = None
        self._cap = None
        self._annotated = None
        self._tables = tables
        self._lock = asyncio.Lock()
        
    def get_name(self):
        return self._name
    def get_status(self):
        return self._status
    def set_camera_status(self, action):
        self._status = action
    def get_is_update(self):
        return self._is_update
    def set_is_update(self, value):
        self._is_update = value
    def set_is_draw(self, value):
        self._is_draw = value    
    def get_tables(self):
        return self._tables
    def get_annotated(self):
        return self._annotated
    def set_annotated(self, image):
        try:
            logger.debug(f"resizing annotated image for camera {self._name}")
            if self._is_draw:
                self.draw_area(image)
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
    
    
    async def stream(self, shutdown_event: asyncio.Event):
        logger.info(f"RTSP stream started for camera {self._name}")
        retry_delay = 2
        max_failures = 10
        while not shutdown_event.is_set():
            logger.info(f"Opening RTSP stream for camera {self._name}")
            self._cap = cv2.VideoCapture(self._source, cv2.CAP_FFMPEG)
            if not self._cap.isOpened():
                logger.error(f"Failed to open RTSP stream {self._name}, retrying...")
                self._cap.release()
                await asyncio.sleep(retry_delay)
                continue
            failure_count = 0
            while not shutdown_event.is_set():
                ret, frame = await asyncio.to_thread(self._cap.read)
                if not ret or frame is None:
                    failure_count += 1
                    logger.warning(
                        f"Failed to read frame from {self._name} "
                        f"({failure_count}/{max_failures})"
                    )
                    if failure_count >= max_failures:
                        logger.error(
                            f"RTSP stream unstable for {self._name}, reconnecting..."
                        )
                        break
                    await asyncio.sleep(0.05)
                    continue
                failure_count = 0
                self._last_frame = frame
                for _ in range(3):
                    await asyncio.to_thread(self._cap.grab)
            self._cap.release()
            logger.info(f"RTSP stream released for camera {self._name}")
            await asyncio.sleep(retry_delay)
        if self._cap:
            self._cap.release()
        logger.info(f"RTSP stream stopped for camera {self._name}")
        
        
    def get_snapshot(self):
        try:
            logger.debug(f"getting frame from stream for camera {self._name}")
            if self._last_frame is None:
                logger.error(f"frame is not available yet for camera {self._name}")
                return None
            if not isinstance(self._last_frame, np.ndarray):
                logger.error(f"invalid frame type for camera {self._name}")
                return None
            if self._last_frame.size == 0:
                logger.error(f"frame is empty or corrupted for camera {self._name}")
                return None
            frame = self._last_frame.copy()
            return frame
        except Exception as e:
            logger.error(f"unexpected error getting frame from {self._name}: {e}")
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
    def get_camera_data(self):
        return {
            "name": self._name,
            "status": self._status,
            "is_update": self._is_update,
            "status_counts": self.get_status_count(),
            "tables": [table.get_table_data() for table in self._tables],
        }
        
    async def start(self):
        """Buka koneksi RTSP satu kali"""
        if self._cap is None:
            logger.info(f"Opening RTSP stream for {self._name}")
            self._cap = cv2.VideoCapture(self._source, cv2.CAP_FFMPEG)
            if not self._cap.isOpened():
                raise RuntimeError(f"Cannot open RTSP stream {self._name}")
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info(f"Camera {self._name} initiallized")
            
            
    async def stop(self):
        """Tutup koneksi RTSP saat shutdown"""
        if self._cap:
            self._cap.release()
            self._cap = None
            logger.info(f"RTSP stream closed for {self._name}")
            
    async def get_frame(self):
        """Ambil frame baru saat dibutuhkan"""
        if self._cap is None:
            raise RuntimeError(f"Camera {self._name} is not started")
        async with self._lock:  # pastikan thread-safe
            ret, frame = await asyncio.to_thread(self._cap.read)
            if not ret or frame is None:
                logger.warning(f"Failed to read frame from {self._name}")
                return None
            return frame