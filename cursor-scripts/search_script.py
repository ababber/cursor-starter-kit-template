#!/usr/bin/env python3
"""
Gemini Search Tool - Web search via Gemini's Google Search grounding.

Usage:
    python search_script.py "your search query"
    
Requires GEMINI_API_KEY in environment or .env file.
"""

import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types


def search(query: str) -> str:
    """
    Performs a Google Search using Gemini's grounding capabilities.
    Returns real-time web results.
    """
    load_dotenv()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not set"
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"],
            ),
        )

        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
        else:
            return "No results found."

    except Exception as e:
        return f"Error performing search: {str(e)}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_script.py 'your query'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    result = search(query)
    print(result)
