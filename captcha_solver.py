import logging
import base64
from typing import Optional
from io import BytesIO

try:
    import ddddocr
    DDDDOCR_AVAILABLE = True
except ImportError:
    DDDDOCR_AVAILABLE = False
    logging.warning("ddddocr not available")

logger = logging.getLogger(__name__)

class CaptchaSolver:
    def __init__(self):
        if not DDDDOCR_AVAILABLE:
            raise ImportError("ddddocr is not installed or available.")
        # ✅ إنشاء OCR مرة واحدة فقط
        self.ocr = ddddocr.DdddOcr(show_ad=False, beta=True)
        logger.info("CaptchaSolver initialized")

    def solve_captcha(self, page, img_selector: str) -> Optional[str]:
        """حل الكابتشا مع معالجة الأخطاء"""
        try:
            logger.info(f"Looking for captcha with selector: {img_selector}")
            
            # ✅ التحقق من وجود العنصر أولاً
            if not page.locator(img_selector).count():
                logger.error("Captcha element not found")
                return None
            
            # ✅ انتظار ظهور العنصر
            page.locator(img_selector).wait_for(state='visible', timeout=10000)
            logger.info("Captcha element visible")
            
            # ✅ التقاط الصورة
            img_element = page.locator(img_selector)
            img_bytes = img_element.screenshot(timeout=10000)
            logger.info(f"Captcha screenshot taken: {len(img_bytes)} bytes")
            
            # ✅ حل الكابتشا
            result = self.ocr.classification(img_bytes)
            logger.info(f"OCR result: '{result}'")
            
            if result and len(result) >= 3:  # ✅ التحقق من طول النتيجة
                return result
            else:
                logger.warning(f"OCR result too short or empty: '{result}'")
                return None
                
        except Exception as e:
            logger.error(f"Error in solve_captcha: {e}")
            return None

    def get_captcha_image_base64(self, page, img_selector: str) -> Optional[str]:
        """الحصول على صورة الكابتشا كـ base64"""
        try:
            img_element = page.locator(img_selector)
            img_bytes = img_element.screenshot()
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting captcha image: {e}")
            return None
