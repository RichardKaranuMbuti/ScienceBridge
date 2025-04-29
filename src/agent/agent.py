from typing import Literal, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.agent.state import State
from src.agent.tools import (
    fetch_dataset_info, 
    execute_python, 
    db_query_tool,
    install_python_packages, 
    ask_ai,
    explain_graph,
    print_tool_execution
)
from src.helpers.fetch_local_data import fetch_local_data
from src.agent.prompts import SYSTEM_PROMPT
import os
import json
from dotenv import load_dotenv
load_dotenv()

# Define path to data directory
path = 'src/data/uploads'

image_path = 'src/data/graphs'
# Load dataset from the path
dataset = fetch_local_data(path)

print(f"Dataset loaded from {path}: {dataset}")

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


model = "gpt-4o-2024-08-06" #"gpt-4o"

def create_agent():
    """Create the agent with tools."""
    # Initialize the language model
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=2000,
        
    )
    
    # Create prompt template with enhanced system message
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{messages}")
    ])
    
    # Define tools explicitly to ensure they are properly serializable
    tools = [
        fetch_dataset_info, 
        execute_python, 
        db_query_tool, 
        install_python_packages, 
        ask_ai, 
        explain_graph
    ]
    
    # Chain prompt with language model and bind tools
    agent = prompt | llm.bind_tools(tools, tool_choice="auto")
    
    return agent

def run_agent(state: State) -> Dict[str, Any]:
    """Run the agent on the current state."""
    agent = create_agent()
    
    print_tool_execution("LLM-AGENT", "RUNNING", "Generating response or tool calls...")
    
    # Pass the dataset and path variables to the agent invocation
    response = agent.invoke({
        "messages": state["messages"],
        "dataset": dataset,
        "path": path,
        "image_path": image_path
    })
    
    # Check if the agent is making a tool call or providing a final answer
    has_tool_calls = hasattr(response, "tool_calls") and response.tool_calls
    if has_tool_calls:
        print_tool_execution("LLM-AGENT", "SUCCESS", "Tool calls generated")
    else:
        print_tool_execution("LLM-AGENT", "SUCCESS", "Final response generated")
    
    # Return the AI's response
    return {"messages": [response]}

def should_continue(state: State) -> Literal["tools", "end"]:
    """Determine if the agent should continue with tools or end."""
    # Get the last message
    last_message = state["messages"][-1]
    
    # Check if the last message has tool calls
    has_tool_calls = hasattr(last_message, "tool_calls") and last_message.tool_calls
    
    if has_tool_calls:
        return "tools"
    else:
        return "end"