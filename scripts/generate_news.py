#!/usr/bin/env python3
"""
generate_news.py - Single script that fetches RSS, rewrites with AI, and generates HTML
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
]


def fetch_articles():
    print("\n=== STEP 1: Fetching RSS feeds ===")
    articles = []
    for feed_info in RSS_FEEDS:
        print(f"  Fetching: {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:3]:
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
                # Strip HTML tags from summary
                summary = re.sub(r'<[^>]+>', '', summary)
                summary = summary.strip()[:500]
                
                articles.append({
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": summary,
                    "published": entry.get("published", ""),
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
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )
    
    if resp.status_code != 200:
        print(f"    API error {resp.status_code}: {resp.text[:200]}")
        return None
    
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    
    # Clean markdown
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
    
    # Generate individual article pages
    os.makedirs("news", exist_ok=True)
    
    for article in articles:
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{article['rewritten_title']} - MotoBreaking</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0a0a0a;--text:#f0f0f0;--text2:#a0a0a0;--accent:#e31937;--border:#222}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Source Sans 3',sans-serif;line-height:1.6}}
a{{color:inherit;text-decoration:none}}
.header{{border-bottom:1px solid var(--border);padding:16px 0;position:sticky;top:0;background:var(--bg);z-index:100}}
.header-inner{{max-width:900px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between}}
.logo{{font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:2px}}
.logo span{{color:var(--accent)}}
.container{{max-width:720px;margin:0 auto;padding:40px 24px}}
.tag{{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;padding:4px 10px;border-radius:3px;color:#fff;display:inline-block;margin-bottom:16px}}
.tag-motogp{{background:#e31937}}.tag-newmodel{{background:#2d8cf0}}.tag-industry{{background:#f5a623;color:#111}}.tag-electric{{background:#22c55e;color:#111}}.tag-review{{background:#a855f7}}.tag-culture{{background:#ec4899}}.tag-wsbk{{background:#f97316}}.tag-bsb{{background:#06b6d4}}
h1{{font-family:'Bebas Neue',sans-serif;font-size:42px;line-height:1.1;letter-spacing:1px;margin-bottom:16px}}
.meta{{font-size:14px;color:#666;margin-bottom:32px;font-family:'JetBrains Mono',monospace}}
.meta span{{margin-right:16px}}
img{{width:100%;border-radius:8px;margin-bottom:32px}}
.content{{font-size:18px;line-height:1.8;color:var(--text2)}}
.content p{{margin-bottom:24px}}
.back{{display:inline-flex;align-items:center;gap:8px;color:var(--accent);font-weight:600;font-size:14px;margin-bottom:32px}}
footer{{border-top:1px solid var(--border);padding:32px 0;margin-top:64px;text-align:center;color:#666;font-size:13px;font-family:'JetBrains Mono',monospace}}
</style>
</head>
<body>
<header class="header"><div class="header-inner"><a href="../index.html" class="logo">MOTO<span>BREAKING</span></a><a href="../index.html" class="back">Back to news</a></div></header>
<main class="container">
<a href="../index.html" class="back">All News</a>
<span class="tag tag-{article['category']}">{article['category']}</span>
<h1>{article['rewritten_title']}</h1>
<div class="meta"><span>{article['published']}</span><span>{article['source']}</span></div>
{f'<img src="{article["image"]}" alt="">' if article['image'] else ''}
<div class="content">{article['rewritten_content'].replace(chr(10), '<br>')}</div>
</main>
<footer>2026 MotoBreaking - Breaking Motorcycle News</footer>
</body>
</html>"""
        filepath = f"news/{article['unique_id']}.html"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Created: {filepath}")
    
    # Generate index.html
    cards_html = ""
    for article in articles:
        cards_html += f"""
      <a href="news/{article['unique_id']}.html" class="news-card">
        {f'<img src="{article["image"]}" alt="" class="news-card-img">' if article['image'] else ''}
        <div class="news-card-body">
          <span class="tag tag-{article['category']} news-card-tag">{article['category']}</span>
          <h3 class="news-card-title">{article['rewritten_title']}</h3>
          <p class="news-card-excerpt">{article['rewritten_summary']}</p>
          <div class="news-card-meta"><span>{article['published']}</span><span>{article['source']}</span></div>
        </div>
      </a>"""
    
    # Read original index.html template
    with open("templates/index.html", "r") as f:
        template = f.read()
    
    # Simple replacement approach - generate a minimal index
    now = datetime.now().strftime("%B %d, %Y %H:%M")
    
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MotoBreaking - Breaking Motorcycle News</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0a0a0a;--bg2:#111;--card:#161616;--card-hover:#1c1c1c;--text:#f0f0f0;--text2:#a0a0a0;--muted:#666;--accent:#e31937;--border:#222;--tag-motogp:#e31937;--tag-newmodel:#2d8cf0;--tag-industry:#f5a623;--tag-electric:#22c55e;--tag-review:#a855f7;--tag-culture:#ec4899;--tag-wsbk:#f97316;--tag-bsb:#06b6d4}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:'Source Sans 3',sans-serif;line-height:1.5}}
a{{color:inherit;text-decoration:none}}
.logo-banner{{background:var(--bg);padding:12px 0;border-bottom:1px solid var(--border)}}
.logo-banner-inner{{max-width:1400px;margin:0 auto;padding:0 24px}}
.logo-banner-text{{font-family:'Bebas Neue',sans-serif;font-size:48px;letter-spacing:4px}}
.logo-banner-text span{{color:var(--accent)}}
.updated-info{{text-align:center;padding:12px;background:var(--bg2);border-bottom:1px solid var(--border);font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--muted)}}
.updated-info span{{color:var(--accent)}}
header{{border-bottom:1px solid var(--border);background:var(--bg);position:sticky;top:0;z-index:100}}
.header-inner{{max-width:1400px;margin:0 auto;padding:0 24px;display:flex;align-items:center;justify-content:space-between;height:64px}}
.logo{{font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:2px}}
.logo span{{color:var(--accent)}}
.header-date{{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--text2)}}
.container{{max-width:1400px;margin:0 auto;padding:0 24px}}
.hero{{padding:32px 0 28px;border-bottom:1px solid var(--border)}}
.hero-grid{{display:grid;grid-template-columns:1.2fr 1fr;gap:32px}}
.hero-main{{position:relative;overflow:hidden;min-height:420px;display:flex;flex-direction:column;justify-content:flex-end;border-radius:8px}}
.hero-image{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0.35}}
.hero-overlay{{position:absolute;inset:0;background:linear-gradient(to top,rgba(10,10,10,0.95) 35%,rgba(10,10,10,0.2) 100%)}}
.hero-content{{position:relative;z-index:2;padding:36px}}
.tag{{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;padding:4px 10px;border-radius:3px;display:inline-block;color:#fff}}
.tag-motogp{{background:var(--tag-motogp)}}.tag-newmodel{{background:var(--tag-newmodel)}}.tag-industry{{background:var(--tag-industry);color:#111}}.tag-electric{{background:var(--tag-electric);color:#111}}.tag-review{{background:var(--tag-review)}}.tag-culture{{background:var(--tag-culture)}}.tag-wsbk{{background:var(--tag-wsbk)}}.tag-bsb{{background:var(--tag-bsb)}}
.hero-title{{font-family:'Bebas Neue',sans-serif;font-size:42px;line-height:1.0;letter-spacing:1px;margin:10px 0}}
.hero-excerpt{{font-size:15px;color:var(--text2);line-height:1.55;max-width:520px}}
.hero-meta{{margin-top:16px;font-size:13px;color:var(--muted);display:flex;align-items:center;gap:12px}}
.hero-meta .time{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--accent)}}
.hero-sidebar{{display:flex;flex-direction:column;gap:0}}
.hero-side-item{{padding:24px 0;border-bottom:1px solid var(--border);display:grid;grid-template-columns:1fr 130px;gap:18px;align-items:start}}
.hero-side-item:first-child{{padding-top:0}}.hero-side-item:last-child{{border-bottom:none}}
.hero-side-item:hover .hero-side-title{{color:var(--accent)}}
.hero-side-tag{{margin-bottom:6px}}
.hero-side-title{{font-size:19px;font-weight:700;line-height:1.35;transition:color 0.2s}}
.hero-side-meta{{margin-top:8px;font-size:13px;color:var(--accent);font-family:'JetBrains Mono',monospace}}
.hero-side-img{{width:130px;height:88px;object-fit:cover;border-radius:6px}}
.section{{padding:40px 0;border-bottom:1px solid var(--border)}}
.section-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px}}
.section-title{{font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:2px;display:flex;align-items:center;gap:12px}}
.section-title::before{{content:'';width:4px;height:24px;background:var(--accent);border-radius:2px}}
.news-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}
.news-card{{background:var(--card);border-radius:10px;overflow:hidden;border:1px solid var(--border);transition:all 0.25s}}
.news-card:hover{{background:var(--card-hover);border-color:#2a2a2a;transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,0,0,0.4)}}
.news-card:hover .news-card-title{{color:var(--accent)}}
.news-card-img{{width:100%;aspect-ratio:16/9;object-fit:cover}}
.news-card-body{{padding:20px}}
.news-card-tag{{margin-bottom:10px}}
.news-card-title{{font-size:18px;font-weight:700;line-height:1.35;margin-bottom:10px;transition:color 0.2s}}
.news-card-excerpt{{font-size:14px;color:var(--text2);line-height:1.55;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.news-card-meta{{margin-top:14px;padding-top:14px;border-top:1px solid var(--border);font-size:12px;color:var(--muted);font-family:'JetBrains Mono',monospace;display:flex;justify-content:space-between}}
footer{{padding:48px 0 32px;border-top:1px solid var(--border)}}
.footer-bottom{{text-align:center;font-size:12px;color:var(--muted);font-family:'JetBrains Mono',monospace}}
@media(max-width:1024px){{.hero-grid{{grid-template-columns:1fr}}.news-grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:640px){{.hero-title{{font-size:36px}}.news-grid{{grid-template-columns:1fr}}.hero-side-item{{grid-template-columns:1fr}}.hero-side-img{{display:none}}}}
</style>
</head>
<body>
<div class="logo-banner"><div class="logo-banner-inner"><div class="logo-banner-text">MOTO <span>BREAKING</span></div></div></div>
<div class="updated-info">Last updated: <span>{now}</span> - Auto-refreshed every 4 hours</div>
<header><div class="header-inner"><div class="logo">MOTO<span>BREAKING</span></div><div class="header-date">{now}</div></div></header>
"""
    
    if articles:
        first = articles[0]
        index_html += f"""
<div class="hero"><div class="container"><div class="hero-grid">
<a href="news/{first['unique_id']}.html" class="hero-main">
{f'<img src="{first["image"]}" alt="" class="hero-image">' if first['image'] else ''}
<div class="hero-overlay"></div>
<div class="hero-content">
<span class="tag tag-{first['category']}">{first['category']}</span>
<h1 class="hero-title">{first['rewritten_title']}</h1>
<p class="hero-excerpt">{first['rewritten_summary']}</p>
<div class="hero-meta"><span class="time">{first['published']}</span><span>{first['source']}</span></div>
</div></a>
<div class="hero-sidebar">
"""
        for a in articles[1:5]:
            index_html += f"""
<a href="news/{a['unique_id']}.html" class="hero-side-item">
<div><span class="tag tag-{a['category']} hero-side-tag">{a['category']}</span>
<h3 class="hero-side-title">{a['rewritten_title']}</h3>
<div class="hero-side-meta">{a['published']}</div></div>
{f'<img src="{a["image"]}" alt="" class="hero-side-img">' if a['image'] else ''}
</a>"""
        
        index_html += "</div></div></div></div>"
        
        index_html += f"""
<div class="section"><div class="container"><div class="section-header"><h2 class="section-title">Latest News</h2></div>
<div class="news-grid">
"""
        for a in articles[5:]:
            index_html += f"""
<a href="news/{a['unique_id']}.html" class="news-card">
{f'<img src="{a["image"]}" alt="" class="news-card-img">' if a['image'] else ''}
<div class="news-card-body">
<span class="tag tag-{a['category']} news-card-tag">{a['category']}</span>
<h3 class="news-card-title">{a['rewritten_title']}</h3>
<p class="news-card-excerpt">{a['rewritten_summary']}</p>
<div class="news-card-meta"><span>{a['published']}</span><span>{a['source']}</span></div>
</div></a>"""
        
        index_html += "</div></div></div>"
    
    index_html += """
<footer><div class="container"><div class="footer-bottom">2026 MotoBreaking - Breaking Motorcycle News</div></div></footer>
</body></html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"  Created: index.html ({len(articles)} articles)")


def main():
    print("=" * 60)
    print("MotoBreaking - News Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    api_key = os.environ.get("GROQ_API_KEY", "")
    print(f"API key: {'SET' if api_key else 'NOT SET'}")
    
    # Step 1: Fetch
    articles = fetch_articles()
    if not articles:
        print("No articles found. Exiting.")
        return
    
    # Step 2: Rewrite
    rewritten = rewrite_articles(api_key, articles)
    
    # Step 3: Generate
    if rewritten:
        generate_html(rewritten)
    else:
        print("No rewritten articles. Generating without AI...")
        # Use original articles as-is
        for a in articles:
            a["rewritten_title"] = a["title"]
            a["rewritten_summary"] = a["summary"][:200]
            a["rewritten_content"] = a["summary"]
        generate_html(articles)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
