# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Create a working directory
WORKDIR /usr/src/app

# Copy only requirements.txt first to leverage Docker caching
COPY requirements.txt /usr/src/app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

# Copy the rest of the application
COPY . /usr/src/app/

# Run the application
CMD ["python", "./main.py"]
