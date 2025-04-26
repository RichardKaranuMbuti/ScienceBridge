from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.agent.state import State
from src.agent.tools import fetch_dataset_info, execute_python, db_query_tool
from src.helpers.fetch_local_data import fetch_local_data
import os
from dotenv import load_dotenv
load_dotenv()

# Define path to data directory
path = 'src/data'

# Load dataset from the path
dataset = fetch_local_data(path)
print(f"Dataset loaded from {path}: {dataset}")

# Define system prompt for the scientific agent
SYSTEM_PROMPT = """You are ScienceBridge, an advanced scientific discovery agent designed to accelerate research.

CAPABILITIES:
- You are given this dataset which is in csv: {dataset} in this path {path}
- Analyze scientific datasets, discover patterns, and generate insights
- Generate visualizations to illustrate findings
- Provide clear, evidence-backed conclusions

WORKFLOW:
1. Understand the user's research question
2. Use available tools to explore and analyze data
3. Generate visualizations to illustrate findings
4. Provide clear, evidence-backed conclusions

When generating Python code:
- Write clean, well-documented code
- Include error handling
- Organize code logically 
- Use efficient data processing techniques

Always think step-by-step. Break complex problems into smaller logical components.
Explain your reasoning and methodology clearly.

The available tools are:
- fetch_dataset_info: Get information about available datasets
- execute_python: Run Python code for data analysis and visualization
- db_query_tool: Run SQL queries against databases
"""

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_agent():
    """Create the agent with tools."""
    # Initialize the language model
    llm = ChatOpenAI(
        model="gpt-4o",
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
        [fetch_dataset_info, execute_python, db_query_tool], 
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