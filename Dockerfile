FROM python:3.9-slim-bookworm

WORKDIR /app

# تثبيت متطلبات النظام
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libfontconfig1 libatk-bridge2.0-0 libatk1.0-0 \
    libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 \
    libgl1-mesa-glx libsm6 libxext6 libxrender-dev libgomp1 \
    fonts-liberation fonts-dejavu fontconfig \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# تثبيت Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ✅ تثبيت Playwright browsers (مهم: قبل نسخ التطبيق)
RUN playwright install chromium && \
    playwright install-deps chromium

# نسخ التطبيق
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main_scheduler.py"]
