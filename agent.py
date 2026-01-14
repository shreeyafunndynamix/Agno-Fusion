#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.google import Gemini  # Import HuggingFace instead of OpenAI
from agno.models.huggingface import HuggingFace
from agno.tools.duckduckgo import DuckDuckGoTools

load_dotenv()
# 1. Set your API Key (Or do this in your terminal export)
# os.environ["HF_API_KEY"] = "your-huggingface-key-here"


api_key = os.getenv("HF_API_KEY")

if api_key:
    # Create an agent with HuggingFace
    agent = Agent(
        name="Jewelry Design Agent",
        # model=Gemini(id='gemini-2.5-flash', api_key=api_key, max_output_tokens=500),     # "gemini-1.5-pro"
        model=HuggingFace(id='HuggingFaceTB/SmolLM3-3B', api_key=api_key, max_tokens=500),     # "gemini-1.5-pro"
        description="You are an advanced research assistant. Cross-reference multiple sources to ensure accuracy.",
        instructions=[
                "Always call the search tool.",
                "Pass a detailed search query.",
                "Return only URLs."
                "Only return direct image URLs.",
                "Each URL must end with .jpg, .png, or .webp",
                "One URL per line.",
                "Do not include any additional text or formatting."
        ],
        tools=[DuckDuckGoTools()],  # Using DuckDuckGo search tool
        expected_output= "links",

        markdown=True
    
    )
    
    if __name__ == "__main__":
        print("✨ Jewelry Design Agent (HF) initialized successfully!")
        agent.print_response("Provide me latest 2 pendant designs image url only?")
        print("✅ Task completed.")

else:
    print("❌ Error: HF_API_KEY not found.")
    print("Please run: export HF_API_KEY='your-key-here'")