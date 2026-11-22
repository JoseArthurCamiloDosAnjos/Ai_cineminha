import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

import assistente 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

lock = threading.Lock()

class Message(BaseModel):
    role: str
    content: str
    
class ChatRequest(BaseModel):
    messages: list[Message]

@app.post("/chat")
def chat(req: ChatRequest):
    if not req.messages:
        return PlainTextResponse("Envie uma mensagem.")
    
    pergunta = req.messages[-1].content
    
    try:
        with lock:
            resposta = assistente.pipeline(pergunta)
    except Exception as e:
        print("Erro no assistente:", e)
        resposta = "Ocorreu um erro ao passar sua mensagem."
        
    return PlainTextResponse(resposta)