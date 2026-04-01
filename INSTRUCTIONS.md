# MotoBreaking — Автоматическое обновление новостей

## Что это такое?

Это система которая автоматически:
1. Скачивает новости с мото-сайтов (MCN, Visordown, Cycle World и др.)
2. Переписывает их через AI (чтобы текст был уникальным для Google Ads)
3. Создаёт красивые HTML страницы
4. Публикует на твоём сайте

## Структура файлов

```
motobreaking/
├── config.json              # Настройки (RSS-ленты, источники)
├── requirements.txt         # Python библиотеки
├── scripts/
│   ├── fetch_news.py       # Шаг 1: Скачивает новости из RSS
│   ├── rewrite_news.py     # Шаг 2: Переписывает через AI
│   └── generate.py         # Шаг 3: Создаёт HTML файлы
├── templates/
│   ├── index.html          # Шаблон главной страницы
│   └── article.html        # Шаблон страницы новости
├── news/                   # Тут будут HTML файлы новостей
└── .github/workflows/
    └── update.yml          # Автоматическое обновление каждые 4 часа
```

## Пошаговая инструкция

### Шаг 1: Получи бесплатный API ключ Groq

Groq — это бесплатный сервис для AI. Ключ нужен чтобы переписывать новости.

1. Зайди на https://console.groq.com
2. Нажми "Sign Up" (зарегистрируйся через GitHub или Google)
3. После входа перейди в раздел "API Keys"
4. Нажми "Create API Key"
5. Скопируй ключ — он выглядит примерно так: `gsk_xxxxxxxxxxxxxx`

### Шаг 2: Создай GitHub репозиторий

1. Зайди на https://github.com
2. Нажми "New Repository"
3. Назови его `motobreaking`
4. Выбери "Public"
5. Нажми "Create repository"

### Шаг 3: Загрузи файлы на GitHub

В терминале (открой терминал на компьютере):

```bash
# Перейди в папку с проектом
cd ~/motobreaking

# Инициализируй git
git init
git add .
git commit -m "Initial setup"

# Подключи свой репозиторий (замени YOUR_USERNAME на свой логин GitHub)
git remote add origin https://github.com/YOUR_USERNAME/motobreaking.git
git branch -M main
git push -u origin main
```

### Шаг 4: Добавь API ключ в GitHub

1. Зайди в свой репозиторий на GitHub
2. Перейди в Settings → Secrets and variables → Actions
3. Нажми "New repository secret"
4. Name: `GROQ_API_KEY`
5. Value: вставь ключ из Шага 1
6. Нажми "Add secret"

### Шаг 5: Включи GitHub Pages

1. В репозитории зайди в Settings → Pages
2. Source: выбери "GitHub Actions"
3. Всё, сайт будет публиковаться автоматически

### Шаг 6: Подключи свой домен (motobreaking.com)

1. В Settings → Pages → Custom domain
2. Введи `motobreaking.com`
3. В Cloudflare добавь CNAME запись: `@ → YOUR_USERNAME.github.io`

## Как это работает

Каждые 4 часа GitHub Actions:
1. Запускает скрипт `fetch_news.py` — он скачивает свежие новости из RSS-лент
2. Запускает `rewrite_news.py` — отправляет каждую новость в AI (Groq) для переписывания
3. Запускает `generate.py` — создаёт красивые HTML страницы
4. Автоматически публикует обновления на сайте

## Как запустить вручную (для теста)

```bash
# Установи библиотеки (один раз)
pip install -r requirements.txt

# Установи API ключ
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# Запусти всё по очереди
python scripts/fetch_news.py
python scripts/rewrite_news.py
python scripts/generate.py
```

## Источники новостей

Сейчас подключены:
- MCN (Motorcycle News)
- Visordown
- Cycle World
- Asphalt & Rubber
- Motor1
- RideApart

Чтобы добавить новый источник — отредактируй `config.json` и добавь новый RSS-фид.

## Важно

- Groq бесплатный — 30 запросов в минуту, этого более чем достаточно
- Если RSS-лента не работает — скрипт пропустит её и продолжит с остальными
- Все переписанные статьи сохраняются в `rewritten_articles.json` — можно проверить результат
