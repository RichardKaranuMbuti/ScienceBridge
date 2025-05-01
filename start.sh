#!/bin/bash
set -e

# Print startup message
echo "Starting Science Bridge application..."

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the FastAPI application
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000