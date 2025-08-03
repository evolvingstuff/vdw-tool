FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all source files
COPY . .

# Run the master script from /data/src when volume mounted
CMD ["python", "/data/src/master_script.py"]