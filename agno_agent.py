#!/usr/bin/env python3
## only version 22, latest working
import os
import csv
import time
import requests
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
load_dotenv()
from ddgs import DDGS
from ddgs.exceptions import DDGSException
import google.genai as genai

from agno.agent import Agent
from agno.models.google import Gemini as AgnoGemini

# ================== INPUTS ==================
#Total scraped images = len(SITES) else openweb X len(KEYWORDS) X num_of_generated_prompts X MAX_IMAGES_PER_QUERY 
#Fetches .jpg", ".jpeg", ".png" images only
SITES = {
    "malabar": "malabargoldanddiamonds.com",
    # "giva": "giva.co",
    # "kalyan": "kalyanjewellers.net",
}
KEYWORDS = [
    "gold ring",
    #can add "sentence prompt"
]

num_of_generated_prompts = 2
MAX_IMAGES_PER_QUERY = 5

#Agno Market Intelligence, check market_intelligence.txt for answers, keep short, 
agnoMI="""purpose,tradition,demand,market,buyer intent,price range in INR,social_media pscyhe
    Provide short, one liners for each, business focused"""
#only add if gemini text limit increased
agno_prompt=""   #only specifics e.g. buyer intent, tredns, design styles,popularity,2025-26,genz

# ================== CONFIG ==================

BASE_DIR = "/home/ec2-user/fusion_engine/Shreeya-Agno/images/v22brand_images"
CSV_PATH = os.path.join(BASE_DIR, "brand_images.csv")  #Brand", "Keyword", "SavedFilename", "ImageURL
MARKET_INTEL_PATH = os.path.join(BASE_DIR, "market_intelligence.txt")

os.makedirs(BASE_DIR, exist_ok=True)

GEMINI_API_KEY = ""

USE_GEMINI_FILTER = True
USE_AGNO_MARKET_INTEL = True

MIN_IMAGE_BYTES = 20_000  # helps removes icons / thumbnails

# ================== GEMINI (Image Gate) ================== removes non-jewelry images
if USE_GEMINI_FILTER:
    gemini = genai.Client(api_key=GEMINI_API_KEY)

def gemini_is_clean_jewelry(keyword, image_url):
    try:
        prompt = f"""
        Keyword: {keyword}
        Image URL:{image_url}

        Is this a single jewelry product? Reject ads,text,logos,models,collages,banner. Accept single jewelry item. YES/NO
        """
        r = gemini.models.generate_content(prompt)
        return "yes" in r.text.lower()
    except Exception:
        return True  # fail-open

# ================== AGNO (Market Intelligence) ==================
agno_agent = Agent(
    model=AgnoGemini(
        id="gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
    ),
    #add words only if gemini text limit increased
    instructions=f"""
    Act senior jewelry intelligence design.
    {agno_prompt}    
    Ranging under 4 words
    """
)

def agno_generate_search_intents(keyword,num_of_generated_prompts,agno_prompt):  
    """
    AGNO converts a raw keyword into
    market-relevant DDGS search intents.
    """
    try:
        ##add words only if gemini text limit increased
        prompt = f"""Only {num_of_generated_prompts} short (ranging under 4 word each) search queries for "{keyword}" 
        {agno_prompt} No markdown. in python list"""

        response = agno_agent.run(prompt)
        text = response.content.strip()

        if text.startswith("[") and text.endswith("]"):
            intents = eval(text)
            return [q.strip() for q in intents if isinstance(q, str)]

    except Exception as e:
        print(f"⚠️ AGNO failed for '{keyword}': {e}")

    return [text]  # fallback

# ================== HELPERS ==================
def clean_url(url):
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query=""))

def looks_like_ui_asset(url):
    bad_tokens = [
        "logo", "icon", "sprite", "banner", "header",
        "footer", "menu", "placeholder", "thumb"
    ]
    return any(tok in url.lower() for tok in bad_tokens)

