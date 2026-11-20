import threading

from fastapi import FatAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextReponse
from pydantic import BaseModel

import assistente 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost5173"],
    allow_methods=["*"],
    allow_headers=["*"]
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
        return PlainTextReponse("Envie uma mensagem.")
    
    pergunta = req.messages[-1].content
    
    try:
        with lock:
            resposta = assistente.pipeline(pergunta)
    except Exception as e:
        print("Erro no assistente:", e)
        resposta = "Ocorreu um erro ao passar sua mensagem."
        
    return PlainTextReponse(resposta)