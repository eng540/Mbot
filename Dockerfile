FROM python:3.9-slim-buster

WORKDIR /app

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libfontconfig libatk-bridge2.0-0 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm-dev libasound2 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application files
COPY . .

# Set environment variables with default values (can be overridden during docker run)
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

# Command to run the scheduler
CMD ["python", "main_scheduler.py"]
