import datetime
from sqlmodel import SQLModel, Field, Relationship

class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str | None
    timestamp: datetime.datetime | None

    messages: list["Message"] = Relationship(back_populates="chat", cascade_delete=True)

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    role: str
    content: str
    timestamp: datetime.datetime | None

    chat_id: int | None = Field(default=True, foreign_key="chat.id", ondelete="CASCADE")
    chat: Chat | None = Relationship(back_populates="messages")
