"""
OpenAI integration for article summarization
"""

import logging
import openai
import os
import sys
# Import the API key from config
from config.config import OPENAI_API_KEY

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

def summarize_with_openai(text):
    """
    Summarizes text using OpenAI's GPT model.
    
    Args:
        text (str): Text to summarize
        
    Returns:
        str: Summarized text or empty string if error occurs
    """
    try:
        user_prompt = f"Please provide a concise summary of this article: {text}"
        completion = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news articles."},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return ""