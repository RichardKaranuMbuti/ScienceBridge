# src/openai_tool/client.py
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def OpenAIClient(query: str, system_prompt: str = "You are a helpful scientific assistant.") -> str:
    """
    Sends a query to OpenAI's GPT-4o model and returns the response.
    
    :param query: The user query string.
    :param system_prompt: The system message to guide the assistant behavior.
    :return: The assistant's reply as a string.
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the user question: {query}"},
        ],
    )
    return completion.choices[0].message.content