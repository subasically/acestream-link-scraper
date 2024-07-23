# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a working directory
WORKDIR /usr/src/app

# Install curl and other dependencies
RUN apt-get update && \
  apt-get install -y curl && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Copy requirements.txt
COPY requirements.txt /usr/src/app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

# Copy the rest of the application
COPY . /usr/src/app/

# Make wait-for-acestream.sh executable
RUN chmod +x /usr/src/app/wait-for-acestream.sh

# Run the application
CMD ["/usr/src/app/wait-for-acestream.sh", "server:80", "python", "main.py"]
