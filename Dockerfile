FROM python:3.11-slim

# Enable BuildKit cache mounts for pip so large wheels (torch/CUDA) are reused across builds.
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep NLTK data in a persistent image path
ENV NLTK_DATA=/usr/local/share/nltk_data
RUN mkdir -p /usr/local/share/nltk_data

# Install PyTorch and CUDA dependencies FIRST
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://download.pytorch.org/whl/cu121 \
    nvidia-cudnn-cu12==9.1.0.70 \
    nvidia-cublas-cu12==12.1.3.1 \
    torch==2.5.1 \
    torchvision==0.20.1

# Copy requirements and install remaining packages
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Download NLTK data and spaCy model
RUN python -c "import nltk; nltk.download('punkt', download_dir='/usr/local/share/nltk_data'); nltk.download('punkt_tab', download_dir='/usr/local/share/nltk_data'); nltk.download('averaged_perceptron_tagger', download_dir='/usr/local/share/nltk_data')" \
    && python -m spacy download en_core_web_sm

# Copy the entire project code last (it changes most frequently)
COPY . .

# Set PYTHONPATH to include the root directory for absolute imports
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose)
CMD ["python", "cortex_server/main.py"]
