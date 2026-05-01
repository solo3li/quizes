# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY req.txt /app/
RUN pip install --no-cache-dir -r req.txt

# Copy project
COPY . /app/

# Create directories and ensure static exists
RUN mkdir -p /app/staticfiles /app/data /app/static

# Run migrations and collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Use Gunicorn to run the application on port 8000
CMD python manage.py migrate && gunicorn quiz_project.wsgi:application --bind 0.0.0.0:8000 --timeout 120

