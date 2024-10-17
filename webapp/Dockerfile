# Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
#    libgirepository1.0-dev \
#    libcairo2-dev \
#    gir1.2-gobject-2.0 \
#    libpango-1.0-0 \
#    libpangocairo-1.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /code/
RUN chmod a+rw logs/
RUN chmod a+rw logs/*
