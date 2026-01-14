"""
Jewelry Trends Web Scraper using SerpAPI
Pulls trendy designs across jewelry categories with 2025 trend indicators
"""

import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from pathlib import Path
load_dotenv()
# === Configuration ===
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
JEWELRY_CATEGORIES = ["Bangle", "Earring", "Necklace", "Pendant", "Ring"]

# === Trend Definition for 2025 ===
TREND_INDICATORS_2025 = {
    "temporal": {
        "current_year": 2025,
        "recent_months": 3,  # Last 3 months
        "keywords": ["2025", "new", "latest", "trending", "viral"]
    },
    "social_signals": {
        "keywords": ["instagram", "tiktok", "pinterest", "viral", "trending", "aesthetic"],
        "weight": 0.3
    },
    "sustainability": {
        "keywords": ["sustainable", "eco-friendly", "ethical", "recycled", "vegan"],
        "weight": 0.25,
        "importance": "High - 2025 focus"
    },
    "minimalism": {
        "keywords": ["minimalist", "minimal", "simple", "clean lines", "understated"],
        "weight": 0.2,
        "importance": "Counter to maximalism"
    },
    "personalization": {
        "keywords": ["custom", "personalized", "bespoke", "unique", "individual"],
        "weight": 0.15,
        "importance": "Growing trend"
    },
    "technology_integration": {
        "keywords": ["smart jewelry", "tech integrated", "AI generated", "digital"],
        "weight": 0.1,
        "importance": "Emerging"
    }
}

