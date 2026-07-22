# This is my  Python image
FROM python:3.12-slim

#For Setting  working directory inside my container
WORKDIR /app

# Install system dependencies 
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first 
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port 8000
EXPOSE 8000

# Run gunicorn when container starts
CMD ["gunicorn", "bloodmatch.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
