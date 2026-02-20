import time
import random
import logging
from playwright.sync_api import sync_playwright, Page, expect
from config import Config
from captcha_solver import CaptchaSolver
from telegram_bot import send_sync_message, send_sync_photo, send_sync_document

logger = logging.getLogger(__name__)

class SniperEngine:
    def __init__(self):
        self.config = Config()
        self.captcha_solver = CaptchaSolver()

    def _human_like_delay(self):
        time.sleep(random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY))

    def _safe_send_document(self, content, filename, caption):
        """Helper to send documents safely to Telegram without crashing the engine."""
        try:
            if isinstance(content, str):
                content = content.encode('utf-8')
            send_sync_document(content, filename, caption)
        except Exception as e:
            logger.error(f"Failed to send document {filename} to Telegram: {e}")

    def _solve_and_submit_captcha(self, page: Page, img_selector: str, input_selector: str, submit_selector: str) -> bool:
        for attempt in range(self.config.CAPTCHA_RETRY_LIMIT):
            try:
                logger.info(f"🔒 Attempt {attempt + 1}")
                send_sync_message(f"🔒 Attempt {attempt + 1}")
                
                # Wait for the captcha image to be visible
                captcha_img_locator = page.locator(img_selector)
                # Ensure the element is visible before trying to take a screenshot
                captcha_img_locator.wait_for(state="visible", timeout=self.config.CAPTCHA_SOLVER_TIMEOUT * 1000)
                
                captcha_text = self.captcha_solver.solve_captcha(page, img_selector)
                logger.info(f"📝 OCR: '{captcha_text}'")
                
                if captcha_text:
                    page.fill(input_selector, captcha_text)
                    self._human_like_delay()
                    page.click(submit_selector)
                    self._human_like_delay()
                    
                    # Check if captcha was solved successfully
                    # If the captcha input field is still visible, it means it failed
                    if page.locator(input_selector).is_visible():
                        logger.warning(f"Captcha solution '{captcha_text}' was incorrect. Retrying...")
                        send_sync_message(f"⚠️ Captcha incorrect. Retrying...")
                        # Reload captcha image if possible
                        refresh_btn = page.locator("input[id*=\"refreshcaptcha\"]")
                        if refresh_btn.is_visible():
                            refresh_btn.click()
                            self._human_like_delay()
                    else:
                        logger.info(f"Captcha solved successfully on attempt {attempt + 1}.")
                        return True
                else:
                    logger.error("❌ OCR failed")
                    send_sync_message("❌ OCR failed")
            except Exception as e:
                logger.error(f"Error during captcha solving attempt {attempt + 1}: {e}")
                send_sync_message(f"❌ Error during captcha solving: {e}")
                # Save HTML on failure for debugging
                self._safe_send_document(page.content(), f"captcha_error_attempt_{attempt+1}.html", f"Captcha Error Details")
            self._human_like_delay()
        logger.error("Failed to solve captcha after multiple attempts.")
        return False

    def run(self) -> bool:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config.HEADLESS)
            context = browser.new_context(
                viewport={'width': self.config.VIEWPORT_WIDTH, 'height': self.config.VIEWPORT_HEIGHT},
                user_agent=self.config.USER_AGENT
            )
            page = context.new_page()

            try:
                logger.info(f"🚀 Starting browser...")
                logger.info(f"🌐 Opening: {self.config.TARGET_URL}")
                send_sync_message(f"🌐 Opening: {self.config.TARGET_URL}")
                
                page.goto(self.config.TARGET_URL, wait_until="networkidle", timeout=60000)
                logger.info("✅ Page loaded")
                send_sync_message("✅ Page loaded")
                
                # Take a screenshot for initial verification
                send_sync_photo(page.screenshot(), caption="Initial Page Load")

                # --- Step 1: Solve initial captcha ---
                logger.info("🔒 Step 1: Initial Captcha: Starting")
                send_sync_message("🔒 Step 1: Initial Captcha: Starting")
                if not self._solve_and_submit_captcha(
                    page, 
                    "img[src*=\"captcha\"]", 
                    "input[id*=\"captchaText\"]", 
                    "input[id*=\"appointment_showMonth\"]"
                ):
                    return False

                # --- Step 2: Check for available appointments ---
                page.wait_for_load_state("networkidle")
                self._human_like_delay()

                if "Unfortunately, there are no appointments available at this time" in page.content():
                    logger.info("❌ No appointments available this month.")
                    send_sync_message("❌ No appointments available this month.")
                    return False
                
                logger.info("✅ Appointments might be available!")
                send_sync_message("✅ Appointments might be available! Proceeding...")
                send_sync_photo(page.screenshot(), caption="Available Appointments View")

                # --- Step 3: Select an available day ---
                available_days = page.locator("td.calendarDay.available a").all()
                if not available_days:
                    logger.info("❌ No available days found.")
                    send_sync_message("❌ No available days found.")
                    return False
                
                available_days[0].click()
                self._human_like_delay()
                page.wait_for_load_state("networkidle")

                # --- Step 4: Select an available time slot ---
                available_times = page.locator("input[name=\"appointment\"][type=\"radio\"]").all()
                if not available_times:
                    logger.info("❌ No time slots found.")
                    send_sync_message("❌ No time slots found.")
                    return False
                
                available_times[0].click()
                self._human_like_delay()
                page.click("input[type=\"submit\"][value=\"Continue\"]")
                self._human_like_delay()
                page.wait_for_load_state("networkidle")

                # --- Step 5: Fill the form ---
                logger.info("📝 Filling appointment form...")
                send_sync_message("📝 Filling appointment form...")
                
                page.fill("input[name=\"lastname\"]", self.config.LAST_NAME)
                page.fill("input[name=\"firstname\"]", self.config.FIRST_NAME)
                page.fill("input[name=\"email\"]", self.config.EMAIL)
                page.fill("input[name=\"emailrepeat\"]", self.config.EMAIL)
                page.fill("input[name=\"fields[0].content\"]", self.config.PASSPORT)
                page.fill("input[name=\"fields[1].content\"]", self.config.PHONE)
                
                # Purpose Selection via JS
                purpose_value = self.config.PURPOSE
                page.evaluate(f"""
                    var select = document.querySelector(\'select[name="fields[2].content"]\');
                    if (select) {{
                        var options = Array.from(select.options);
                        var target = options.find(o => o.text.includes(\'{purpose_value}\'));
                        if (target) {{
                            select.value = target.value;
                            select.dispatchEvent(new Event(\'change\', {{ bubbles: true }}));
                        }}
                    }}
                """)
                self._human_like_delay()

                # --- Step 6: Final Captcha and Submit ---
                logger.info("🔒 Step 6: Final Captcha: Starting")
                send_sync_message("🔒 Step 6: Final Captcha: Starting")
                if not self._solve_and_submit_captcha(
                    page, 
                    "img[src*=\"captcha\"]", 
                    "input[id*=\"captchaText\"]", 
                    "input[type=\"submit\"][value=\"Submit\"]"
                ):
                    return False
                
                page.wait_for_load_state("networkidle")
                self._human_like_delay()

                # --- Step 7: Check Success ---
                if "Your appointment has been booked successfully" in page.content() or "Vielen Dank" in page.content():
                    logger.info("🎉 SUCCESS! Appointment booked.")
                    send_sync_message("🎉 SUCCESS! Appointment booked.")
                    send_sync_photo(page.screenshot(), caption="Booking Success Confirmation")
                    return True
                else:
                    logger.error("❌ Booking failed at final step.")
                    send_sync_message("❌ Booking failed at final step.")
                    self._safe_send_document(page.content(), "booking_failed.html", "Final Failure Details")
                    return False

            except Exception as e:
                logger.error(f"❌ Critical Error: {e}")
                send_sync_message(f"❌ Critical Error: {e}")
                try:
                    send_sync_photo(page.screenshot(), caption="Critical Error Screenshot")
                except: pass
                return False
            finally:
                browser.close()

if __name__ == "__main__":
    sniper = SniperEngine()
    sniper.run()
