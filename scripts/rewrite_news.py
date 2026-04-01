#!/usr/bin/env python3
"""
rewrite_news.py - Rewrites news articles via AI (Groq API using requests)
"""

import json
import os
import sys
import time
import requests


API_URL = "https://api.groq.com/openai/v1/chat/completions"


def rewrite_article(api_key, title, summary, source):
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

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 1500
    }
    
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    
    if resp.status_code != 200:
        print(f"  HTTP {resp.status_code}: {resp.text[:200]}")
        return None
    
    data = resp.json()
    result = data["choices"][0]["message"]["content"]
    print(f"  AI response: {len(result)} chars")
    
    # Remove markdown code blocks
    result = result.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        lines = lines[1:-1]
        result = "\n".join(lines)
        if result.startswith("json"):
            result = result[4:]
    
    parsed = json.loads(result.strip())
    
    if not all(k in parsed for k in ["headline", "summary", "content"]):
        print(f"  Missing fields: {list(parsed.keys())}")
        return None
    
    return parsed


def main():
    print("=" * 60)
    print("MotoBreaking - AI Article Rewriting")
    print("=" * 60)
    
    api_key = os.environ.get("GROQ_API_KEY", "")
    print(f"API key: {'SET' if api_key else 'NOT SET'} (length: {len(api_key)})")
    
    if not api_key:
        print("ERROR: GROQ_API_KEY not set!")
        with open("rewritten_articles.json", "w") as f:
            json.dump([], f)
        return
    
    # Test API first
    print("\nTesting Groq API...")
    test_resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": "Say hi"}], "max_tokens": 5},
        timeout=10
    )
    print(f"Test: HTTP {test_resp.status_code}")
    if test_resp.status_code == 200:
        print(f"Response: {test_resp.json()['choices'][0]['message']['content']}")
    else:
        print(f"Error: {test_resp.text[:200]}")
    
    # Load articles
    with open("raw_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    print(f"\nArticles to rewrite: {len(articles)}")
    
    if not articles:
        print("No articles found.")
        with open("rewritten_articles.json", "w") as f:
            json.dump([], f)
        return
    
    rewritten = []
    
    for i, article in enumerate(articles):
        print(f"\n[{i+1}/{len(articles)}] {article['title'][:60]}...")
        
        try:
            result = rewrite_article(
                api_key,
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
                print(f"  OK: {result['headline'][:60]}")
            else:
                article["status"] = "failed"
                print(f"  FAILED")
                
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
        
        if i < len(articles) - 1:
            time.sleep(2)
    
    with open("rewritten_articles.json", "w", encoding="utf-8") as f:
        json.dump(rewritten, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Rewritten: {len(rewritten)} of {len(articles)}")


if __name__ == "__main__":
    main()
