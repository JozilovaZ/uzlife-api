FROM python:3.12-slim

# Muhitni sozlaymiz
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Postgres kutubxonasi + rasm generatsiyasi uchun DejaVu shriftlari
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Avval requirements — Docker qatlam keshidan foydalanish uchun
COPY requirements.txt .
RUN pip install -r requirements.txt

# Loyiha kodi
COPY . .

# Ishga tushirish skripti
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
