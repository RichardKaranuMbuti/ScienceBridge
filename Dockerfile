FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV HOME=/root
ENV DOCKER_CONTAINER=true

# Install system dependencies including python3-venv and pip
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-venv \
    python3-dev \
    python3-pip \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install wheel
RUN python -m pip install --upgrade pip setuptools wheel

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-install common data science packages to avoid runtime installation delays
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    scikit-learn \
    plotly \
    statsmodels \
    jupyter \
    ipython

# Copy project files
COPY . .

# Create .dockerignore file
RUN echo "*.csv\n*.png\n*.jpeg\n*.jpg\nscience_agent.db\n.env\nvenv/\nvenvs/\ndatasets/" > .dockerignore

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create necessary directories with proper permissions
RUN mkdir -p /app/src/data/uploads \
    /app/venvs \
    /tmp/matplotlib \
    /app/temp \
    /app/plots \
    && chmod -R 755 /app/venvs \
    && chmod -R 755 /app/plots \
    && chmod -R 755 /app/temp \
    && chmod -R 777 /tmp/matplotlib

# Set proper ownership for matplotlib config directory
RUN chown -R root:root /tmp/matplotlib

# Verify pip installation
RUN pip --version && python --version

# Note: Running as root for now - consider switching to non-root user for production security

# Expose port
EXPOSE 8000 

# Use the startup script as entrypoint
ENTRYPOINT ["./start.sh"]