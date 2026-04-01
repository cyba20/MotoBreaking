#!/usr/bin/env python3
"""
rewrite_news.py — Переписываем новости через AI (Groq API)
Этот файл берёт собранные новости и переписывает их уникальным текстом
"""

import json
import os
import sys
from groq import Groq


def get_groq_client():
    """Создаём клиент Groq API"""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ОШИБКА: Не найден GROQ_API_KEY!")
        print("Получи бесплатный ключ на https://console.groq.com")
        sys.exit(1)
    return Groq(api_key=api_key)


def rewrite_article(client, title, summary, source):
    """Переписываем статью через AI"""
    
    prompt = f"""You are a professional motorcycle news journalist. Rewrite the following news article in English. Make it completely unique and original — do NOT copy the original text. Write in your own words.

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
            model="llama-3.3-70b-versatile",
            temperature=0.8,
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        
        # Парсим JSON из ответа
        # Убираем возможные markdown обёртки
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        return json.loads(result.strip())
        
    except Exception as e:
        print(f"Ошибка AI переписывания: {e}")
        return None


def main():
    print("=" * 50)
    print("MotoBreaking — AI Переписывание новостей")
    print("=" * 50)
    
    # Загружаем собранные статьи
    with open("raw_articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    print(f"Статей для переписывания: {len(articles)}")
    
    client = get_groq_client()
    rewritten = []
    
    for i, article in enumerate(articles):
        print(f"\nПереписываем статью {i+1}/{len(articles)}: {article['title'][:50]}...")
        
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
            print(f"  ✓ Готово: {result['headline'][:50]}...")
        else:
            article["status"] = "failed"
            print(f"  ✗ Ошибка, пропускаем")
    
    # Сохраняем переписанные статьи
    with open("rewritten_articles.json", "w", encoding="utf-8") as f:
        json.dump(rewritten, f, indent=2, ensure_ascii=False)
    
    print(f"\nГотово! Переписано: {len(rewritten)} из {len(articles)}")


if __name__ == "__main__":
    main()
