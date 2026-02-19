import time
import random
import logging
from playwright.sync_api import sync_playwright, Page, BrowserContext
from config import Config
from captcha_solver import CaptchaSolver

logger = logging.getLogger(__name__)

class SniperEngine:
    def __init__(self):
        self.config = Config()
        self.captcha_solver = CaptchaSolver()

    def _human_like_delay(self):
        time.sleep(random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY))

    def _solve_and_submit_captcha(self, page: Page, img_selector: str, input_selector: str, submit_selector: str) -> bool:
        for attempt in range(self.config.CAPTCHA_RETRY_LIMIT):
            captcha_text = self.captcha_solver.solve_captcha(page, img_selector)
            if captcha_text:
                page.fill(input_selector, captcha_text)
                self._human_like_delay()
                page.click(submit_selector)
                self._human_like_delay()
                # Check if captcha was solved successfully (e.g., by checking for error message or new page content)
                if "Please enter here the text you see in the picture above" not in page.content():
                    logger.info(f"Captcha solved successfully on attempt {attempt + 1}.")
                    return True
                else:
                    logger.warning(f"Captcha solution '{captcha_text}' was incorrect. Retrying...")
                    # Reload captcha image if possible
                    if page.locator('input[id*="refreshcaptcha"]').is_visible():
                        page.click('input[id*="refreshcaptcha"]')
                        self._human_like_delay()
            else:
                logger.error("Failed to get captcha text. Retrying...")
            self._human_like_delay()
        logger.error("Failed to solve captcha after multiple attempts.")
        return False

    def run(self) -> bool:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.config.HEADLESS)
            context = browser.new_context(
                viewport={
                    'width': self.config.VIEWPORT_WIDTH,
                    'height': self.config.VIEWPORT_HEIGHT
                },
                user_agent=self.config.USER_AGENT
            )
            page = context.new_page()

            try:
                logger.info(f"Navigating to {self.config.TARGET_URL}")
                page.goto(self.config.TARGET_URL)
                self._human_like_delay()

                # --- Step 1: Solve initial captcha ---
                if not self._solve_and_submit_captcha(
                    page, 
                    'img[src*="captcha"]', 
                    'input[id*="captchaText"]', 
                    'input[id*="appointment_showMonth"]'
                ):
                    return False

                # --- Step 2: Check for available appointments ---
                if "Unfortunately, there are no appointments available at this time" in page.content():
                    logger.info("No appointments available for the current month.")
                    # Navigate to next month if needed (simplified for now, full logic in main scheduler)
                    # For this initial run, we just check the current view
                    return False

                logger.info("Appointments might be available. Proceeding to select.")

                # --- Step 3: Select an available day and time ---
                # This part needs to be dynamic based on actual available dates
                # For demonstration, let's assume we click the first available day if any
                available_days = page.locator('td.calendarDay.available a').all()
                if not available_days:
                    logger.info("No available days found in the current month.")
                    return False

                available_days[0].click() # Click the first available day
                self._human_like_delay()

                # --- Step 4: Select an available time slot ---
                available_times = page.locator('input[name="appointment"][type="radio"]').all()
                if not available_times:
                    logger.info("No available time slots found for the selected day.")
                    return False

                available_times[0].click() # Click the first available time slot
                self._human_like_delay()
                page.click('input[type="submit"][value="Continue"]') # Click continue after selecting time
                self._human_like_delay()

                # --- Step 5: Fill the form and select purpose ---
                logger.info("Filling appointment form...")
                page.fill('input[name="lastname"]', self.config.LAST_NAME)
                page.fill('input[name="firstname"]', self.config.FIRST_NAME)
                page.fill('input[name="email"]', self.config.EMAIL)
                page.fill('input[name="emailrepeat"]', self.config.EMAIL)
                page.fill('input[name="fields[0].content"]', self.config.PASSPORT)
                page.fill('input[name="fields[1].content"]', self.config.PHONE)
                self._human_like_delay()

                # Crucial: Select purpose using JavaScript to ensure session state update
                purpose_value = self.config.PURPOSE
                js_script = f"""
                    var selectElement = document.querySelector('select[name="fields[2].content"]');
                    if (selectElement) {{
                        var options = Array.from(selectElement.options);
                        var targetOption = options.find(option => option.text.includes('{purpose_value}'));
                        if (targetOption) {{
                            selectElement.value = targetOption.value;
                            selectElement.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            console.log('Purpose selected via JS: {purpose_value}');
                        }} else {{ 
                            console.log('Purpose select element not found or option not found.'); 
                        }}
                    }}
                """

                page.evaluate(js_script)
                logger.info(f"Purpose '{purpose_value}' selected via JavaScript.")
                self._human_like_delay()

                # --- Step 6: Solve final captcha and submit ---
                if not self._solve_and_submit_captcha(
                    page, 
                    'img[src*="captcha"]', 
                    'input[id*="captchaText"]', 
                    'input[type="submit"][value="Submit"]'
                ):
                    return False

                # --- Step 7: Check for success message ---
                if "Your appointment has been booked successfully" in page.content() or "Vielen Dank" in page.content():
                    logger.info("Appointment booked successfully!")
                    return True
                elif "An error occurred while processing your appointment" in page.content():
                    logger.error("Server error during appointment booking. Retrying might be needed.")
                    return False
                else:
                    logger.warning("Unknown result after submission.")
                    return False

            except Exception as e:
                logger.error(f"An error occurred during the booking process: {e}")
                return False
            finally:
                browser.close()

if __name__ == "__main__":
    sniper = SniperEngine()
    if sniper.run():
        print("Booking attempt finished successfully.")
    else:
        print("Booking attempt failed.")

    # Example usage for Muscat
    muscat_embassy_config = {
        "url": Config.MUSCAT_URL,
        "last_name": Config.LAST_NAME_MUSCAT,
        "first_name": Config.FIRST_NAME_MUSCAT,
        "email": Config.EMAIL_MUSCAT,
        "phone": Config.PHONE_MUSCAT,
        "passport": Config.PASSPORT_MUSCAT,
        "purpose": Config.PURPOSE_MUSCAT
    }
    sniper = SniperEngine(muscat_embassy_config)
    if sniper.run():
        print("Muscat booking attempt finished successfully.")
    else:
        print("Muscat booking attempt failed.")

    # Example usage for Cairo
    cairo_embassy_config = {
        "url": Config.CAIRO_URL,
        "last_name": Config.LAST_NAME_CAIRO,
        "first_name": Config.FIRST_NAME_CAIRO,
        "email": Config.EMAIL_CAIRO,
        "phone": Config.PHONE_CAIRO,
        "passport": Config.PASSPORT_CAIRO,
        "purpose": Config.PURPOSE_CAIRO
    }
    sniper = SniperEngine(cairo_embassy_config)
    if sniper.run():
        print("Cairo booking attempt finished successfully.")
    else:
        print("Cairo booking attempt failed.")
