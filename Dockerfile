# استخدام Debian 12 (Bookworm) - مدعوم حتى 2028
FROM python:3.9-slim-bookworm

WORKDIR /app

# تثبيت متطلبات النظام لـ Playwright وddddocr
RUN apt-get update && apt-get install -y \
    # متطلبات Playwright/Chromium
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    # متطلبات إضافية لـ ddddocr (إذا كنت تستخدم OCR للكابتشا)
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # خطوط ودعم اللغات
    fonts-liberation \
    fonts-dejavu \
    fontconfig \
    wget \
    curl \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# تثبيت متطلبات Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# تثبيت متصفح Chromium فقط (أخف من تثبيت الكل)
RUN playwright install chromium && \
    playwright install-deps chromium

# تنظيف Playwright cache لتقليل حجم الصورة
RUN rm -rf ~/.cache/ms-playwright/ffmpeg* \
    ~/.cache/ms-playwright/firefox* \
    ~/.cache/ms-playwright/webkit*

# نسخ ملفات التطبيق
COPY . .

# إنشاء مستخدم غير root للأمان (اختياري لكن موصى به)
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# متغيرات البيئة
ENV HEADLESS="True"
ENV DEBUG_MODE="False"
ENV TARGET_URL="https://service2.diplo.de/rktermin/extern/appointment_showMonth.do?request_locale=en&locationCode=mask&realmId=354&categoryId=1638&"
ENV CATEGORY_ID="1638"
ENV LAST_NAME="AL-kiHI"
ENV FIRST_NAME="Taratst"
ENV EMAIL="waffaron@gmail.com"
ENV PHONE="00967777123488"
ENV PASSPORT="2490087"
ENV PURPOSE="Student Visa"
ENV TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
ENV TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
ENV REGULAR_CHECK_CRON="0 * * * *"
ENV INTENSIVE_CHECK_CRON="0-30 23 * * *"
ENV CAPTCHA_RETRY_LIMIT="3"
ENV CAPTCHA_SOLVER_TIMEOUT="10"
ENV USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
ENV VIEWPORT_WIDTH="1280"
ENV VIEWPORT_HEIGHT="800"
ENV MIN_DELAY="1"
ENV MAX_DELAY="3"
ENV MAX_RETRIES="5"
ENV RETRY_DELAY="5"
ENV PYTHONUNBUFFERED=1

# Health check للتأكد من عمل البوت
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe', timeout=5)" || exit 1

# تشغيل الجدولة
CMD ["python", "main_scheduler.py"]
