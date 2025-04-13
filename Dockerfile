# Python 3.11 imageni ishlatamiz
FROM python:3.11-slim

# Foydalanuvchi yaratamiz (xavfsizlik uchun)
RUN useradd -m appuser

# Ishchi direktoriyani yaratamiz
WORKDIR /app

# Talab qilinadigan kutubxonalarni o‘rnatish uchun requirements.txt faylini ko‘chiramiz
COPY requirements.txt .

# Kutubxonalarni o‘rnatamiz
RUN pip install --no-cache-dir -r requirements.txt

# Kodni konteynerga ko‘chiramiz
COPY bot.py .

# Foydalanuvchini o‘zgartiramiz
USER appuser

# Botni ishga tushiramiz
CMD ["python", "bot.py"]