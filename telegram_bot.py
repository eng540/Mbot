import logging
from telegram import Bot
from telegram.error import TelegramError
from io import BytesIO
from config import Config

logger = logging.getLogger(__name__)

# Singleton instance
_bot_instance = None
_chat_id = None

def _get_bot():
    """Get or create bot instance."""
    global _bot_instance, _chat_id
    if _bot_instance is None:
        config = Config()
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN":
            _bot_instance = Bot(token=config.TELEGRAM_BOT_TOKEN)
            _chat_id = config.TELEGRAM_CHAT_ID
            logger.info("Telegram bot initialized.")
        else:
            logger.warning("Telegram bot token not configured.")
    return _bot_instance, _chat_id

def send_sync_message(text: str):
    """Send message synchronously."""
    bot, chat_id = _get_bot()
    if not bot:
        return
    
    try:
        max_length = 4096
        if len(text) > max_length:
            for i in range(0, len(text), max_length):
                bot.send_message(chat_id=chat_id, text=text[i:i+max_length])
        else:
            bot.send_message(chat_id=chat_id, text=text)
        logger.info("Telegram message sent.")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")

def send_sync_photo(photo_bytes: bytes, caption: str = ""):
    """Send photo synchronously."""
    bot, chat_id = _get_bot()
    if not bot:
        return
    
    try:
        photo = BytesIO(photo_bytes)
        bot.send_photo(chat_id=chat_id, photo=photo, caption=caption[:1024])
        logger.info("Telegram photo sent.")
    except Exception as e:
        logger.error(f"Failed to send photo: {e}")

def send_sync_document(file_bytes: bytes, filename: str = "file.html", caption: str = ""):
    """Send document synchronously."""
    bot, chat_id = _get_bot()
    if not bot:
        return
    
    try:
        document = BytesIO(file_bytes)
        document.name = filename
        bot.send_document(chat_id=chat_id, document=document, caption=caption[:1024])
        logger.info("Telegram document sent.")
    except Exception as e:
        logger.error(f"Failed to send document: {e}")
