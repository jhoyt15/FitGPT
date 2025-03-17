# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install essential build tools and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    gcc \
    g++ \
    cmake \
    make \
    pkg-config \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Configure pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Use a more reliable mirror for pip
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Install requirements in smaller groups with explicit ordering to handle dependencies better
RUN pip install --no-cache-dir Flask==2.0.1 Werkzeug==2.0.3 python-dotenv flask-cors Flask-Login && \
    pip install --no-cache-dir elasticsearch==8.17.1 && \
    pip install --no-cache-dir oauthlib requests-oauthlib google-auth google-auth-oauthlib && \
    pip install --no-cache-dir fuzzywuzzy jinja2 python-Levenshtein gunicorn && \
    pip install --no-cache-dir huggingface-hub transformers sentence-transformers && \
    pip install --no-cache-dir mistralai && \
    pip install --no-cache-dir langchain langchain-core langchain-community && \
    pip install --no-cache-dir langchain-elasticsearch langchain_mistralai

# Copy the download script
COPY download_model.py .

# Pre-download the HuggingFace model with retry logic
RUN python download_model.py || \
    (echo "Retrying model download..." && sleep 5 && python download_model.py) || \
    (echo "Skipping model download, will download at runtime")

# Copy the rest of the application
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# You'll need to set this when running the container
ENV MISTRAL_API_KEY=${MISTRAL_API_KEY}

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["flask", "run", "--host=0.0.0.0"]