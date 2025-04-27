from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.agent.state import State
from src.agent.tools import fetch_dataset_info, execute_python, db_query_tool, install_python_packages, ask_ai
from src.helpers.fetch_local_data import fetch_local_data
from src.agent.prompts import SYSTEM_PROMPT
import os
from dotenv import load_dotenv
load_dotenv()

# Define path to data directory
path = 'src/data'

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
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{messages}")
    ])
    
    # Chain prompt with language model and bind tools
    agent = prompt | llm.bind_tools(
        [fetch_dataset_info, execute_python, db_query_tool, install_python_packages, ask_ai], 
    )
    
    return agent

def run_agent(state: State):
    """Run the agent on the current state."""
    agent = create_agent()
    
    # Pass the dataset and path variables to the agent invocation
    response = agent.invoke({
        "messages": state["messages"],
        "dataset": dataset,
        "path": path
    })
    
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