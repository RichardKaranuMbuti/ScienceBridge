# app/api/endpoints/files.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path

from app.db.base import get_db
from app.db.models import File
from app.db.schemas import FileCreate, FileResponse, FileUpdate
from app.db import crud

router = APIRouter()

UPLOAD_DIR = "src/data/uploads"
# Ensure upload directory exists
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a new file (CSV or Excel)."""
    # Validate file type
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ['.csv', '.xlsx', '.xls']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV and Excel files are supported"
        )
    
    # Save the file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    finally:
        file.file.close()
    
    # Create file record
    file_create = FileCreate(
        original_filename=file.filename,
        description=description
    )
    
    try:
        db_file = crud.create_file(db, file_create, file, file_path)
        return FileResponse.from_orm(db_file)
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record file: {str(e)}"
        )

@router.get("/", response_model=List[FileResponse])
def get_files(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all files with pagination."""
    files = crud.get_files(db, skip=skip, limit=limit)
    return files

@router.get("/{file_id}", response_model=FileResponse)
def get_file(
    file_id: int, 
    db: Session = Depends(get_db)
):
    """Get a specific file by ID."""
    db_file = crud.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return db_file

@router.put("/{file_id}", response_model=FileResponse)
def update_file(
    file_id: int, 
    file_update: FileUpdate, 
    db: Session = Depends(get_db)
):
    """Update file information."""
    db_file = crud.update_file(db, file_id=file_id, file_update=file_update)
    if db_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return db_file

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int, 
    db: Session = Depends(get_db)
):
    """Delete a file."""
    success = crud.delete_file(db, file_id=file_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or could not be deleted"
        )
    return {"status": "success", "message": "File deleted successfully"}

@router.get("/info/types")
def get_file_types():
    """Get supported file types."""
    return {"file_types": [".csv", ".xlsx", ".xls"]}