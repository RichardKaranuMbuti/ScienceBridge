# ScienceBridge Documentation

## Table of Contents

- [Database Management](#database-management)
- [FastAPI Application](#fastapi-application)
- [Docker Setup](#docker-setup)
- [Environment Variables](#environment-variables)
- [Development Guidelines](#development-guidelines)
- [Deployment Options](#deployment-options)

## Database Management

ScienceBridge uses Alembic for database migrations. Here are the common commands:

```bash
# Check the current state of your database
alembic current

# Generate a new migration with a descriptive name
alembic revision --autogenerate -m "add_usage_table"

# Apply the migration to update the database
alembic upgrade head

# Revert the latest migration
alembic downgrade -1

# Check migration history
alembic history
```

## FastAPI Application

ScienceBridge is built with FastAPI and packaged as a Docker container for easy deployment and scaling.

### Prerequisites

- Docker installed on your system
- Docker Hub account (for publishing)

## Docker Setup

### Building the Docker Image

To build the Docker image locally:

```bash
# Build the image
docker build -t science-bridge .
```

### Running the Container

```bash
# Run the container in detached mode (-d), map port 8000, and give it a name
docker run -d -p 8000:8000 --name science-bridge-container science-bridge

# To see logs of the running container
docker logs science-bridge-container

# To stop the container
docker stop science-bridge-container

# To remove the container after stopping
docker rm science-bridge-container
```

> **Note**: When the container starts for the first time, the creation of a separated virtual environment for the agent takes a few minutes. You can check the logs of your container to monitor the progress.

### Using Pre-built Image

To use the pre-built image from Docker Hub:

```bash
# Pull the image
docker pull zaibaki/science-bridge:latest

# Tag the Docker image with your Docker Hub username
docker tag science-bridge username/science-bridge:latest

# Push the image to Docker Hub
docker push username/science-bridge:latest
```

Replace `username` with your Docker Hub username.

## Environment Variables

ScienceBridge uses environment variables for configuration. Create a `.env` file at the root of your project with the required variables before building the Docker image.

Example `.env` file:

```
DATABASE_URL=sqlite:///./science_agent.db
DEBUG=False
API_KEY=your_api_key_here
```

### Using Environment Variables with Docker

Use the `--env-file` flag (recommended):

```bash
docker run --env-file .env zaibaki/science-bridge
docker run -p 8000:8000 --env-file .env zaibaki/science-bridge # port mapping

```

## Development Guidelines

For local development without Docker:

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
uvicorn main:app --reload
```

## Deployment Options

### Ignored Files in Docker

The following files are ignored when building the Docker image:

- CSV files (\*.csv)
- PNG files (\*.png)
- JPEG files (_.jpeg, _.jpg)
- Database file (science_agent.db)
- Environment variables (.env)
- Virtual environments (venv/, venvs/)
- Datasets directory (datasets/)

### Publishing to Docker Hub

1. Login to Docker Hub:

```bash
docker login
```

2. Push the image to Docker Hub:

```bash
docker push username/science-bridge:latest
```
