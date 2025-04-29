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


def extract_final_result(agent_result):
    """
    Extract the final structured result from the agent output.
    Handles various formats including JSON enclosed in code blocks.
    """
    import json
    import re
    
    # If agent_result is already a dict with a 'messages' key, extract the messages
    messages = agent_result.get('messages', []) if isinstance(agent_result, dict) else []
    
    # Find the last AI message in the list
    ai_messages = [msg for msg in messages if hasattr(msg, 'content') and getattr(msg, 'type', None) != 'tool']
    
    # If no AI messages found, return None
    if not ai_messages:
        return None
    
    # Get the content of the last AI message
    last_message_content = ai_messages[-1].content if ai_messages else None
    
    if not last_message_content:
        return None
    
    # Try to extract JSON from the message content
    # First check if content is enclosed in code block with json formatter
    json_code_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    match = re.search(json_code_pattern, last_message_content)
    
    if match:
        # Extract the content from the code block
        extracted_content = match.group(1).strip()
        # Make sure it starts with a curly brace (JSON object)
        if extracted_content.startswith('{'):
            json_str = extracted_content
        else:
            # If it doesn't start with {, try to find JSON object within the extracted content
            json_obj_match = re.search(r'(\{[\s\S]*\})', extracted_content)
            json_str = json_obj_match.group(1) if json_obj_match else extracted_content
    else:
        # If no code block found, try to extract the entire JSON object from the content
        json_pattern = r'(\{[\s\S]*?\})(?:\s*$|\s*[^}])'
        match = re.search(json_pattern, last_message_content)
        if match:
            json_str = match.group(1)
        else:
            # Last resort: try to find any JSON object in the content
            json_str = last_message_content
    
    # Debug print
    print(f"Attempting to parse JSON: {json_str[:100]}...")
    
    # Try to parse the extracted content as JSON
    try:
        parsed_json = json.loads(json_str)
        
        # Verify it has the expected structure (for validation)
        required_fields = ['action_plan', 'decisions_and_justifications', 'observations', 
                         'visualizations', 'summary', 'next_steps', 'conclusion']
        
        # Check if the parsed JSON has the required fields
        missing_fields = [field for field in required_fields if field not in parsed_json]
        if missing_fields:
            print(f"Parsed JSON is missing required fields: {missing_fields}")
            # Try to extract a more complete JSON object
            complete_json_pattern = r'(\{[\s\S]*?"conclusion"[\s\S]*?\})'
            match = re.search(complete_json_pattern, last_message_content)
            if match:
                try:
                    complete_json = json.loads(match.group(1))
                    return complete_json
                except json.JSONDecodeError as e:
                    print(f"Failed to parse complete JSON: {str(e)}")
        
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        
        # Cleanup the JSON string and try again
        try:
            # Fix common JSON syntax issues
            cleaned_json_str = json_str.replace("'", "\"")  # Replace single quotes with double quotes
            cleaned_json_str = re.sub(r',(\s*[\]}])', r'\1', cleaned_json_str)  # Remove trailing commas
            parsed_json = json.loads(cleaned_json_str)
            return parsed_json
        except json.JSONDecodeError:
            pass
        
        # As a final fallback, try to find any complete JSON structure in the entire message
        try:
            # This pattern looks for a complete JSON object with all required fields
            complete_pattern = r'\{[\s\S]*?"action_plan"[\s\S]*?"decisions_and_justifications"[\s\S]*?"observations"[\s\S]*?"visualizations"[\s\S]*?"summary"[\s\S]*?"next_steps"[\s\S]*?"conclusion"[\s\S]*?\}'
            match = re.search(complete_pattern, last_message_content)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # If we still can't find a complete JSON, look for any JSON objects and check if they're valid
            json_candidates = re.findall(r'(\{[\s\S]*?\})', last_message_content)
            for candidate in sorted(json_candidates, key=len, reverse=True):  # Try the longest candidates first
                try:
                    result = json.loads(candidate)
                    # Check if it has at least some of the required fields
                    if isinstance(result, dict) and any(field in result for field in required_fields):
                        return result
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"Error in fallback JSON extraction: {str(e)}")
        
        print("All JSON extraction attempts failed")
        return None


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
                    {"step": 1, "description": "Process didnt complete"},
                ],
                "decisions_and_justifications": [
                    {"decision": "None",
                     "justification": "None",
                      "tool_used": "None"}
                ],
                "observations": ["Analysis Failed"],
                "visualizations": [],
                "summary": "Analysis wasnt completed.",
                "next_steps": ["None"],
                "conclusion": "Agent run failed or didnt complete."
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
        print("final result:", result)
        return result
        
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}"
        )