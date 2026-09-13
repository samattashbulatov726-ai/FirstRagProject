RAG-Agent: агент с retrieval по README и веб-поиском

Сервис на FastAPI, который отвечает на вопросы о моих GitHub-проектах, опираясь на содержимое их README, а при необходимости — обращается к веб-поиску. Построен на Groq API, эмбеддингах sentence-transformers, векторной базе Chroma и function calling для агентного поведения.

Что делает
Отвечает на вопросы о технологиях, коде и содержимом моих репозиториев на основе их README
Сам решает, искать ли ответ в README или в интернете — через tool calling у LLM
Может пройти несколько шагов подряд (например, найти актуальный факт в интернете и сопоставить его с содержимым README)
Отдаёт ответ через простой HTTP-эндпоинт /ask
Архитектура
Вопрос пользователя
        │
        ▼
   LLM (Groq) решает: нужен ли инструмент?
        │
   ┌────┴────┐
   ▼         ▼
search_    search_
readmes()   web()
   │         │
   └────┬────┘
        ▼
Результат возвращается модели
        │
        ▼
Финальный текстовый ответ
search_readmes — превращает вопрос в эмбеддинг, ищет ближайшие по смыслу куски README в Chroma
search_web — реальный поиск в интернете через DuckDuckGo (ddgs), без API-ключей
Модель может вызвать инструмент несколько раз подряд, если вопрос составной
Стек
Компонент	Технология
LLM	Groq API (openai/gpt-oss-20b)
Эмбеддинги	sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, локально, без API)
Векторная база	Chroma
Веб-фреймворк	FastAPI + uvicorn
Веб-поиск	ddgs (DuckDuckGo, бесплатно)
Контейнеризация	Docker
Сбор данных

README собираются автоматически через GitHub REST API (request.py) — скрипт проходит по всем публичным репозиториям аккаунта и скачивает README.md каждого через raw.githubusercontent.com, с учётом основной ветки (main/master).

Структура проекта
RAG-Project/
├── .env                  # секреты (GROQ_API_KEY), не коммитится
├── Dockerfile
├── requirements.txt
├── main.py               # FastAPI-приложение: lifespan, инструменты агента, /ask
├── request.py            # сбор README через GitHub API
└── data/                 # README.md собранных репозиториев
Запуск
Локально
bash
pip install -r requirements.txt

Создать .env:

GROQ_API_KEY=ваш_ключ

Запустить сервер:

bash
uvicorn main:app --reload

Открыть http://127.0.0.1:8000/docs — интерактивная документация Swagger, оттуда можно сразу протестировать /ask.

В Docker
bash
docker build -t rag-app .
docker run -p 8000:8000 --env-file .env rag-app
Пример запроса
bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Какие технологии используются в моих проектах?"}'

Ответ:

json
{
  "answer": "В ваших проектах используются Python, PyTorch (LSTM, CNN с transfer learning на ResNet18), scikit-learn (Pipeline, GridSearchCV), pandas, NumPy..."
}
Что можно улучшить дальше
Обработка ошибок внешних сервисов (веб-поиск может временно не отвечать)
Persistent-хранилище для Chroma вместо in-memory (данные сейчас пересчитываются при каждом старте)
Ограничение числа шагов агента и логирование цепочки вызовов инструментов
Автоматическая оценка качества ответов (LLM-судья) на наборе тестовых вопросов
