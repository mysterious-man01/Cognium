import datetime
from pydantic import BaseModel

class ChatRequest(BaseModel):
    model: str
    chat: str
    prompt: str

class MsgModelRequest(BaseModel):
    id: int | None
    role: str
    content: str
    timestamp: datetime.datetime | None


class ConfigRequest(BaseModel):
    sys_prt: str
    temp: float
    max_tokens: int
    top_k: int
    top_p: float
    min_p: float