def is_valid_image(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        if r.status_code != 200:
            return False
        if "image" not in r.headers.get("Content-Type", ""):
            return False
        size = int(r.headers.get("Content-Length", 0))
        return size > MIN_IMAGE_BYTES
    except Exception:
        return False

def save_image(url, brand, keyword, index):
    brand = brand or "open_web"
    brand_dir = os.path.join(BASE_DIR, brand)
    os.makedirs(brand_dir, exist_ok=True)

    safe_kw = keyword[:50].replace(" ", "_").replace(",", "")
    filename = f"{brand}_{safe_kw}_{index}.jpg"
    path = os.path.join(brand_dir, filename)

    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
        print(f"✅ {brand} → {filename}")
        return filename
    return None

# ================== CORE SCRAPER ================== scraper jpg,png,jpeg
def scrape_images(brand, domain, keyword):
    rows = []
    count = 0

    primary_query = f"site:{domain} {keyword}" if domain else keyword
    fallback_query = keyword

    def run_ddgs_query(query):
        nonlocal count
        with DDGS() as ddgs:
            for img in ddgs.images(query, max_results=40):
                src = img.get("image")
                if not src:
                    continue

                src = clean_url(src)

                if looks_like_ui_asset(src):
                    continue

                if not src.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue

                if not is_valid_image(src):
                    continue

                if USE_GEMINI_FILTER:
                    if not gemini_is_clean_jewelry(keyword, src):
                        continue

                filename = save_image(src, brand, keyword, count)
                if filename:
                    rows.append([brand or "open_web", keyword, filename, src])
                    count += 1

                if count >= MAX_IMAGES_PER_QUERY:
                    break

                time.sleep(0.4)

    try:
        run_ddgs_query(primary_query)
    except DDGSException:
        print("⚠️ Site query failed, falling back")

    if count < MAX_IMAGES_PER_QUERY:
        try:
            run_ddgs_query(fallback_query)
        except DDGSException:
            print("❌ Open web failed")

    return rows

# ================== MARKET INTEL TEXT ==================
def agno_market_intelligence_prompt(keyword,agnoMI):
    prompt = f"""
    Analyze {keyword}: {agnoMI}
    """
    try:
        response = agno_agent.run(prompt)
        # AGNO response object contains .content
        return response.content.strip()
    except Exception as e:
        print(f"⚠️ AGNO failed for '{keyword}': {e}")
        # fallback to template
        return f"""
    🔹 Product: {keyword}
    • Purpose: Unknown
    • Tradition: Unknown
    • Market demand: Unknown
    • Demand: Unknown
    • Buyer intent: Unknown
    """

# ================== RUN ==================
all_rows = []
market_intel_blocks = []

# Brand-based scraping
if SITES:
    for brand, domain in SITES.items():
        print(f"\n🏷️ Brand: {brand}")
        for kw in KEYWORDS:
            print(f"   🧠 AGNO → {kw}")
            intents = agno_generate_search_intents(kw,num_of_generated_prompts,agno_prompt)

            for intent in intents:
                print(f"      🔍 {intent}")
                all_rows.extend(scrape_images(brand, domain, intent))
else:
    print("\n⚠️ No brands configured, skipping to open web only.")
    # Open web scraping
    print("\n🌍 Open Web")
    for kw in KEYWORDS:
        intents = agno_generate_search_intents(kw,num_of_generated_prompts,agno_prompt)
        for intent in intents:
            all_rows.extend(scrape_images(None, None, intent))

# Save CSV
with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Brand", "Keyword", "SavedFilename", "ImageURL"])
    writer.writerows(all_rows)

# Save market intelligence text
if USE_AGNO_MARKET_INTEL:
    for kw in intents:
        market_intel_blocks.append(agno_market_intelligence_prompt(kw, agnoMI))

    with open(MARKET_INTEL_PATH, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(market_intel_blocks))

print("\n✅ DONE")
print(f"📄 CSV → {CSV_PATH}")
print(f"🧠 Market Intel → {MARKET_INTEL_PATH}")
