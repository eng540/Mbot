import os

class Config:
    # --- General Settings ---
    HEADLESS = os.getenv("HEADLESS", "True").lower() == "true"  # Run browser in headless mode (True for production)
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true" # Set to True to enable more verbose logging and screenshots

    # --- Target Embassy Settings ---
    # Use a single URL for the target embassy, configurable via environment variable
    TARGET_URL = os.getenv("TARGET_URL", "https://service2.diplo.de/rktermin/extern/appointment_showMonth.do?request_locale=en&locationCode=mask&realmId=354&categoryId=1638&")
    CATEGORY_ID = os.getenv("CATEGORY_ID", "1638") # Category ID for the target visa type

    # --- User Data ---
    LAST_NAME = os.getenv("LAST_NAME", "AL-kiHI")
    FIRST_NAME = os.getenv("FIRST_NAME", "Taratst")
    EMAIL = os.getenv("EMAIL", "waffaron@gmail.com")
    PHONE = os.getenv("PHONE", "00967777123488")
    PASSPORT = os.getenv("PASSPORT", "2490087")
    PURPOSE = os.getenv("PURPOSE", "Student Visa") # This should match the text in the dropdown

    # --- Telegram Bot Settings ---
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

    # --- Scheduling Settings ---
    # Regular check: every hour
    REGULAR_CHECK_CRON = os.getenv("REGULAR_CHECK_CRON", "0 * * * *") # Every hour at minute 0

    # Intensive check: 2 AM Aden time (GMT+3). For a 30-minute window.
    # Aden 2 AM is 23:00 GMT (previous day). So, 23:00-23:30 GMT.
    # Cron format: minute hour day_of_month month day_of_week
    INTENSIVE_CHECK_CRON = os.getenv("INTENSIVE_CHECK_CRON", "0-30 23 * * *") # Every minute from 23:00 to 23:30 GMT

    # --- Captcha Settings ---
    CAPTCHA_RETRY_LIMIT = int(os.getenv("CAPTCHA_RETRY_LIMIT", "3")) # Max attempts to solve captcha
    CAPTCHA_SOLVER_TIMEOUT = int(os.getenv("CAPTCHA_SOLVER_TIMEOUT", "10")) # Seconds to wait for captcha solution

    # --- Playwright Settings ---
    USER_AGENT = os.getenv("USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    VIEWPORT_WIDTH = int(os.getenv("VIEWPORT_WIDTH", "1280"))
    VIEWPORT_HEIGHT = int(os.getenv("VIEWPORT_HEIGHT", "800"))

    # --- Delay Settings (to mimic human behavior) ---
    MIN_DELAY = int(os.getenv("MIN_DELAY", "1")) # Minimum delay in seconds
    MAX_DELAY = int(os.getenv("MAX_DELAY", "3")) # Maximum delay in seconds

    # --- Error Handling ---
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5")) # Max retries for network errors or server issues
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5")) # Delay between retries in seconds
