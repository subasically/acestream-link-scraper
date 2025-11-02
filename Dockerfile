FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=proxy.py

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY supervisord.conf /etc/supervisord.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .
RUN mkdir -p /app/data

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
