# app/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime
import os

Base = declarative_base()

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    original_filename = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Float)  # in KB
    file_type = Column(String)  # csv, xlsx, etc.
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    is_processed = Column(Boolean, default=False)
    
    def as_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "description": self.description,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "is_processed": self.is_processed
        }

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    file_id = Column(Integer, index=True)  # No FK constraint for simplicity
    result_path = Column(String, nullable=True)  # Path to result JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "file_id": self.file_id,
            "result_path": self.result_path,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Usage(Base):
    __tablename__ = "usages"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    model_name = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def as_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "analysis_id": self.analysis_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }