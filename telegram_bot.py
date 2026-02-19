import logging
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

    async def send_message(self, text: str):
        if not self.bot:
            return
        try:
            await self.bot.send_message(chat_id=self.config.TELEGRAM_CHAT_ID, text=text)
            logger.info("Telegram message sent.")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")

    async def send_photo(self, photo_bytes: bytes, caption: str = ""):
        if not self.bot:
            return
        try:
            await self.bot.send_photo(chat_id=self.config.TELEGRAM_CHAT_ID, photo=photo_bytes, caption=caption)
            logger.info("Telegram photo sent.")
        except TelegramError as e:
            logger.error(f"Failed to send Telegram photo: {e}")

# For synchronous use in scheduler
def send_sync_message(text: str):
    import asyncio
    notifier = TelegramNotifier()
    if notifier.bot:
        asyncio.run(notifier.send_message(text))

def send_sync_photo(photo_bytes: bytes, caption: str = ""):
    import asyncio
    notifier = TelegramNotifier()
    if notifier.bot:
        asyncio.run(notifier.send_photo(photo_bytes, caption))
