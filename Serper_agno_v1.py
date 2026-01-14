'''
Working on local host
Serper api
open api
2 self learning components
'''


from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from datetime import datetime
import requests
import os
from fpdf import FPDF
from fastapi import FastAPI, Request
import uvicorn
import json
from typing import List
import gradio as gr

# === API Keys ===
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# === Memory Store ===
MEMORY_FILE = "memory.json"
def store_to_memory(prompt, result):
    memory = []
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
    memory.append({"prompt": prompt, "result": result})
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

# === Custom Tool: Serper Search ===
def fetch_trending_designs(query: str):
    print("🕒 Scraping time:", datetime.now().isoformat())
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"q": f"{query} design trends"}
    response = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
    data = response.json()
    results = data.get("organic", [])

    current_year = datetime.now().year
    valid_years = [str(current_year - i) for i in range(3)]

    fresh_results = []
    for result in results:
        text = f"{result.get('title', '')} {result.get('snippet', '')}"
        if any(year in text for year in valid_years):
            fresh_results.append(result)

    return fresh_results[:3]

# === Agents ===
trend_agent = Agent(
    name="TrendAgent",
    role="Fetches and filters design inspiration trends based on a user topic.",
    instructions="Use the web_search tool to get fresh design inspiration.",
    tools={"web_search": fetch_trending_designs},
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4")
)

creative_agent = Agent(
    name="CreativeAgent",
    role="Generates layout, style, and copy based on trend input and user goal.",
    instructions="Generate a layout concept, design details, ad copy, and two tone variants.",
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4")
)

critic_agent = Agent(
    name="CriticAgent",
    role="Critiques the creative output and suggests improvements.",
    instructions="Review creative output and enhance tone, emotion, and design precision.",
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4")
)

variant_agent = Agent(
    name="VariantAgent",
    role="Creates two creative variants with different styles (bold/minimal).",
    instructions="Take a design concept and return 2 distinct versions: bold and minimalistic.",
    model=OpenAIChat(api_key=OPENAI_API_KEY, id="gpt-4")
)

creative_team = Team(
    members=[trend_agent, creative_agent, critic_agent, variant_agent],
    name="DesignGeniusTeam"
)

# === PDF Export ===
def export_to_pdf(content: str, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.splitlines():
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# === Image Generation via DALL-E (OpenAI) ===
def generate_image(prompt: str):
    dalle_endpoint = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024"
    }
    response = requests.post(dalle_endpoint, headers=headers, json=payload)
    data = response.json()
    return data["data"][0]["url"] if "data" in data else ""

# === CLI Entry ===
def main():
    user_prompt = input("🎯 Enter design goal (e.g., 'Eco brand ad'): ")
    result = creative_team.run(task=f"Create design output for: {user_prompt}", message=user_prompt)
    print("\n🎨 Final Design Output:\n")
    print(result.content)
    store_to_memory(user_prompt, result.content)
    export_to_pdf(result.content)
    image_url = generate_image(user_prompt)
    print(f"\n🖼️ Image Generated: {image_url}\n✅ Output saved to output.pdf")

# # === FastAPI ===
# app = FastAPI()

# @app.post("/generate")
# async def generate(request: Request):
#     data = await request.json()
#     prompt = data.get("prompt")
#     if not prompt:
#         return {"error": "Missing prompt"}
#     result = creative_team.run(task=f"Create design output for: {prompt}",message=prompt)
#     store_to_memory(prompt, result.content)
#     export_to_pdf(result.content, filename="api_output.pdf")
#     image_url = generate_image(prompt)
#     return {"output": result.content, "pdf": "api_output.pdf", "image": image_url}

# === Gradio UI ===
def gradio_ui():
    def run_pipeline(prompt):
        result = creative_team.run(task=f"Create design output for: {prompt}", message=prompt)
        store_to_memory(prompt, result.content)
        export_to_pdf(result.content, filename="gradio_output.pdf")
        image_url = generate_image(prompt)
        return result.content, image_url

    with gr.Blocks() as demo:
        gr.Markdown("# 🧠 DesignGenius (Agentic AI Designer)")
        prompt_input = gr.Textbox(label="Design Goal Prompt")
        submit_btn = gr.Button("Generate Design")
        output_text = gr.Textbox(label="Generated Output")
        image_output = gr.Image(label="Generated Image")

        submit_btn.click(fn=run_pipeline, inputs=[prompt_input], outputs=[output_text, image_output])

    demo.launch()

if __name__ == "__main__":
    gradio_ui()
    # import argparse
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--api", action="store_true", help="Run as API server")
    # parser.add_argument("--ui", action="store_true", help="Run as Gradio app")
    # args = parser.parse_args()

    # if args.api:
    #     uvicorn.run("designgenius_agentic:app", host="0.0.0.0", port=8000, reload=True)
    # elif args.ui:
    #     gradiocd..
    # _ui()
    # else:
    #     main()