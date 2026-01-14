import asyncio, os
from textwrap import dedent

from dotenv import load_dotenv
from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.oxylabs import OxylabsTools
from agno.models.huggingface import HuggingFace


# Load environment variables from a .env file
load_dotenv()
api_key = os.getenv("HF_API_KEY")
model=HuggingFace(id='', api_key=api_key, max_tokens=500)

# SERP analysis agent
serp_agent = Agent(
    # Use Oxylabs Google Search scraper
    tools=[OxylabsTools().search_google],

    model=model,
    role="You are Google Search agent that can gather SERP results for given keyword.",
    instructions=dedent("""
        Search Google with a keyword and analyze the SERP result.
        Use only the extracted data to identify: 1) Brand visibility, 2) Top competitors by position, 3) Search intent (informational/commercial/transactional).
        Flag high-value URLs (positions 1-3, competitor pages, relevant content) for deeper analysis.
        Return Markdown-formatted data with keyword, brand visibility score, competitor list, and intent classification.
    """),
    markdown=True
)

# Website analysis agent
web_agent = Agent(
    # Use Oxylabs generic website scraper
    tools=[OxylabsTools().scrape_website],

    model=model,
    role="You are a web scraping agent that can gather data from websites.",
    instructions=dedent("""
        Scrape and analyze each URL one by one. Use JavaScript rendering.
        Extract and analyze: 1) Primary keywords (frequency and prominence), 2) Content structure (headings, word count), 3) Meta tags, 4) Internal/external links count.
        Identify content gaps and assess content quality signals (readability, keyword density, topic coverage depth).
        Return key insights for each URL in a concise and Markdown-formatted report.
    """),
    markdown=True
)

# Team that works together and produces a final report
team = Team(
    model=model,
    members=[serp_agent, web_agent],
    name="SEO Analysis Team",
    role="Coordinate SERP and web analysis agents and draft a final report.",
    instructions=dedent("""
        First, have the SERP agent analyze Google SERP for a given keyword and return URLs for further analysis.
        Then, pass the URLs to the web agent for a deep dive into top-performing and competitor pages.
        In the end, make a joint report of the keyword-by-keyword analysis from the SERP and web agent.
        The report must contain an actionable SEO strategy with Executive Summary, Keyword Analysis, Competitive Landscape, Content Gap Analysis, and Recommendations.
    """),
    markdown=True,
    share_member_interactions=True
)


async def main():
    # Example SEO analysis prompt
    user_prompt = dedent("""
        Find Google.com SEO insights for 'best running shoes 2025'.
        Brand name for tracking is 'Adidas'.
    """)
    
    result = await team.arun(user_prompt)
    print(result)

    # Save the final report to a Markdown file
    with open("seo_analysis.md", "w") as file:
        file.write(result.content)


if __name__ == "__main__":
    asyncio.run(main())