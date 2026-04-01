#!/usr/bin/env python3
"""
generate.py — Генерирует HTML страницы из переписанных новостей
Создаёт index.html и отдельные страницы для каждой новости
"""

import json
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


def load_articles(filepath="rewritten_articles.json"):
    """Загружаем переписанные статьи"""
    if not os.path.exists(filepath):
        print(f"Файл {filepath} не найден. Сначала запусти rewrite_news.py")
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_article_pages(articles, output_dir="news"):
    """Создаём отдельные HTML страницы для каждой новости"""
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("article.html")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for article in articles:
        filename = f"{article['unique_id']}.html"
        filepath = os.path.join(output_dir, filename)
        
        html = template.render(
            article=article,
            title=article["rewritten_title"],
            year=datetime.now().year
        )
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"Создана страница: {filepath}")
    
    return articles


def generate_index_page(articles, output_file="index.html"):
    """Создаём главную страницу со списком новостей"""
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")
    
    html = template.render(
        articles=articles,
        year=datetime.now().year,
        updated=datetime.now().strftime("%B %d, %Y %H:%M")
    )
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Создана главная страница: {output_file}")


def main():
    print("=" * 50)
    print("MotoBreaking — Генерация HTML")
    print("=" * 50)
    
    articles = load_articles()
    
    if not articles:
        print("Нет статей для генерации.")
        return
    
    print(f"Генерируем страницы для {len(articles)} статей...")
    
    generate_article_pages(articles)
    generate_index_page(articles)
    
    print("\nГотово! Все HTML файлы созданы.")


if __name__ == "__main__":
    main()
