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

# Create a directory for static files
RUN mkdir -p /app/staticfiles

# Run migrations and collect static files (optional: can be done at runtime)
# RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Default command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
