FROM python:3.8-slim

WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /usr/src/app/

# Ensure scripts are executable
RUN chmod +x /usr/src/app/wait-for-acestream.sh

# Default command
CMD ["python", "main.py"]
