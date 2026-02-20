import logging
from telegram import Bot
from telegram.error import TelegramError
from io import BytesIO
from config import Config

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Synchronous Telegram notifier - best practice for scheduled tasks."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern - ensure single bot instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if TelegramNotifier._initialized:
            return
            
        self.config = Config()
        self.bot = None
        self.chat_id = None
        
        if self.config.TELEGRAM_BOT_TOKEN and self.config.TELEGRAM_BOT_TOKEN != "YOUR_TELEGRAM_BOT_TOKEN":
            self.bot = Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            self.chat_id = self.config.TELEGRAM_CHAT_ID
            logger.info("Telegram bot initialized.")
        else:
            logger.warning("Telegram bot token not configured.")
        
        TelegramNotifier._initialized = True
    
    def is_enabled(self) -> bool:
        """Check if bot is properly configured."""
        return self.bot is not None and self.chat_id is not None
    
    def send_message(self, text: str) -> bool:
        """Send text message synchronously."""
        if not self.is_enabled():
            logger.debug("Telegram not enabled, skipping message.")
            return False
        
        try:
            # Split long messages
            max_length = 4096
            if len(text) > max_length:
                for i in range(0, len(text), max_length):
                    part = text[i:i + max_length]
                    self.bot.send_message(chat_id=self.chat_id, text=part)
            else:
                self.bot.send_message(chat_id=self.chat_id, text=text)
            
            logger.info("Telegram message sent.")
            return True
            
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    def send_photo(self, photo_bytes: bytes, caption: str = "") -> bool:
        """Send photo synchronously."""
        if not self.is_enabled():
            return False
        
        try:
            photo = BytesIO(photo_bytes)
            self.bot.send_photo(
                chat_id=self.chat_id,
                photo=photo,
                caption=caption[:1024]
            )
            logger.info("Telegram photo sent.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return False
    
    def send_document(self, file_bytes: bytes, filename: str = "file.html", caption: str = "") -> bool:
        """Send document synchronously."""
        if not self.is_enabled():
            return False
        
        try:
            document = BytesIO(file_bytes)
            document.name = filename
            self.bot.send_document(
                chat_id=self.chat_id,
                document=document,
                caption=caption[:1024]
            )
            logger.info("Telegram document sent.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            return False


# ==================== Module-level convenience functions ====================

_notifier = None

def _get_notifier() -> TelegramNotifier:
    """Get or create notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier

def send_sync_message(text: str) -> bool:
    """Send message (convenience function)."""
    return _get_notifier().send_message(text)

def send_sync_photo(photo_bytes: bytes, caption: str = "") -> bool:
    """Send photo (convenience function)."""
    return _get_notifier().send_photo(photo_bytes, caption)

def send_sync_document(file_bytes: bytes, filename: str = "file.html", caption: str = "") -> bool:
    """Send document (convenience function)."""
    return _get_notifier().send_document(file_bytes, filename, caption)

def test_connection() -> bool:
    """Test Telegram connection."""
    notifier = _get_notifier()
    if not notifier.is_enabled():
        logger.error("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return False
    
    success = notifier.send_message("🤖 Bot connection test successful!")
    if success:
        logger.info("✅ Telegram connection test passed.")
    else:
        logger.error("❌ Telegram connection test failed.")
    return success


if __name__ == "__main__":
    # Test when run directly
    test_connection()
