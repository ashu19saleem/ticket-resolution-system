FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

# Copy project files
COPY app/ ./app/
COPY models/ ./models/
COPY rag/ ./rag/
COPY utils/ ./utils/
COPY data/ ./data/
COPY .env.example .env

# Create embeddings directory
RUN mkdir -p embeddings

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
