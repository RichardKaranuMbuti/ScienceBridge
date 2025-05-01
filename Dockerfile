FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create .dockerignore file to ignore the same files as in .gitignore
RUN echo "*.csv\n*.png\n*.jpeg\n*.jpg\nscience_agent.db\n.env\nvenv/\nvenvs/\ndatasets/" > .dockerignore

# Create startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8000


# Use the startup script as entrypoint
ENTRYPOINT ["./start.sh"]
