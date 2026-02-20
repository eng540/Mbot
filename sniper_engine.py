import time
import random
import logging
from playwright.sync_api import sync_playwright, Page
from config import Config
from captcha_solver import CaptchaSolver
from telegram_bot import send_sync_message, send_sync_photo, send_sync_document

logger = logging.getLogger(__name__)

class SniperEngine:
    def __init__(self):
        self.config = Config()
        self.captcha_solver = CaptchaSolver()

    def _send_status(self, message: str, screenshot: bool = False, page: Page = None):
        """إرسال حالة إلى Telegram"""
        logger.info(message)
        send_sync_message(f"🤖 {message}")
        
        if screenshot and page:
            try:
                img = page.screenshot(full_page=True, timeout=10000)
                send_sync_photo(img, f"📸 {message[:50]}")
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")

    def _human_like_delay(self, min_d=None, max_d=None):
        min_delay = min_d or self.config.MIN_DELAY
        max_delay = max_d or self.config.MAX_DELAY
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        return delay

    def _solve_and_submit_captcha(self, page: Page, img_selector: str, input_selector: str, submit_selector: str, step_name: str) -> bool:
        """حل الكابتشا مع إشعارات Telegram"""
        self._send_status(f"🔒 {step_name}: Starting captcha solve", screenshot=True, page=page)
        
        for attempt in range(1, self.config.CAPTCHA_RETRY_LIMIT + 1):
            self._send_status(f"🔒 Attempt {attempt}/{self.config.CAPTCHA_RETRY_LIMIT}")
            
            captcha_text = self.captcha_solver.solve_captcha(page, img_selector)
            self._send_status(f"📝 OCR result: '{captcha_text}'")
            
            if not captcha_text:
                self._send_status("❌ OCR failed", screenshot=True, page=page)
                self._human_like_delay(2, 4)
                continue

            try:
                page.fill(input_selector, captcha_text)
                self._human_like_delay(0.5, 1.5)
                page.click(submit_selector)
                self._human_like_delay(2, 4)
            except Exception as e:
                self._send_status(f"❌ Error submitting: {e}", screenshot=True, page=page)
                continue

            page_content = page.content()
            if "Please enter here the text you see in the picture above" not in page_content:
                self._send_status(f"✅ Captcha solved! Entered: '{captcha_text}'", screenshot=True, page=page)
                return True
            else:
                self._send_status(f"❌ Wrong captcha: '{captcha_text}', retrying...", screenshot=True, page=page)

        self._send_status("🚨 All captcha attempts failed", screenshot=True, page=page)
        return False

    def run(self) -> bool:
        with sync_playwright() as p:
            browser = None
            try:
                self._send_status("🚀 Starting browser...")
                browser = p.chromium.launch(
                    headless=self.config.HEADLESS,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
                )
                
                context = browser.new_context(
                    viewport={'width': self.config.VIEWPORT_WIDTH, 'height': self.config.VIEWPORT_HEIGHT},
                    user_agent=self.config.USER_AGENT
                )
                page = context.new_page()
                
                # ✅ إصلاح: wait_until='load' بدلاً من 'networkidle'
                self._send_status(f"🌐 Opening: {self.config.TARGET_URL[:60]}...")
                try:
                    page.goto(self.config.TARGET_URL, timeout=120000, wait_until='load')
                    self._send_status("✅ Page loaded", screenshot=True, page=page)
                except Exception as e:
                    self._send_status(f"❌ Failed to load: {str(e)[:100]}")
                    # ✅ محاولة ثانية بدون screenshot
                    try:
                        page.goto(self.config.TARGET_URL, timeout=60000, wait_until='domcontentloaded')
                        self._send_status("✅ Page loaded (fallback)", screenshot=True, page=page)
                    except:
                        return False

                self._human_like_delay(5, 8)  # ✅ انتظار أطول

                # كابتشا أولى
                if not self._solve_and_submit_captcha(
                    page, 
                    'img[src*="captcha"]', 
                    'input[id*="captchaText"]', 
                    'input[id*="appointment_showMonth"]',
                    "Step 1: Initial Captcha"
                ):
                    return False

                # باقي الخطوات...
                self._send_status("🔍 Checking availability...", screenshot=True, page=page)
                
                if "Unfortunately, there are no appointments available" in page.content():
                    self._send_status("📭 No appointments available", screenshot=True, page=page)
                    return False

                self._send_status("🎯 Appointments might be available!", screenshot=True, page=page)

                # ... (باقي الكود كما هو)

                return False  # مؤقتاً حتى نختبر الموقع

            except Exception as e:
                self._send_status(f"💥 ERROR: {str(e)[:200]}")
                return False
                
            finally:
                if browser:
                    browser.close()
                    self._send_status("🔒 Browser closed")

if __name__ == "__main__":
    sniper = SniperEngine()
    result = sniper.run()
    print(f"Result: {'SUCCESS' if result else 'FAILED'}")
