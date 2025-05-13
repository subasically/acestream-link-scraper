FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=proxy.py

# Install all dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    curl \
    build-essential \
    supervisor && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    flask \
    requests \
    beautifulsoup4

# Set up app directory and Nginx root
WORKDIR /app
COPY main.py proxy.py ntfy.py index.html supervisord.conf nginx.conf ./

# Point Nginx to /app as its web root
RUN mkdir -p /var/www/html && \
    ln -s /app/index.html /var/www/html/index.html

# Expose ports
# 8500 for static UI, 8888 for manifest proxy
EXPOSE 8500 8888

# Launch all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