# === SerpAPI Search ===
class JewelryTrendsScraper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
        self.results = {}
        self.timestamp = datetime.now()
        
    def fetch_trends(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Fetch trending designs for a jewelry category
        """
        headers = {
            "X-API-KEY": self.api_key, # Replace with your SerpAPI key
            "Content-Type": "application/json"
        }
        
        queries = [
            f"{category} jewelry trends 2025",
            f"trending {category.lower()} designs 2025",
            f"{category} jewelry viral designs",
            f"best {category.lower()} styles 2025",
            f"sustainable {category.lower()} jewelry trends"
        ]
        
        all_results = []
        
        for query in queries:
            payload = {"q": query}
            try:
                response = requests.post(self.base_url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("organic", [])
                    all_results.extend(results)
                    print(f"✓ Fetched results for: {query}")
                else:
                    print(f"✗ Error fetching {query}: {response.status_code}")
            except Exception as e:
                print(f"✗ Exception fetching {query}: {str(e)}")
        
        # Remove duplicates and apply trend scoring
        unique_results = self._deduplicate(all_results)
        scored_results = self._score_trends(unique_results, category)
        
        return scored_results[:limit]
    
    def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate URLs"""
        seen_urls = set()
        unique = []
        for result in results:
            url = result.get('link', '')
            if url not in seen_urls:
                seen_urls.add(url)
                unique.append(result)
        return unique
    
    def _score_trends(self, results: List[Dict], category: str) -> List[Dict]:
        """
        Score each result based on 2025 trend indicators
        """
        for result in results:
            score = self._calculate_trend_score(result)
            result['trend_score'] = score
            result['trend_category'] = category
            result['scraped_date'] = self.timestamp.isoformat()
        
        # Sort by trend score
        return sorted(results, key=lambda x: x.get('trend_score', 0), reverse=True)
    
    def _calculate_trend_score(self, result: Dict) -> float:
        """
        Calculate trend score based on 2025 indicators
        """
        text = f"{result.get('title', '')} {result.get('snippet', '')}".lower()
        score = 0.0
        
        # Temporal relevance (40% weight)
        if any(kw in text for kw in TREND_INDICATORS_2025["temporal"]["keywords"]):
            score += 0.4
        
        # Social signals (30% weight)
        if any(kw in text for kw in TREND_INDICATORS_2025["social_signals"]["keywords"]):
            score += 0.3
        
        # Sustainability (25% weight)
        if any(kw in text for kw in TREND_INDICATORS_2025["sustainability"]["keywords"]):
            score += 0.25
        
        # Minimalism (20% weight)
        if any(kw in text for kw in TREND_INDICATORS_2025["minimalism"]["keywords"]):
            score += 0.2
        
        # Personalization (15% weight)
        if any(kw in text for kw in TREND_INDICATORS_2025["personalization"]["keywords"]):
            score += 0.15
        
        # Tech integration (10% weight)
        if any(kw in text for kw in TREND_INDICATORS_2025["technology_integration"]["keywords"]):
            score += 0.1
        
        return min(score, 1.0)  # Normalize to 0-1
    
    def fetch_all_categories(self, limit: int = 10) -> Dict:
        """
        Fetch trends for all jewelry categories
        """
        print("\n" + "="*60)
        print("🔍 FETCHING JEWELRY TRENDS ACROSS ALL CATEGORIES")
        print("="*60 + "\n")
        
        for category in JEWELRY_CATEGORIES:
            print(f"\n📿 Fetching trends for: {category}")
            print("-" * 40)
            self.results[category] = self.fetch_trends(category, limit)
        
        return self.results
    
    def save_to_json(self, filename: str = "jewelry_trends.json"):
        """Save results to JSON"""
        output = {
            "timestamp": self.timestamp.isoformat(),
            "trend_indicators_2025": TREND_INDICATORS_2025,
            "categories": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n✅ Results saved to {filename}")
    
    def save_to_csv(self, filename: str = "jewelry_trends.csv"):
        """Save results to CSV for easier analysis"""
        all_data = []
        
        for category, results in self.results.items():
            for result in results:
                all_data.append({
                    "category": category,
                    "title": result.get('title', ''),
                    "snippet": result.get('snippet', ''),
                    "url": result.get('link', ''),
                    "trend_score": result.get('trend_score', 0),
                    "scraped_date": result.get('scraped_date', '')
                })
        
        df = pd.DataFrame(all_data)
        df = df.sort_values('trend_score', ascending=False)
        df.to_csv(filename, index=False)
        print(f"✅ Results saved to {filename}")
        return df
    
    def print_summary(self):
        """Print a summary of trends"""
        print("\n" + "="*60)
        print("📊 JEWELRY TRENDS SUMMARY - 2025")
        print("="*60 + "\n")
        
        for category, results in self.results.items():
            if results:
                print(f"\n🎯 {category.upper()}")
                print("-" * 40)
                for i, result in enumerate(results[:5], 1):
                    print(f"\n{i}. {result.get('title', 'N/A')[:70]}")
                    print(f"   Trend Score: {result.get('trend_score', 0):.2f}/1.0")
                    print(f"   Snippet: {result.get('snippet', 'N/A')[:100]}...")


# === Trend Definition Guide for 2025 ===
def print_trend_definition_guide():
    """Print recommendations for defining trendy designs in 2025"""
    
    guide = """
    ╔════════════════════════════════════════════════╗
    ║   "TRENDY" FOR JEWELRY IN 2025                 ║
    ╚════════════════════════════════════════════════╝

    1. 🌍 SUSTAINABILITY & ETHICS (Weight: 25%)
       ✓ Use recycled/upcycled materials
       ✓ Conflict-free sourcing
       ✓ Eco-friendly production methods
       ✓ Vegan alternatives to animal products
       → Consumer Insight: 73% of Gen Z prioritizes sustainability

    2. 📱 SOCIAL MEDIA VIRALITY (Weight: 30%)
       ✓ Pinterest pins (jewelry reference boards)
       ✓ Instagram Reels & Stories (styling inspiration)
       ✓ TikTok trends (#jewelrystyle, #fashionhacks)
       ✓ Influencer endorsements
       ✓ User-generated content engagement
       → Metric: Track shares, saves, comments in last 3 months

    3. ✨ MINIMALISM & SIMPLICITY (Weight: 20%)
       ✓ Clean lines & understated elegance
       ✓ Geometric shapes
       ✓ Multi-functional pieces
       ✓ "Less is more" philosophy
       → Counter to maximalist jewelry of past years

    4. 🎨 PERSONALIZATION & INDIVIDUALITY (Weight: 15%)
       ✓ Custom engravings/initials
       ✓ Mix-and-match modular designs
       ✓ Birthstone/zodiac customization
       ✓ Limited edition collections
       → Trend: Younger consumers want unique pieces

    5. 🔗 TECH INTEGRATION (Weight: 10%)
       ✓ Smart jewelry (health tracking)
       ✓ AR try-on experiences
       ✓ AI-generated design suggestions
       ✓ NFT/Digital ownership options
       → Emerging: Blend of fashion and technology

    6. 🎭 CULTURAL & COLOR TRENDS
       ✓ Earth tones (terracotta, sage, bronze)
       ✓ Maximalist color combinations
       ✓ Retro-inspired (70s, 80s, 90s)
       ✓ Global aesthetic fusion
       → Research: Pantone, WGSN, Pinterest Trend Reports

    7. ⏰ TEMPORAL RELEVANCE
       ✓ Featured in last 3 months
       ✓ Related to current events/seasons
       ✓ Aligned with upcoming holidays
       ✓ Real-time search volume analysis
       → Tools: Google Trends, SerpAPI, TikTok analytics

    8. 💰 PRICE POSITIONING
       ✓ Fast fashion ($5-50)
       ✓ Mid-range ($50-200)
       ✓ Premium ($200-1000)
       ✓ Luxury ($1000+)
       → 2025 Trend: Bridge between affordable & quality

    ╔════════════════════════════════════════════════════════════════╗
    ║   SCORING METHODOLOGY                                          ║
    ╚════════════════════════════════════════════════════════════════╝

    TREND SCORE = (Social_Signals × 0.30) +
                  (Sustainability × 0.25) +
                  (Minimalism × 0.20) +
                  (Personalization × 0.15) +
                  (Tech_Integration × 0.10)

    A score > 0.7 = Highly Trendy ✨
    A score 0.5-0.7 = Trending 📈
    A score < 0.5 = Emerging/Niche 🔍

    ╔════════════════════════════════════════════════════════════════╗
    ║   DATA SOURCES TO MONITOR                                      ║
    ╚════════════════════════════════════════════════════════════════╝

    1. Social Media Analytics
       - Instagram: @stylepins, @vogue, @jcrew
       - Pinterest: Jewelry boards (100M+ pins)
       - TikTok: #jewelrytrend (3B+ views)
       - Reddit: r/jewelry, r/fashion

    2. Industry Reports
       - WGSN Insider (forecasting)
       - Pantone Fashion Color Report
       - McKinsey Fashion Report
       - LinkedIn Fashion Industry Trends

    3. E-commerce Signals
       - Amazon Best Sellers (Jewelry category)
       - Etsy Trending (Handmade jewelry)
       - Farfetch (Luxury trends)
       - Shopify trend data

    4. News & Publications
       - Vogue, Harper's Bazaar, Elle
       - WWD (Women's Wear Daily)
       - Fashion magazines
       - Luxury brand announcements

    5. Real-time Trending
       - Google Trends (jewelry searches)
       - Twitter/X trend analysis
       - YouTube search trends
       - Celebrity styling choices

    """
    
    # print(guide)
    print(".")


# === Main Execution ===
def main():
    if not SERPER_API_KEY:
        print("⚠️  SERPER_API_KEY environment variable not set!")
        print("   Set it with: export SERPER_API_KEY='your_api_key'")
        return
    
    # Print trend definition guide
    print_trend_definition_guide()
    
    # Initialize scraper
    scraper = JewelryTrendsScraper(SERPER_API_KEY)
    
    # Fetch trends for all categories
    scraper.fetch_all_categories(limit=8)
    
    # Save results
    scraper.save_to_json("jewelry_trends.json")
    scraper.save_to_csv("jewelry_trends.csv")
    
    # Print summary
    scraper.print_summary()
    
    print("\n" + "="*60)
    print("✅ SCRAPING COMPLETE")
    print("="*60)
    print("\nOutput files:")
    print("  📄 jewelry_trends.json (detailed)")
    print("  📊 jewelry_trends.csv (analysis)")
    print("\n")


if __name__ == "__main__":
    main()
