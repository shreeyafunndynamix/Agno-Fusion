import os
from agno.agent import Agent
from agno.tools.scrapegraph import ScrapeGraphTools
from agno.models.huggingface import HuggingFace
from dotenv import load_dotenv
load_dotenv()   
api_key = os.getenv("SGAI_API_KEY")
hfapi_key = os.getenv("HF_API_KEY")

# Default behavior - only smartscraper enabled
scrapegraph = ScrapeGraphTools(enable_searchscraper=True, api_key=api_key)

agent = Agent(
    model=HuggingFace(id='HuggingFaceTB/SmolLM3-3B', api_key=hfapi_key, max_tokens=500), 
    tools=[scrapegraph],
    markdown=True)

# Use smartscraper to extract specific information
agent.print_response("""
Use smartscraper to extract the following from https://www.giva.co/:
- News articles
- Headlines
- Images links ending to image file formats like .jpg, .png, .webp
- Prices
- reviews of most love product                                         

""", stream=True)