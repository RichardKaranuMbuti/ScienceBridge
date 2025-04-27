from openai import OpenAI
import os
import base64
from dotenv import load_dotenv
from typing import List, Dict, Union

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

def encode_image(image_path: str) -> str:
    """
    Encodes an image file to a base64 string.
    
    :param image_path: Path to the image file.
    :return: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def OpenAIVisionClient(
    query: str, 
    image_paths: List[str],
    system_prompt: str = "You are a helpful visual analysis assistant. Describe what you observe in the images."
) -> str:
    """
    Analyzes images and answers queries using OpenAI's vision model.
    
    :param query: The user query about the images.
    :param image_paths: List of image file paths (local paths or URLs).
    :param system_prompt: The system message to guide the assistant behavior.
    :return: The assistant's analysis as a string.
    """
    # Prepare the content array with the user query
    content = [{"type": "text", "text": query}]
    
    # Add each image to the content array
    for path in image_paths:
        if path.startswith(("http://", "https://")):  # If it's a URL
            content.append({
                "type": "image_url",
                "image_url": {"url": path}
            })
        else:  # For local files
            base64_image = encode_image(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
    
    # Make the API call
    completion = client.chat.completions.create(
        model="gpt-4o",  # Using gpt-4o which has vision capabilities
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ],
        max_tokens=1000
    )
    
    return completion.choices[0].message.content