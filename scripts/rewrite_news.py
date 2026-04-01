#!/usr/bin/env python3
"""
rewrite_news.py — Rewrites news articles via AI (Groq API)
"""

import json
import os
import sys
import time
from groq import Groq


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set!")
        print("Get a free key at https://console.groq.com")
        sys.exit(1)
    return Groq(api_key=api_key)


def rewrite_article(client, title, summary, source):
    prompt = f"""You are a professional motorcycle news journalist. Rewrite the following news article in English. Make it completely unique and original - do NOT copy the original text. Write in your own words.

Requirements:
- Write in engaging, professional journalistic style
- Keep all facts accurate but express them differently
- Make it 300-500 words
- Include a catchy headline
- Add a short summary (2-3 sentences)
- Structure with paragraphs
- DO NOT mention the original source by name

Original title: {title}
Original source: {source}
Original summary: {summary}

Return ONLY valid JSON in this exact format:
{{
  "headline": "your new headline here",
  "summary": "2-3 sentence summary",
  "content": "full rewritten article text with paragraphs"
}}"""

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.8,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        print(f"  AI response length: {len(result)}")
        
        # Remove markdown code blocks if present
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            lines = lines[1:-1]  # Remove first and last line
            result = "\n".join(lines)
            if result.startswith("json"):
                result = result[4:]
        
        parsed = json.loads(result.strip())
        
        # Validate required fields
        if not all(k in parsed for k in ["headline", "summary", "content"]):
            print(f"  Missing fields in AI response")
            return None
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  AI error: {type(e).__name__}: {e}")
        return None


def main():
    print("=" * 50)
    print("MotoBreaking - AI Article Rewriting")
    print("=" * 50)
    
    # Load collected articles
    with open("raw_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    print(f"Articles to rewrite: {len(articles)}")
    
    if not articles:
        print("No articles found. Check fetch_news.py output.")
        # Save empty array so pipeline continues
        with open("rewritten_articles.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        return
    
    client = get_groq_client()
    rewritten = []
    
    for i, article in enumerate(articles):
        print(f"\n[{i+1}/{len(articles)}] {article['title'][:60]}...")
        
        result = rewrite_article(
            client,
            article["title"],
            article["summary"],
            article["source"]
        )
        
        if result:
            article["rewritten_title"] = result["headline"]
            article["rewritten_summary"] = result["summary"]
            article["rewritten_content"] = result["content"]
            article["status"] = "rewritten"
            rewritten.append(article)
            print(f"  OK: {result['headline'][:60]}...")
        else:
            article["status"] = "failed"
            print(f"  FAILED, skipping")
        
        # Small delay to avoid rate limiting
        if i < len(articles) - 1:
            time.sleep(2)
    
    # Save rewritten articles
    with open("rewritten_articles.json", "w", encoding="utf-8") as f:
        json.dump(rewritten, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Rewritten: {len(rewritten)} of {len(articles)}")
    
    if len(rewritten) == 0:
        print("WARNING: No articles were rewritten. Check Groq API key and model availability.")


if __name__ == "__main__":
    main()
