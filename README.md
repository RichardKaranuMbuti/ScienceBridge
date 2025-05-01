# ScienceBridge

An agent that accelerates scientific research by autonomously navigating across provided science datasets, generating hypotheses, and validating them through code

# Generate a new migration with a descriptive name:

alembic revision --autogenerate -m "add_usage_table"

# To check the current state of your database

alembic current

# Generate a new migration

alembic revision --autogenerate -m "add_usage_table"

# Apply the migration to update the database

alembic upgrade head

# If you need to revert the migration

alembic downgrade -1

# Check migration history

alembic history

# FastAPI Application

## Description

This is a FastAPI application dockerized for easy deployment and scaling.

## Prerequisites

- Docker installed on your system
- Docker Hub account (for publishing)

## Building the Docker Image

To build the Docker image of the application:

```bash
docker build -t fastapi-app .
```

To tag the Docker image with your Docker Hub username:

```bash
docker tag fastapi-app username/fastapi-app:latest
```

Replace `username` with your Docker Hub username.

## Running the Docker Container

To run the container locally:

```bash
docker run -d -p 8000:8000 username/fastapi-app
```

The API will be accessible at http://localhost:8000

## Environment Variables

The application uses environment variables for configuration. Create a `.env` file at the root of your project with the required variables before building the Docker image.

Example `.env` file:

```
DATABASE_URL=sqlite:///./science_agent.db
DEBUG=False
API_KEY=your_api_key_here
```

Use the --env-file Flag (Recommended)
This option lets you pass your entire .env file:
bashdocker run -d -p 8000:8000 --name science-bridge-container \
 --env-file ./.env \
 science-bridge

## Publishing to Docker Hub

1. Login to Docker Hub:

```bash
docker login
```

2. Push the image to Docker Hub:

```bash
docker push username/fastapi-app:latest
```

## Development

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

## Ignored Files in Docker

The following files are ignored when building the Docker image:

- CSV files (\*.csv)
- PNG files (\*.png)
- JPEG files (_.jpeg, _.jpg)
- Database file (science_agent.db)
- Environment variables (.env)
- Virtual environments (venv/, venvs/)
- Datasets directory (datasets/)

build the image
docker build -t science-bridge .

# Run the container in detached mode (-d), map port 8000, and give it a name

docker run -d -p 8000:8000 --name science-bridge-container science-bridge

# To see logs of the running container

docker logs science-bridge-container

# To stop the container

docker stop science-bridge-container

# To remove the container after stopping

docker rm science-bridge-container

When the container starts for first time the creation of separated virtual environment for the agent takes some few minutes
you can check the logs of your container by running
docker logs science-bridge-container or what you named your container
