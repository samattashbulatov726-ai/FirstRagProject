import os
os.environ["NO_PROXY"] = "*"

from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()

import json
import httpx
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq
from ddgs import DDGS

resources = {}

def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# --- Инструменты агента ---
def search_readmes(question, n_results=3):
    try:
        question_embedding = resources["embed_model"].encode([question])
        results = resources["collection"].query(
            query_embeddings=question_embedding.tolist(),
            n_results=n_results
        )
        return "\n\n---\n\n".join(results["documents"][0])
    except Exception as e:
        return f"Не удалось выполнить поиск по README: {e}"

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3, region="ru-ru"))
        if not results:
            return "По этому запросу ничего не найдено в интернете."
        return "\n\n".join([f"{r['title']}: {r.get('body', '')}" for r in results])
    except Exception as e:
        return f"Не удалось выполнить веб-поиск: {e}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_readmes",
            "description": "Искать информацию в README моих собственных GitHub-проектов — используй, если вопрос про технологии, код или содержимое моих репозиториев",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Вопрос для поиска по README"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Искать актуальную информацию в интернете — используй, если вопрос НЕ связан с моими проектами",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос"}
                },
                "required": ["query"]
            }
        }
    }
]

def run_agent(user_question, max_steps=8):
    messages = [
        {"role": "system", "content": "У тебя есть доступ к функциям search_readmes и search_web. Используй их для ответа. Не проси пользователя предоставить данные вручную — всегда используй доступные инструменты, чтобы найти информацию самостоятельно."},
        {"role": "user", "content": user_question}
    ]

    for step in range(max_steps):
        response = resources["groq_client"].chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            tools=tools
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if function_name == "search_readmes":
            result = search_readmes(args["question"])
        elif function_name == "search_web":
            result = search_web(args["query"])
        else:
            result = f"Неизвестная функция: {function_name}"

        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })

    return "Не удалось получить финальный ответ за отведённое число шагов"

# --- Загрузка ресурсов при старте сервера ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.environ["GROQ_API_KEY"].strip()
    resources["groq_client"] = Groq(api_key=api_key, http_client=httpx.Client(trust_env=False))
    resources["embed_model"] = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name="readme_collection")

    data_dir = "data"
    all_chunks, all_ids = [], []
    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)
        if not filename.endswith(".md"):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            continue
        for i, chunk in enumerate(chunk_text(text)):
            all_chunks.append(chunk)
            all_ids.append(f"{filename}_chunk_{i}")

    embeddings = resources["embed_model"].encode(all_chunks)
    collection.add(documents=all_chunks, embeddings=embeddings.tolist(), ids=all_ids)
    resources["collection"] = collection

    print(f"Загружено {len(all_chunks)} чанков из README")
    yield
    resources.clear()

app = FastAPI(lifespan=lifespan)

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    answer = run_agent(req.question)
    return AskResponse(answer=answer)