#!/usr/bin/env python3
"""
fetch_news.py — Скрипт для сбора новостей из RSS-лент
Этот файл скачивает последние новости из мото-сайтов
"""

import feedparser
import json
import hashlib
from datetime import datetime
from pathlib import Path


def load_config(config_path="config.json"):
    """Загружаем настройки из config.json"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_rss_feeds(feeds):
    """Скачиваем новости из всех RSS-лент"""
    all_articles = []
    
    for feed_info in feeds:
        print(f"Скачиваем: {feed_info['name']}...")
        try:
            feed = feedparser.parse(feed_info["url"])
            
            for entry in feed.entries[:5]:  # Берём по 5 статей с каждого сайта
                article = {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "source": feed_info["name"],
                    "category": feed_info["category"],
                    "image": get_image_from_entry(entry),
                    "unique_id": hashlib.md5(entry.get("link", "").encode()).hexdigest()[:8]
                }
                all_articles.append(article)
                
        except Exception as e:
            print(f"Ошибка с {feed_info['name']}: {e}")
    
    print(f"Всего собрано статей: {len(all_articles)}")
    return all_articles


def get_image_from_entry(entry):
    """Пытаемся найти картинку в RSS-записи"""
    # Ищем в media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if media.get('medium') == 'image' or media.get('type', '').startswith('image'):
                return media.get('url', '')
    
    # Ищем в enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'):
                return enc.get('href', '')
    
    # Ищем в links
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.get('type', '').startswith('image'):
                return link.get('href', '')
    
    return ""


def save_raw_articles(articles, output_file="raw_articles.json"):
    """Сохраняем собранные статьи в JSON файл"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"Статьи сохранены в {output_file}")


def main():
    print("=" * 50)
    print("MotoBreaking — Сбор новостей")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    config = load_config()
    articles = fetch_rss_feeds(config["rss_feeds"])
    
    if articles:
        save_raw_articles(articles)
        print("Готово! Теперь запусти rewrite_news.py")
    else:
        print("Статьи не найдены. Проверь RSS-ленты.")


if __name__ == "__main__":
    main()
