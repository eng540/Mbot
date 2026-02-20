import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config import Config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self):
        self.config = Config()
        if not self.config.TELEGRAM_BOT_TOKEN or self.config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
            logger.warning("Telegram bot token not configured. Telegram notifications will be disabled.")
            self.bot = None
        else:
            self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)

    async def _send_message(self, text: str):
        if not self.bot:
            return
        try:
            await self.bot.send_message(chat_id=self.config.TELEGRAM_CHAT_ID, text=text)
            logger.info("Telegram message sent.")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def _send_photo(self, photo_bytes: bytes, caption: str = ""):
        if not self.bot:
            return
        try:
            await self.bot.send_photo(chat_id=self.config.TELEGRAM_CHAT_ID, photo=photo_bytes, caption=caption)
            logger.info("Telegram photo sent.")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram photo: {e}")

    async def _send_document(self, document_bytes: bytes, filename: str, caption: str = ""):
        if not self.bot:
            return
        try:
            await self.bot.send_document(chat_id=self.config.TELEGRAM_CHAT_ID, document=document_bytes, filename=filename, caption=caption)
            logger.info(f"Telegram document '{filename}' sent.")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram document: {e}")

# For synchronous use in scheduler
def send_sync_message(text: str):
    notifier = TelegramNotifier()
    if notifier.bot:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(notifier._send_message(text))
            else:
                loop.run_until_complete(notifier._send_message(text))
        except Exception as e:
            logger.error(f"Error in send_sync_message: {e}")

def send_sync_photo(photo_bytes: bytes, caption: str = ""):
    notifier = TelegramNotifier()
    if notifier.bot:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(notifier._send_photo(photo_bytes, caption))
            else:
                loop.run_until_complete(notifier._send_photo(photo_bytes, caption))
        except Exception as e:
            logger.error(f"Error in send_sync_photo: {e}")

def send_sync_document(document_bytes: bytes, filename: str, caption: str = ""):
    notifier = TelegramNotifier()
    if notifier.bot:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(notifier._send_document(document_bytes, filename, caption))
            else:
                loop.run_until_complete(notifier._send_document(document_bytes, filename, caption))
        except Exception as e:
            logger.error(f"Error in send_sync_document: {e}")
