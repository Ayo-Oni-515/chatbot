FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Environment settings for pyenv
ENV DEBIAN_FRONTEND=noninteractive
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PYENV_ROOT/plugins/python-build/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev \
    libncursesw5-dev libffi-dev liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pyenv
RUN curl https://pyenv.run | bash

# Install Python 3.13.5 with pyenv
RUN pyenv install 3.13.5 && pyenv global 3.13.5

# Verify Python version and ensure pip is up-to-date
RUN python3 --version && \
    python3 -m ensurepip --upgrade && \
    python3 -m pip install --upgrade pip

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Pull models during build (requires temporary Ollama server)
RUN ollama serve & \
    sleep 5 && \
    ollama pull llama3.2:3b && \
    ollama pull mxbai-embed-large:335m && \
    pkill ollama

# Set application directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Startup script to run both Ollama and FastAPI
RUN cat <<'EOF' > /start.sh
#!/bin/bash
set -e

# Start Ollama in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
while ! ollama list >/dev/null 2>&1; do
    sleep 1
done

# Start FastAPI
exec uvicorn main:app --host 0.0.0.0 --port 8000
EOF

RUN chmod +x /start.sh

# Expose FastAPI and Ollama ports
EXPOSE 8000 11434

# Run startup script
CMD ["/start.sh"]
