#!/usr/bin/env python3
"""
generate_news.py - Fetches RSS, rewrites with AI, generates HTML using Jinja2 templates
"""

import json
import os
import sys
import time
import hashlib
import re
import requests
import feedparser
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

RSS_FEEDS = [
    {"url": "https://www.motorcyclenews.com/rss/news/", "name": "MCN", "category": "industry"},
    {"url": "https://www.visordown.com/rss", "name": "Visordown", "category": "newmodel"},
    {"url": "https://www.asphaltandrubber.com/feed/", "name": "Asphalt & Rubber", "category": "motogp"},
    {"url": "https://www.motor1.com/rss/news/motorcycles/feed.xml", "name": "Motor1", "category": "industry"},
    {"url": "https://www.rideapart.com/rss/", "name": "RideApart", "category": "electric"},
    {"url": "https://www.cycleworld.com/rss", "name": "Cycle World", "category": "review"},
    {"url": "https://www.bennetts.co.uk/bikesocial/news/rss", "name": "BikeSocial", "category": "industry"},
    {"url": "https://www.motorcycle.com/feed/", "name": "Motorcycle.com", "category": "review"},
    {"url": "https://www.bikeexif.com/feed", "name": "Bike EXIF", "category": "culture"},
    {"url": "https://www.pistonheads.com/rss/news/motorcycles/", "name": "PistonHeads", "category": "industry"},
    {"url": "https://www.dirtbikemagazine.com/feed/", "name": "Dirt Bike Magazine", "category": "culture"},
    {"url": "https://www.superbikeplanet.com/feed/", "name": "Superbike Planet", "category": "wsbk"},
]


def fetch_articles():
    print("\n=== STEP 1: Fetching RSS feeds ===")
    articles = []
    for feed_info in RSS_FEEDS:
        print(f"  Fetching: {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:5]:
                image = ""
                if hasattr(entry, 'media_content') and entry.media_content:
                    for m in entry.media_content:
                        if m.get('type', '').startswith('image'):
                            image = m.get('url', '')
                            break
                if not image and hasattr(entry, 'enclosures') and entry.enclosures:
                    for e in entry.enclosures:
                        if e.get('type', '').startswith('image'):
                            image = e.get('href', '')
                            break
                
                summary = entry.get("summary", "")
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = summary.strip()[:500]
                
                articles.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": summary,
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "image": image,
                    "unique_id": hashlib.md5(entry.get("link", "").encode()).hexdigest()[:8]
                })
        except Exception as e:
            print(f"  Error with {feed_info['name']}: {e}")
    
    print(f"  Total articles fetched: {len(articles)}")
    return articles


def rewrite_with_ai(api_key, title, summary, source):
    prompt = f"""You are a motorcycle news journalist. Rewrite this news in your own words. Make it unique.

Original title: {title}
Original summary: {summary}
Source: {source}

Return ONLY JSON:
{{"headline":"new title","summary":"2-3 sentence summary","content":"full article text, 3-4 paragraphs"}}"""

    resp = requests.post(
        GROQ_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1000},
        timeout=30
    )
    
    if resp.status_code != 200:
        print(f"    API error {resp.status_code}: {resp.text[:200]}")
        return None
    
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    print(f"    AI response: {len(text)} chars")
    
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:-1])
        if text.startswith("json"):
            text = text[4:]
    
    return json.loads(text.strip())


def rewrite_articles(api_key, articles):
    print("\n=== STEP 2: Rewriting with AI ===")
    if not api_key:
        print("  WARNING: No API key, skipping AI rewrite")
        return []
    
    rewritten = []
    for i, article in enumerate(articles):
        print(f"  [{i+1}/{len(articles)}] {article['title'][:50]}...")
        try:
            result = rewrite_with_ai(api_key, article["title"], article["summary"], article["source"])
            if result and all(k in result for k in ["headline", "summary", "content"]):
                article["rewritten_title"] = result["headline"]
                article["rewritten_summary"] = result["summary"]
                article["rewritten_content"] = result["content"]
                article["status"] = "rewritten"
                rewritten.append(article)
                print(f"    OK: {result['headline'][:50]}")
            else:
                print(f"    FAILED: invalid response")
        except Exception as e:
            print(f"    ERROR: {e}")
        time.sleep(1)
    
    print(f"  Rewritten: {len(rewritten)}/{len(articles)}")
    return rewritten


def generate_html(articles):
    print("\n=== STEP 3: Generating HTML ===")
    
    if not articles:
        print("  No articles to generate")
        return
    
    env = Environment(loader=FileSystemLoader("templates"))
    now = datetime.now().strftime("%B %d, %Y %H:%M")
    
    # Generate individual article pages
    os.makedirs("news", exist_ok=True)
    article_template = env.get_template("article.html")
    
    for article in articles:
        html = article_template.render(
            article=article,
            title=article.get("rewritten_title", article["title"]),
            year=datetime.now().year
        )
        filepath = f"news/{article['unique_id']}.html"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Created: {filepath}")
    
    # Generate index.html using Jinja2 template
    index_template = env.get_template("index.html")
    html = index_template.render(
        articles=articles,
        year=datetime.now().year,
        updated=now
    )
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Created: index.html ({len(articles)} articles)")


def main():
    print("=" * 60)
    print("MotoBreaking - News Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    api_key = os.environ.get("GROQ_API_KEY", "")
    print(f"API key: {'SET' if api_key else 'NOT SET'}")
    
    articles = fetch_articles()
    if not articles:
        print("No articles found. Exiting.")
        return
    
    rewritten = rewrite_articles(api_key, articles)
    
    if rewritten:
        generate_html(rewritten)
    else:
        print("No rewritten articles. Generating without AI...")
        for a in articles:
            a["rewritten_title"] = a["title"]
            a["rewritten_summary"] = a["summary"][:200]
            a["rewritten_content"] = a["summary"]
        generate_html(articles)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
