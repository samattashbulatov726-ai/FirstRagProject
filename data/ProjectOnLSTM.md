# 📰 End-to-End News Classifier (LSTM on PyTorch)

Проект представляет собой законченный пайплайн для сбора новостных данных и их классификации по 5 категориям (`business`, `entertainment`, `health`, `sports`, `technology`) с использованием рекуррентной нейросети (LSTM) на PyTorch.

---

## 📂 Структура проекта и файлы

- **Сбор данных:** Скрипт запрашивает свежие заголовки и описания новостей через NewsAPI, обрабатывает ошибки сети и сохраняет всё в `news_dataset.csv`.
- **`main.py`:** Основной конвейер. Включает очистку текста (RegEx), создание кастомного словаря с фильтрацией редких слов (минимальная частота — 2), токенизацию, векторизацию, создание PyTorch `Dataset`/`DataLoader` и двухслойную модель LSTM.
- **`requirements.txt`:** Список необходимых библиотек для работы нейросети и парсера.
- **`Dockerfile`:** Инструкция для автоматической сборки легковесного Docker-контейнера на базе `python:3.12-slim`.

---

## 🛠️ Архитектура нейросети

```text
Input Tokens (max_len=30) 
   ↓
nn.Embedding (vocab_size, embedding_dim=300)
   ↓
nn.LSTM (hidden_size=64, num_layers=2, dropout=0.5)
   ↓
nn.Dropout (0.5)
   ↓
nn.Linear → Logits (5 classes)
