# 1. Use official Python base image
FROM python:3.11-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set working directory in the container
WORKDIR /app

# 4. Install system dependencies
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
# 5. Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6. Copy project files
COPY . .

# 7. Collect static files
RUN python manage.py collectstatic --noinput

# 8. Run Django migrations
RUN python manage.py makemigrations && python manage.py migrate

# 9. Set the default command
# Run the app with Gunicorn
CMD ["gunicorn", "SchoolBusTracking.wsgi:application", "--bind", "0.0.0.0:8000"]