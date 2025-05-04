# Use the official Python image from the Docker Hub
FROM python:alpine

# Install nginx and supervisor
RUN apk add --no-cache nginx supervisor

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy supervisor config
COPY supervisord.conf /etc/supervisord.conf

# Make nginx log dir
RUN mkdir -p /run/nginx

# Expose ports: 80 for nginx, 6878 for AceStream proxy (if needed)
EXPOSE 80

# Run the application using supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
