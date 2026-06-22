from pydantic import BaseModel


class ChatRequest(BaseModel):
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int = 512
