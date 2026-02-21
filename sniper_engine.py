import time
import random
import logging
from playwright.sync_api import sync_playwright, Page
from config import Config
from captcha_solver import CaptchaSolver
from telegram_bot import send_sync_message, send_sync_photo

logger = logging.getLogger(__name__)

class SniperEngine:
    def __init__(self):
        self.config = Config()
        self.captcha_solver = CaptchaSolver()

    def _send_status(self, message: str, screenshot: bool = False, page: Page = None):
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
        """حل الكابتشا وإرسالها"""
        self._send_status(f"🔒 {step_name}: Starting", screenshot=True, page=page)
        
        for attempt in range(1, self.config.CAPTCHA_RETRY_LIMIT + 1):
            self._send_status(f"🔒 Attempt {attempt}/{self.config.CAPTCHA_RETRY_LIMIT}")
            
            # ✅ حل الكابتشا (بشكل متزامن - لا async)
            try:
                captcha_text = self.captcha_solver.solve_captcha(page, img_selector)
            except Exception as e:
                logger.error(f"Captcha solver crashed: {e}")
                captcha_text = None
            
            self._send_status(f"📝 OCR result: '{captcha_text}'")
            
            if not captcha_text:
                self._send_status("❌ OCR failed or returned None", screenshot=True, page=page)
                
                # ✅ تحديث الكابتشا إذا فشل OCR
                try:
                    refresh_btn = page.locator('input[id*="refreshcaptcha"], a[id*="refreshcaptcha"], button[id*="refreshcaptcha"], img[id*="refreshcaptcha"]')
                    if refresh_btn.count() > 0 and refresh_btn.is_visible():
                        self._send_status("🔄 Refreshing captcha...")
                        refresh_btn.click()
                        self._human_like_delay(3, 5)
                    else:
                        self._human_like_delay(2, 4)
                except Exception as e:
                    logger.error(f"Refresh failed: {e}")
                    self._human_like_delay(2, 4)
                continue

            # ✅ ملء الحقل
            try:
                self._send_status(f"✍️ Filling captcha: '{captcha_text}'")
                page.fill(input_selector, captcha_text)
                self._human_like_delay(0.5, 1.5)
                
                # ✅ التقاط صورة قبل الإرسال
                self._send_status("📸 Before submit", screenshot=True, page=page)
                
                # ✅ الضغط على زر الإرسال
                page.click(submit_selector)
                self._send_status("📤 Submitted", screenshot=True, page=page)
                self._human_like_delay(3, 5)
                
            except Exception as e:
                self._send_status(f"❌ Error filling/submitting: {e}", screenshot=True, page=page)
                continue

            # ✅ التحقق من النجاح
            try:
                page_content = page.content()
                if "Please enter here the text you see in the picture above" not in page_content:
                    self._send_status(f"✅ Captcha accepted!", screenshot=True, page=page)
                    return True
                else:
                    self._send_status(f"❌ Wrong captcha, retrying...", screenshot=True, page=page)
            except Exception as e:
                logger.error(f"Error checking result: {e}")

        self._send_status("🚨 All attempts failed", screenshot=True, page=page)
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
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=self.config.USER_AGENT
                )
                page = context.new_page()
                
                # فتح الموقع
                self._send_status(f"🌐 Opening site...")
                page.goto(self.config.TARGET_URL, timeout=120000, wait_until='load')
                self._human_like_delay(5, 8)
                self._send_status("✅ Page loaded", screenshot=True, page=page)

                # ✅ الخطوة 1: كابتشا أولى
                if not self._solve_and_submit_captcha(
                    page, 
                    'img[src*="captcha"]', 
                    'input[id*="captchaText"]', 
                    'input[id*="appointment_showMonth"]',
                    "Step 1: Initial Captcha"
                ):
                    return False

                # ✅ التحقق من النتيجة
                self._send_status("🔍 Checking result...", screenshot=True, page=page)
                
                if "Unfortunately, there are no appointments available" in page.content():
                    self._send_status("📭 No appointments", screenshot=True, page=page)
                    return False

                self._send_status("🎯 Success! Continuing...", screenshot=True, page=page)
                return True  # مؤقتاً للاختبار

            except Exception as e:
                self._send_status(f"💥 ERROR: {str(e)[:200]}")
                return False
                
            finally:
                if browser:
                    browser.close()
                    self._send_status("🔒 Browser closed")
