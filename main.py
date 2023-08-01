from flask import Flask, render_template, session
from flask_socketio import SocketIO, emit
import openai
import os
import chromadb
import tiktoken

client = chromadb.PersistentClient(path="./db")
collection = client.get_collection("jb-c")
with open("./system.txt", 'r') as file:
    system_message = file.read()


openai.api_key = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins=["https://banny.club", "http://banny.club"])

max_tokens = 4096
model="gpt-3.5-turbo"
tokenizer = tiktoken.encoding_for_model(model_name=model)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('send_message')
def handle_send_message(json):
    message = json['message']
    chat_history = session.get('chat_history', [])

    if not chat_history:
        chat_history.append(build_context(message))

    chat_history.append({"role": "user", "content": message})

    # chat_history = limit_chat_history(chat_history)
    session['chat_history'] = chat_history

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=chat_history,
        stream=True
    )

    assistant_message = {"role": "assistant", "content": ""}
    is_new_message = True

    for chunk in response:
        if 'delta' in chunk['choices'][0]: # pyright: ignore
            next_token = chunk['choices'][0]['delta'].get('content', '') # pyright: ignore
            if next_token:
                emit('next_token', {'message': next_token, 'is_new_message': is_new_message})
                assistant_message["content"] += next_token
                is_new_message = False

    chat_history.append(assistant_message)
    session['chat_history'] = chat_history
    emit('end_of_response')

def build_context(message):
    query_result = collection.query(
        query_texts=[message], 
        n_results=20, 
        include=["documents","distances"],
    )

    token_count = len(tokenizer.encode(system_message))
    system_with_context = system_message
    for document in query_result['documents'][0]: # pyright: ignore
        full_text = f'\n###\n' + document
        text_tokens = len(tokenizer.encode(full_text))
        if token_count + text_tokens < int(max_tokens / 2):
            system_with_context += full_text
            token_count += text_tokens
        else:
            break

    return {"role": "system", "content": system_with_context}

def limit_chat_history(chat_history):
    return chat_history


if __name__ == "__main__":
    socketio.run(app)
