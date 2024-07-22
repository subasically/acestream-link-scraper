FROM python:3.8-slim

# Install dependencies
RUN apt-get update && apt-get install -y curl jq

# Set the working directory
WORKDIR /usr/src/app

# Copy the entrypoint script
COPY wait-for-acestream.sh .

# Copy the rest of the application files
COPY . .

# Install any Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the entrypoint script is executable
RUN chmod +x wait-for-acestream.sh

# Set the default command
CMD ["python", "main.py"]
