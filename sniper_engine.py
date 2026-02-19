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

    def _send_status(self, message: str, screenshot: bool = False, html: bool = False, page: Page = None):
        """إرسال حالة + صورة + HTML إلى Telegram"""
        logger.info(message)
        
        # إرسال الرسالة النصية
        send_sync_message(f"🤖 {message}")
        
        # إرسال لقطة شاشة
        if screenshot and page:
            try:
                img = page.screenshot(full_page=True)
                send_sync_photo(img, f"📸 {message[:50]}")
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
        
        # إرسال HTML
        if html and page:
            try:
                html_content = page.content()
                # تقصير HTML إذا كان طويلاً جداً
                if len(html_content) > 4000:
                    html_content = html_content[:2000] + "\n...\n[HTML truncated]\n...\n" + html_content[-2000:]
                
                # حفظ HTML في ملف مؤقت وإرساله
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                    f.write(html_content)
                    f.flush()
                    # إرسال كملف نصي
                    with open(f.name, 'rb') as file:
                        send_sync_document(file, f"📄 HTML: {message[:30]}")
                    import os
                    os.unlink(f.name)
                    
            except Exception as e:
                logger.error(f"HTML capture failed: {e}")

    def _human_like_delay(self, min_d=None, max_d=None):
        min_delay = min_d or self.config.MIN_DELAY
        max_delay = max_d or self.config.MAX_DELAY
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        return delay

    def _get_element_html(self, page: Page, selector: str) -> str:
        """استخراج HTML لعنصر محدد"""
        try:
            element = page.locator(selector).first
            if element:
                return element.evaluate("el => el.outerHTML")
        except:
            pass
        return f"Element not found: {selector}"

    def _solve_and_submit_captcha(self, page: Page, img_selector: str, input_selector: str, submit_selector: str, step_name: str) -> bool:
        """حل الكابتشا مع HTML تفصيلي"""
        self._send_status(f"🔒 {step_name}: Starting", screenshot=True, html=True, page=page)
        
        # إرسال HTML للكابتشا
        captcha_html = self._get_element_html(page, img_selector)
        send_sync_message(f"🔍 Captcha HTML:\n```html\n{captcha_html[:500]}\n```")
        
        for attempt in range(1, self.config.CAPTCHA_RETRY_LIMIT + 1):
            self._send_status(f"🔒 Attempt {attempt}", html=True, page=page)
            
            # حل الكابتشا
            captcha_text = self.captcha_solver.solve_captcha(page, img_selector)
            self._send_status(f"📝 OCR: '{captcha_text}'")
            
            if not captcha_text:
                self._send_status("❌ OCR failed", html=True, page=page)
                continue

            # ملء الحقل
            try:
                page.fill(input_selector, captcha_text)
                
                # إرسال HTML بعد الملء
                filled_html = self._get_element_html(page, input_selector)
                send_sync_message(f"✍️ Input HTML after fill:\n```html\n{filled_html[:300]}\n```")
                
                self._human_like_delay(0.5, 1.5)
                page.click(submit_selector)
                self._human_like_delay(2, 4)
                
            except Exception as e:
                self._send_status(f"❌ Error: {e}", html=True, page=page)
                continue

            # التحقق
            page_content = page.content()
            if "Please enter here the text you see in the picture above" not in page_content:
                self._send_status(f"✅ Success! Entered: '{captcha_text}'", screenshot=True, html=True, page=page)
                return True
            else:
                self._send_status(f"❌ Wrong: '{captcha_text}'", screenshot=True, html=True, page=page)

        self._send_status("🚨 All attempts failed", screenshot=True, html=True, page=page)
        return False

    def run(self) -> bool:
        with sync_playwright() as p:
            browser = None
            try:
                self._send_status("🚀 Starting browser...")
                browser = p.chromium.launch(headless=self.config.HEADLESS)
                
                context = browser.new_context(
                    viewport={'width': self.config.VIEWPORT_WIDTH, 'height': self.config.VIEWPORT_HEIGHT},
                    user_agent=self.config.USER_AGENT
                )
                page = context.new_page()
                
                # فتح الموقع
                self._send_status(f"🌐 Opening: {self.config.TARGET_URL[:60]}...")
                page.goto(self.config.TARGET_URL, timeout=60000, wait_until='networkidle')
                self._send_status("✅ Page loaded", screenshot=True, html=True, page=page)
                
                self._human_like_delay(3, 5)

                # كابتشا أولى
                if not self._solve_and_submit_captcha(
                    page, 
                    'img[src*="captcha"]', 
                    'input[id*="captchaText"]', 
                    'input[id*="appointment_showMonth"]',
                    "Step 1: Initial Captcha"
                ):
                    return False

                # التحقق من التوفر
                self._send_status("🔍 Checking availability...", screenshot=True, html=True, page=page)
                
                page_html = page.content()
                
                if "Unfortunately, there are no appointments available" in page_html:
                    # استخراج الجدول فقط
                    calendar_html = self._get_element_html(page, 'table.calendar')
                    send_sync_message(f"📅 Calendar HTML:\n```html\n{calendar_html[:1000]}\n```")
                    self._send_status("📭 No appointments", screenshot=True, page=page)
                    return False

                self._send_status("🎯 Appointments available!", screenshot=True, html=True, page=page)

                # اختيار اليوم
                self._send_status("📅 Selecting day...", html=True, page=page)
                available_days = page.locator('td.calendarDay.available a').all()
                
                if not available_days:
                    self._send_status("❌ No days found", screenshot=True, html=True, page=page)
                    return False

                # HTML لليوم المختار
                day_html = available_days[0].evaluate("el => el.outerHTML")
                send_sync_message(f"📅 Selected day HTML:\n```html\n{day_html}\n```")
                
                available_days[0].click()
                self._human_like_delay(2, 4)

                # اختيار الوقت
                self._send_status("⏰ Selecting time...", screenshot=True, html=True, page=page)
                available_times = page.locator('input[name="appointment"][type="radio"]').all()
                
                if not available_times:
                    self._send_status("❌ No times found", screenshot=True, html=True, page=page)
                    return False

                # HTML لجميع الأوقات المتاحة
                times_html = ""
                for i, t in enumerate(available_times[:5]):  # أول 5 فقط
                    times_html += f"{i+1}. {t.evaluate('el => el.outerHTML')[:200]}\n"
                send_sync_message(f"⏰ Available times HTML:\n```html\n{times_html}\n```")
                
                available_times[0].click()
                self._human_like_delay(1, 2)
                
                page.click('input[type="submit"][value="Continue"]')
                self._human_like_delay(2, 4)

                # ملء الاستمارة
                self._send_status("📝 Filling form...", screenshot=True, html=True, page=page)
                
                # HTML قبل الملء
                form_before = self._get_element_html(page, 'form')
                send_sync_message(f"📋 Form HTML (before):\n```html\n{form_before[:800]}\n```")
                
                page.fill('input[name="lastname"]', self.config.LAST_NAME)
                page.fill('input[name="firstname"]', self.config.FIRST_NAME)
                page.fill('input[name="email"]', self.config.EMAIL)
                page.fill('input[name="emailrepeat"]', self.config.EMAIL)
                page.fill('input[name="fields[0].content"]', self.config.PASSPORT)
                page.fill('input[name="fields[1].content"]', self.config.PHONE)
                
                # HTML بعد الملء
                form_after = self._get_element_html(page, 'form')
                send_sync_message(f"📋 Form HTML (after):\n```html\n{form_after[:800]}\n```")
                
                self._send_status(f"✅ Filled: {self.config.FIRST_NAME} {self.config.LAST_NAME}", screenshot=True, html=True, page=page)

                # اختيار الغرض
                js_script = f"""
                    var select = document.querySelector('select[name="fields[2].content"]');
                    if (!select) return 'Select not found';
                    var options = Array.from(select.options).map(o => o.text + '=' + o.value);
                    var target = Array.from(select.options).find(o => o.text.includes('{self.config.PURPOSE}'));
                    if (target) {{
                        select.value = target.value;
                        select.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return 'Selected: ' + target.text + ' | All options: ' + options.join(', ');
                    }}
                    return 'Purpose not found | Available: ' + options.join(', ');
                """
                result = page.evaluate(js_script)
                send_sync_message(f"📋 Purpose JS result:\n{result}")
                self._human_like_delay(2, 3)

                # كابتشا نهائية
                if not self._solve_and_submit_captcha(
                    page, 
                    'img[src*="captcha"]', 
                    'input[id*="captchaText"]', 
                    'input[type="submit"][value="Submit"]',
                    "Step 2: Final Captcha"
                ):
                    return False

                # النتيجة
                self._send_status("🎯 Final result...", screenshot=True, html=True, page=page)
                content = page.content()
                
                if "Your appointment has been booked successfully" in content or "Vielen Dank" in content:
                    self._send_status("🎉 SUCCESS!", screenshot=True, html=True, page=page)
                    return True
                elif "An error occurred" in content:
                    self._send_status("❌ Server error", screenshot=True, html=True, page=page)
                    return False
                else:
                    self._send_status("⚠️ Unknown result", screenshot=True, html=True, page=page)
                    return False

            except Exception as e:
                self._send_status(f"💥 ERROR: {str(e)[:200]}", screenshot=True, html=True, page=page if 'page' in locals() else None)
                return False
                
            finally:
                if browser:
                    browser.close()
                    self._send_status("🔒 Browser closed")
