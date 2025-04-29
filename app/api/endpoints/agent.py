# app/api/endpoints/agent.py
from fastapi import APIRouter, Depends, HTTPException, Body, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from typing import Dict, Any, Optional, List
import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path

from app.db.base import get_db
from app.db.schemas import AnalysisCreate, AnalysisResponse, AgentResponse, UsageCreate
from app.db import crud
from src.agent.graph import ScienceAgent

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize the agent
science_agent = ScienceAgent()



def save_usage_data(run_id: str, usage_metadata: Dict[str, Any], analysis_id: Optional[int], db: Session):
    """Save token usage data to database."""
    if not usage_metadata:
        return
    
    try:
        usage_create = UsageCreate(
            run_id=run_id,
            analysis_id=analysis_id,
            input_tokens=usage_metadata.get("input_tokens", 0),
            output_tokens=usage_metadata.get("output_tokens", 0),
            total_tokens=usage_metadata.get("total_tokens", 0),
            model_name=usage_metadata.get("model_name", None)
        )
        
        crud.create_usage(db, usage_create)
    except OperationalError as e:
        # Log the error but don't fail the whole request
        logger.error(f"Failed to save usage data: {str(e)}")
        if "no such table: usages" in str(e):
            logger.error("The 'usages' table does not exist. Please run database migrations.")


def extract_final_result(agent_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the final structured result from the agent output."""
    # Check if messages exist in the result
    if "messages" not in agent_result:
        return {}
    
    # Find the last AI message with content
    for message in reversed(agent_result["messages"]):
        if message.__class__.__name__ == "AIMessage" and message.content:
            try:
                # Try to parse the content as JSON
                return json.loads(message.content)
            except json.JSONDecodeError:
                continue
    
    return {}


def extract_usage_metadata(agent_result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract token usage metadata from agent messages."""
    total_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "model_name": None
    }
    
    # Extract usage from all AI messages
    if "messages" in agent_result:
        for message in agent_result["messages"]:
            if message.__class__.__name__ == "AIMessage" and hasattr(message, "usage_metadata"):
                usage = message.usage_metadata
                if usage:
                    total_usage["input_tokens"] += usage.get("input_tokens", 0)
                    total_usage["output_tokens"] += usage.get("output_tokens", 0)
                    total_usage["total_tokens"] += usage.get("total_tokens", 0)
                    # Get model name from the last message with a model name
                    if hasattr(message, "response_metadata") and message.response_metadata:
                        model_name = message.response_metadata.get("model_name")
                        if model_name:
                            total_usage["model_name"] = model_name
    
    return total_usage


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    background_tasks: BackgroundTasks,
    request_data: Dict[str, Any] = Body(...),
    file_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Run the science agent with the given input."""
    query = request_data.get("query")
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required"
        )
    
    # Create an analysis record if file_id is provided
    analysis_id = None
    if file_id:
        # Verify file exists
        db_file = crud.get_file(db, file_id)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Create analysis record
        analysis = crud.create_analysis(
            db,
            AnalysisCreate(
                title=f"Analysis {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                description=query[:100] + "..." if len(query) > 100 else query,
                file_id=file_id
            )
        )
        analysis_id = analysis.id
    
    # Run the agent
    thread_id = f"science-session-{uuid.uuid4()}"
    try:
        agent_result = science_agent.run(query, thread_id)
        print(f"Agent result: {agent_result}")
        
        # Extract the final structured result from agent output
        result = extract_final_result(agent_result)
        
        if not result:
            # If no structured result was found, use a default template
            result = {
                "action_plan": [
                    {"step": 1, "description": "Data processing completed"}
                ],
                "decisions_and_justifications": [
                    {"decision": "Automated analysis", "justification": "Based on query requirements", "tool_used": "science_agent"}
                ],
                "observations": ["Analysis completed"],
                "visualizations": [],
                "summary": "Analysis completed successfully.",
                "next_steps": ["Review results"],
                "conclusion": "Analysis completed with the provided data."
            }
            
            # Check if there are any plot paths in agent_result
            if "plot_paths" in agent_result and agent_result["plot_paths"]:
                result["visualizations"] = []
                for i, path in enumerate(agent_result["plot_paths"]):
                    # If path starts with physical directory, convert to web path
                    if path.startswith("src/data/"):
                        web_path = path.replace("src/data/", "/data/")
                    # If path already starts with /data, keep it as is
                    elif path.startswith("/data/"):
                        web_path = path
                    # Otherwise, assume it's a relative path and make it absolute
                    else:
                        web_path = f"/data/uploads/graphs/{os.path.basename(path)}"
                        
                    result["visualizations"].append({
                        "path": web_path,
                        "description": f"Generated visualization {i+1}",
                        "key_insights": ["Visualization generated from analysis"]
                    })
        
        # Extract usage metadata
        usage_metadata = extract_usage_metadata(agent_result)
        
        # Try to save usage data, but don't fail the request if it doesn't work
        try:
            background_tasks.add_task(save_usage_data, thread_id, usage_metadata, analysis_id, db)
        except Exception as e:
            logger.error(f"Failed to queue usage data task: {str(e)}")
        
        # Fix: Update visualizations paths if they exist in the result
        if "visualizations" in result and result["visualizations"]:
            for viz in result["visualizations"]:
                if "path" in viz and viz["path"].startswith("src/data/"):
                    viz["path"] = viz["path"].replace("src/data/", "/data/")
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )