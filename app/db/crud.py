# app/db/crud.py
from sqlalchemy.orm import Session
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict

from app.db.models import File, Analysis,Usage
from app.db.schemas import FileCreate, FileUpdate, AnalysisCreate,UsageCreate

def create_file(db: Session, file_create: FileCreate, uploaded_file, file_path: str) -> File:
    """Create a new file record and save the file."""
    # Generate a unique filename
    unique_filename = f"{uuid.uuid4()}_{uploaded_file.filename}"
    
    # Get file size in KB
    file_size = os.path.getsize(file_path) / 1024
    
    # Get file extension
    file_type = os.path.splitext(uploaded_file.filename)[1].lower().lstrip('.')
    
    # Create DB record
    db_file = File(
        filename=unique_filename,
        original_filename=uploaded_file.filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        description=file_create.description
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file(db: Session, file_id: int) -> Optional[File]:
    """Get a file by ID."""
    file = db.query(File).filter(File.id == file_id).first()
    if file:
        file.last_accessed = datetime.utcnow()
        db.commit()
        db.refresh(file)
    return file

def get_files(db: Session, skip: int = 0, limit: int = 100) -> List[File]:
    """Get all files with pagination."""
    return db.query(File).offset(skip).limit(limit).all()

def update_file(db: Session, file_id: int, file_update: FileUpdate) -> Optional[File]:
    """Update a file record."""
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        update_data = file_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_file, key, value)
        db.commit()
        db.refresh(db_file)
    return db_file

def delete_file(db: Session, file_id: int) -> bool:
    """Delete a file and its record."""
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        try:
            # Delete the physical file
            if os.path.exists(db_file.file_path):
                os.remove(db_file.file_path)
            # Delete the DB record
            db.delete(db_file)
            db.commit()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            db.rollback()
    return False


# Usage operations
def create_usage(db: Session, usage: UsageCreate) -> Usage:
    db_usage = Usage(
        run_id=usage.run_id,
        analysis_id=usage.analysis_id,
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
        model_name=usage.model_name
    )
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage

def get_usage_by_run_id(db: Session, run_id: str) -> Optional[Usage]:
    return db.query(Usage).filter(Usage.run_id == run_id).first()

def get_usage_by_analysis_id(db: Session, analysis_id: int) -> List[Usage]:
    return db.query(Usage).filter(Usage.analysis_id == analysis_id).all()

def get_total_usage(db: Session) -> Dict[str, int]:
    result = db.query(
        Usage.model_name,
        db.func.sum(Usage.input_tokens).label("total_input"),
        db.func.sum(Usage.output_tokens).label("total_output"),
        db.func.sum(Usage.total_tokens).label("total")
    ).group_by(Usage.model_name).all()
    
    return {
        model: {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total
        }
        for model, input_tokens, output_tokens, total in result
    }