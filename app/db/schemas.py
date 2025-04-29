# app/db/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

# Files
class FileBase(BaseModel):
    original_filename: str
    description: Optional[str] = None

class FileCreate(FileBase):
    pass

class FileUpdate(BaseModel):
    description: Optional[str] = None
    is_processed: Optional[bool] = None

class FileResponse(FileBase):
    id: int
    filename: str
    file_path: str
    file_size: float
    file_type: str
    uploaded_at: datetime.datetime
    last_accessed: Optional[datetime.datetime] = None
    is_processed: bool

    class Config:
        from_attributes = True

# Analysis
class AnalysisBase(BaseModel):
    title: str
    description: Optional[str] = None
    file_id: int

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisResponse(AnalysisBase):
    id: int
    result_path: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Usage
class UsageBase(BaseModel):
    run_id: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model_name: Optional[str] = None

class UsageCreate(UsageBase):
    analysis_id: Optional[int] = None

class UsageResponse(UsageBase):
    id: int
    analysis_id: Optional[int] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

# Agent Response
class VisualizationInfo(BaseModel):
    path: str
    description: str
    key_insights: List[str]

class ActionStep(BaseModel):
    step: int
    description: str

class DecisionJustification(BaseModel):
    decision: str
    justification: str
    tool_used: str

class AgentResponse(BaseModel):
    action_plan: List[ActionStep]
    decisions_and_justifications: List[DecisionJustification]
    observations: List[str]
    visualizations: List[VisualizationInfo]
    summary: str
    next_steps: List[str]
    conclusion: str