from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
from src.agent.state import State
from src.helpers.fetch_local_data import fetch_local_data
from src.agent.tools import ask_ai, execute_python, human_assistance

load_dotenv()

path = 'src/data'

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

dataset = fetch_local_data(path)
print(f"Dataset loaded from {path}: {dataset}")

# Define system prompt for the scientific discovery agent
SYSTEM_PROMPT = """You are ScienceBridge, an advanced scientific discovery agent designed to accelerate research across distributed scientific repositories.

CAPABILITIES:
- You are given this dataset which is in csv: {dataset} in this path {path}: 
- Generate Python code to analyze scientific datasets
- You are provided with a Python execution environment
- Generate analysis, summaries, visualizations (graphs, charts) from data
- Create statistical models to test correlations between factors
- Visualize findings in interpretable formats
- Design follow-up queries based on results

WORKFLOW:
1. Understand the user's research question
2. Decompose it into testable hypotheses
3. Identify relevant data to use 
4. Generate Python analysis code for each data source
5. Integrate findings to validate or refute hypotheses
6. Identify gaps requiring additional data
7. Propose next experimental directions

When generating Python code:
- Write clean, well-documented code
- Include error handling
- Organize code logically
- Use efficient data processing techniques
- Document expected outputs and their interpretation

Always think step-by-step. Break complex problems into smaller logical components. Explain your reasoning and methodology clearly.
Return the final clear answer relevant to the user's question. If you need to use a tool, include the tool call in your response.
"""

def create_agent():
    """Create an agent with tools."""
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
    # Do NOT include any customization of tool_call_id in the tools themselves
    chain = prompt | llm.bind_tools([ask_ai, execute_python, human_assistance])
    
    return chain


def run_agent(state: State):
    """Run the agent on the current state."""
    llm_with_tools = create_agent()
    response = llm_with_tools.invoke({
                "messages": state["messages"],
                "dataset": dataset,
                "path": path
            })

    # Return the updated state with the new AI message appended
    return {"messages": state["messages"] + [response]}

def should_continue(state: State) -> str:
    """Determine if the agent should continue running or use tools."""
    # Get the last message
    last_message = state["messages"][-1]
    
    # Debug output
    print(f"Last message type: {type(last_message)}")
    has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
    print(f"Last message has tool_calls? {has_tool_calls}")
    
    if has_tool_calls:
        print(f"Tool calls: {last_message.tool_calls}")
        return "tools"
    
    # Otherwise, we're done with this iteration
    print("No tool calls found, ending.")
    return "end"