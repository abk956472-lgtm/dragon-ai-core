from fastapi import FastAPI
from pydantic import BaseModel

from dragon_core.engine import dragon_engine


app = FastAPI(
    title="DRAGON AI CORE",
    version="1.2.0"
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "system": "DRAGON AI CORE",
        "status": "online",
        "version": "1.2.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    return dragon_engine.process(request.message)
