import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from config import Config
from sniper_engine import SniperEngine
from telegram_bot import send_sync_message

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

def check_and_book(embassy_name: str):
    """فحص وحجز موعد."""
    logger.info(f"Starting appointment check for {embassy_name}...")
    send_sync_message(f"🔍 Starting check for {embassy_name}")
    
    sniper = SniperEngine()
    try:
        if sniper.run():
            message = f"✅ Appointment booked successfully for {embassy_name}!"
            logger.info(message)
            send_sync_message(message)
        else:
            message = f"❌ No appointments found or booking failed for {embassy_name}."
            logger.info(message)
            send_sync_message(message)
    except Exception as e:
        message = f"⚠️ Error during {embassy_name} check: {e}"
        logger.error(message)
        send_sync_message(message)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    
    # ✅ تشغيل فوري عند الإقلاع
    logger.info("🚀 Running immediate check on startup...")
    check_and_book("Muscat")
    
    # ✅ التجدولة كل ساعة
    scheduler.add_job(
        check_and_book,
        CronTrigger.from_crontab(Config.REGULAR_CHECK_CRON),
        args=["Muscat"],
        id="muscat_regular_check"
    )
    logger.info(f"Scheduled regular check: {Config.REGULAR_CHECK_CRON}")

    scheduler.add_job(
        check_and_book,
        CronTrigger.from_crontab(Config.INTENSIVE_CHECK_CRON),
        args=["Muscat (Intensive)"],
        id="muscat_intensive_check"
    )
    logger.info(f"Scheduled intensive check: {Config.INTENSIVE_CHECK_CRON}")

    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
