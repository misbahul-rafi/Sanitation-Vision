from telegram.ext import ApplicationBuilder
import cv2
import logging
import os
import traceback

logger = logging.getLogger("SanitationVision")

class Notifier:
    def __init__(self):
        self._bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self._chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.app = ApplicationBuilder().token(self._bot_token).build()
        self._initialized = False

        async def error_handler(update, context):
            logger.error("Telegram internal error occurred", exc_info=context.error)

        self.app.add_error_handler(error_handler)

    async def initialize(self):
        try:
            logger.info("Initializing Telegram notifier")
            await self.app.initialize()
            await self.app.start()
            self._initialized = True
            logger.info("Telegram notifier successfully initialized")
        except Exception as e:
            logger.critical(f"Gagal initialize Telegram Notifier: {e}")
            self._initialized = False

    async def stop(self):
        try:
            if not self._initialized:
                logger.warning("Notifier stop called but notifier not initialized")
                return

            await self.app.stop()
            await self.app.shutdown()
            self._initialized = False
            logger.info("Notifier berhasil dihentikan")
        except Exception as e:
            logger.error(f"Gagal menghentikan notifier: {e}")

    async def send_message(self, message):
        if not self._initialized:
            logger.warning("send_message dipanggil tapi notifier belum initialized")
            return
        try:
            await self.app.bot.send_message(chat_id=self._chat_id, text=message)
            logger.info(f"Pesan berhasil dikirim.")
        except Exception as e:
            logger.error(f"Gagal mengirim pesan: {e}")

    async def send_alert(self, table_id, camera_name, time_dirtied, image=None):
        if not self._initialized:
            logger.warning("notifier is'n initialize")
            return

        try:
            caption = (
                f"Area {camera_name} Meja no. {table_id} "
                f"terdeteksi belum dibersihkan selama {time_dirtied} menit"
            )

            if image is None:
                logger.warning(f"Tidak ada image untuk alert table {table_id}, mengirim pesan teks saja")
                await self.send_message(caption)
                return

            success, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 10])
            if not success:
                logger.error("Gagal mengencode image untuk dikirim ke Telegram")
                await self.send_message(caption + " (tanpa gambar karena error encode)")
                return

            bytes_image = buffer.tobytes()

            await self.app.bot.send_photo(
                chat_id=self._chat_id,
                photo=bytes_image,
                caption=caption
            )

            logger.debug(f"Alert terkirim untuk table {table_id} di camera {camera_name}")

        except Exception as e:
            logger.error(f"Error saat mengirim alert Telegram: {e}")
