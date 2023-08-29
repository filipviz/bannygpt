from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
import openai
import os
import chromadb
import tiktoken
from dotenv import load_dotenv

load_dotenv(".env")

client = chromadb.PersistentClient(path="./db")
collection = client.get_collection("jb-c")
with open("./system.txt", "r") as file:
    system_message = file.read()

openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

max_tokens = 4096
model = "gpt-3.5-turbo"
tokenizer = tiktoken.encoding_for_model(model_name=model)

@app.get("/")
def index():
    return FileResponse("index.html")

@app.websocket("/ws")
async def handle_send_message(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    messages = data.get("messages", [])
    if messages:
        if len(messages) == 1:
            messages.insert(0, build_context(messages[0].get("content")))
        is_new_message = True
        response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                stream=True
            )
        for chunk in response:
            if "delta" in chunk["choices"][0]: # pyright: ignore
                next_token = chunk["choices"][0]["delta"].get("content", "") # pyright: ignore
                if next_token:
                    await websocket.send_json({"token": next_token, "is_new_message": is_new_message})
                    is_new_message = False
    await websocket.send_text("end_of_message")

def build_context(message):
    query_result = collection.query(
        query_texts=[message],
        n_results=20,
        include=["documents", "distances"],
    )

    token_count = len(tokenizer.encode(system_message))
    system_with_context = system_message
    for document in query_result["documents"][0]:  # pyright: ignore
        full_text = f"\n###\n" + document
        text_tokens = len(tokenizer.encode(full_text))
        if token_count + text_tokens < int(max_tokens / 2):
            system_with_context += full_text
            token_count += text_tokens
        else:
            break

    return {"role": "system", "content": system_with_context}

def limit_chat_history(chat_history):
    return chat_history
