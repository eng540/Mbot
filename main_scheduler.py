import logging
import time  # ✅ تم الإضافة
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from config import Config
from sniper_engine import SniperEngine
from telegram_bot import send_sync_message, send_sync_photo

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Embassy configurations


def check_and_book(embassy_name: str):
    logger.info(f"Starting appointment check for {embassy_name}...")
    sniper = SniperEngine()
    try:
        if sniper.run():
            message = f"✅ Appointment booked successfully for {embassy_name}!"
            logger.info(message)
            send_sync_message(message)
            # Optionally, stop scheduler after successful booking
            # scheduler.shutdown()
        else:
            message = f"❌ No appointments found or booking failed for {embassy_name}."
            logger.info(message)
            send_sync_message(message)
    except Exception as e:
        message = f"⚠️ An error occurred during {embassy_name} check: {e}"
        logger.error(message)
        send_sync_message(message)

if __name__ == "__main__":
    scheduler = BackgroundScheduler()

    # Regular hourly check for Muscat
    scheduler.add_job(
        check_and_book,
        CronTrigger.from_crontab(Config.REGULAR_CHECK_CRON),
        args=["Muscat"],
        id="muscat_regular_check"
    )
    logger.info(f"Scheduled Muscat regular check: {Config.REGULAR_CHECK_CRON}")

    # Intensive check for Muscat (2 AM Aden time / 23:00 GMT)
    scheduler.add_job(
        check_and_book,
        CronTrigger.from_crontab(Config.INTENSIVE_CHECK_CRON),
        args=["Muscat (Intensive)"],
        id="muscat_intensive_check"
    )
    logger.info(f"Scheduled Muscat intensive check: {Config.INTENSIVE_CHECK_CRON}")

    # Regular hourly check for Cairo (example, can be enabled/disabled)
    # scheduler.add_job(
    #     check_and_book,
    #     CronTrigger.from_crontab(Config.REGULAR_CHECK_CRON),
    #     args=["Cairo"],
    #     id="cairo_regular_check"
    # )
    # logger.info(f"Scheduled Cairo regular check: {Config.REGULAR_CHECK_CRON}")

    scheduler.start()
    logger.info("Scheduler started. Press Ctrl+C to exit.")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(2)  # ✅ الآن يعمل بدون خطأ
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shut down.")
