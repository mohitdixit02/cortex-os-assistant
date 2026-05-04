FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch and CUDA dependencies FIRST
# These are the heaviest and least likely to change.
# By putting them above the COPY requirements.txt, we ensure they stay cached
# even if requirements.txt is edited.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    nvidia-cudnn-cu12==9.1.0.70 \
    nvidia-cublas-cu12==12.1.3.1 \
    torch==2.5.1 \
    torchvision==0.20.1

# Copy requirements and install remaining packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data and spaCy model
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')" \
    && python -m spacy download en_core_web_sm

# Copy the entire project code last (it changes most frequently)
COPY . .

# Set PYTHONPATH to include the root directory for absolute imports
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose)
CMD ["python", "cortex_server/main.py"]
