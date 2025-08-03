FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Hugo and Pagefind
RUN apt-get update && apt-get install -y \
    wget \
    ca-certificates \
    tar \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Hugo (using tar.gz method which is more reliable)
RUN wget -O hugo.tar.gz https://github.com/gohugoio/hugo/releases/download/v0.121.1/hugo_0.121.1_linux-amd64.tar.gz \
    && tar -xzf hugo.tar.gz \
    && mv hugo /usr/local/bin/ \
    && rm hugo.tar.gz LICENSE README.md

# Install Pagefind for search indexing
RUN curl -L https://github.com/CloudCannon/pagefind/releases/download/v1.0.4/pagefind-v1.0.4-x86_64-unknown-linux-musl.tar.gz \
    | tar -xz -C /usr/local/bin/

# Install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all source files
COPY . .

# Expose port 1313 for Hugo site serving
EXPOSE 1313

# Run the app script from /data/src when volume mounted
CMD ["python", "/data/_src/app.py"]