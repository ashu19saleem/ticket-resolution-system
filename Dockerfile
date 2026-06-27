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

# Create embeddings directory
RUN mkdir -p embeddings

# Set environment variables
ENV LLM_PROVIDER=groq
ENV EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
ENV VECTOR_DB_PROVIDER=chroma
ENV TOP_K_RESULTS=5

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Start the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
