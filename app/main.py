# app/main.py
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

from app.api.endpoints import agent, files
from app.db.base import engine, Base

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Ensure data directories exist
for path in ["src/data/uploads", "src/data/graphs"]:
    Path(path).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Science Agent API",
    description="API for scientific data analysis using LangGraph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/data", StaticFiles(directory="src/data"), name="data_static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

@app.get("/")
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("base.html", {"request": request, "active_page": "home"})

@app.get("/files")
async def file_list(request: Request):
    """Render the file list page."""
    return templates.TemplateResponse("list.html", {"request": request, "active_page": "files"})

@app.get("/upload")
async def file_upload(request: Request):
    """Render the file upload page."""
    return templates.TemplateResponse("upload.html", {"request": request, "active_page": "upload"})

@app.get("/chat")
async def chat_page(request: Request):
    """Render the chat page."""
    return templates.TemplateResponse("chat.html", {"request": request, "active_page": "chat"})

@app.get("/chat-all-datasets")
async def chat_page(request: Request):
    """Render the chat page."""
    return templates.TemplateResponse("chat_all.html", {"request": request, "active_page": "chat_all_datasets"})