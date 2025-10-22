# ====== Backend Dockerfile ======
FROM python:3.10-slim

# تحديد مسار العمل داخل الكونتينر
WORKDIR /app

# نسخ ملفات المشروع إلى داخل الكونتينر
COPY . /app

# تثبيت المتطلبات
RUN pip install --no-cache-dir -r requirements.txt

# فتح المنفذ 8000
EXPOSE 8000

# تشغيل السيرفر باستخدام uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
