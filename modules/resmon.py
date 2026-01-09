import psutil, asyncio, time, os, csv, datetime
from typing import Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class Resmon:
    def __init__(self, disk_path: str = "/"):
        self._base_dir = os.getenv("BASE_DIR")
        self._interval : float = float(os.getenv("RESMON_INTERVAL"))
        self.disk_path = disk_path
        self._latest: Dict[str, Any] = {}
        self._csv_path = os.path.join(self._base_dir, "logs", "resmon.csv")

        logger.debug(f"Memulai Resmon dengan interval={self._interval} dan disk_path={disk_path}")
        try:
            os.makedirs(os.path.dirname(self._csv_path), exist_ok=True)
            logger.debug(f"Direktori logging resmon dipastikan ada: {self._csv_path}")
        except Exception as e:
            logger.error(f"Gagal membuat direktori log Resmon: {e}")

        self.init_csv()
        
    def init_csv(self):
        try:
            with open(self._csv_path, "x", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "cpu", "memory", "disk", "temperature"])
            logger.info("File CSV Resmon berhasil dibuat")
        except FileExistsError:
            logger.debug("File CSV Resmon sudah ada, tidak perlu membuat baru")
        except Exception as e:
            logger.error(f"Gagal inisialisasi file CSV Resmon: {e}")
    
    def save_resmon(self):
        try:
            with open(self._csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.datetime.now().isoformat(),
                    self._latest.get("cpu", {}).get("percent"),
                    self._latest.get("memory", {}).get("percent"),
                    self._latest.get("disk", {}).get("percent"),
                    self._latest.get("temperature", {}).get("temperature")
                ])
            logger.debug("Berhasil menyimpan data resmon ke CSV")
        except Exception as e:
            logger.error(f"Gagal menyimpan data Resmon ke CSV: {e}")
        
    async def run(self, shutdown_event: asyncio.Event):
        logger.info("Resmon mulai berjalan")
        while not shutdown_event.is_set():
            try:
                cpu_temp = None
                if hasattr(psutil, "sensors_temperatures"):
                    try:
                        temps = psutil.sensors_temperatures()
                        if temps and "cpu_thermal" in temps:
                            cpu_temp = temps["cpu_thermal"][0].current
                    except Exception as e:
                        logger.warning(f"Gagal membaca temperature CPU: {e}")

                try:
                    cpu_percent = round(psutil.cpu_percent(interval=.5, percpu=False), 1)
                except Exception as e:
                    logger.error(f"Gagal membaca CPU usage: {e}")
                    cpu_percent = None

                try:
                    mem = psutil.virtual_memory()
                except Exception as e:
                    logger.error(f"Gagal membaca Memory usage: {e}")
                    mem = None

                try:
                    disk = psutil.disk_usage(self.disk_path)
                except Exception as e:
                    logger.error(f"Gagal membaca Disk usage: {e}")
                    disk = None

                self._latest = {
                    "cpu": {
                        "percent": cpu_percent
                    },
                    "memory": {
                        "percent": mem.percent if mem else None,
                        "used": round(mem.used / 1024 / 1024) if mem else None,
                        "total": round(mem.total / 1024 / 1024) if mem else None
                    },
                    "disk": {
                        "percent": disk.percent if disk else None,
                        "used": round(disk.used / 1024 / 1024) if disk else None,
                        "total": round(disk.total / 1024 / 1024) if disk else None
                    },
                    "temperature": {
                        "temperature": cpu_temp
                    },
                    "timestamp": time.time()
                }

                logger.debug(f"Update resmon terbaru: {self._latest}")
                self.save_resmon()

            except Exception as e:
                logger.error(f"Terjadi error fatal di loop Resmon: {e}")

            await asyncio.sleep(self._interval)

        logger.info("Resmon dihentikan")

    def snapshot(self) -> Dict[str, Any]:
        logger.debug("Snapshot Resmon diminta")
        return self._latest
