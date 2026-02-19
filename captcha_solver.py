import logging
import base64
from io import BytesIO
from PIL import Image
from typing import Optional  # ✅ أضفنا هذا الاستيراد
from playwright.sync_api import Page

try:
    import ddddocr
    DDDDOCR_AVAILABLE = True
except ImportError:
    DDDDOCR_AVAILABLE = False
    logging.warning("ddddocr not available - captcha solving disabled")

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self):
        if not DDDDOCR_AVAILABLE:
            raise ImportError("ddddocr is not installed or available.")
        self.ocr = ddddocr.DdddOcr(show_ad=False)

    # ✅ استخدمنا Optional[str] بدلاً من str | None
    def solve_captcha(self, page: Page, img_selector: str) -> Optional[str]:
        """Solves captcha from an image element on the page."""
        try:
            # Get the image element as a screenshot
            img_element = page.locator(img_selector)
            img_bytes = img_element.screenshot()

            # Use ddddocr to solve the captcha
            result = self.ocr.classification(img_bytes)
            logger.info(f"Captcha solved: {result}")
            return result
        except Exception as e:
            logger.error(f"Error solving captcha: {e}")
            return None

    # ✅ استخدمنا Optional[str] بدلاً من str | None
    def get_captcha_image_base64(self, page: Page, img_selector: str) -> Optional[str]:
        """Gets the captcha image as a base64 string."""
        try:
            img_element = page.locator(img_selector)
            img_bytes = img_element.screenshot()
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting captcha image: {e}")
            return None
