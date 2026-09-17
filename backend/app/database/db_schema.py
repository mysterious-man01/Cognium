# from __future__ import annotations
from typing import Optional
import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from pgvector.sqlalchemy import Vector

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

    attachments: list["Attachment"] = Relationship(back_populates="message", cascade_delete=True)

    chat_id: int = Field(foreign_key="chat.id", nullable=False,  ondelete="CASCADE")
    chat: Chat = Relationship(back_populates="messages")

class Document(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hash: str | None = Field(unique=True)

    name: str = Field(unique=True)
    size: int
    uri: str = Field(unique=True)
    timestamp: datetime.datetime | None

    chunks: list["Chunk"] = Relationship(back_populates="document", cascade_delete=True)
    summary: Optional["Summary"] = Relationship(back_populates="document", cascade_delete=True)

    attachments: list["Attachment"] = Relationship(back_populates="document")

class Attachment(SQLModel, table=True):
    message_id: int = Field(foreign_key='message.id', primary_key=True, ondelete="CASCADE")
    document_id: int = Field(foreign_key="document.id", primary_key=True, ondelete="CASCADE")

    message: Message = Relationship(back_populates="attachments")
    document: Document = Relationship(back_populates="attachments")

class Chunk(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    page: int | None
    section: int | None
    model: str
    index: int
    text: str
    embedding: list[float] = Field(sa_column=Column(Vector(1024)))

    document_id: int = Field(
        foreign_key="document.id", nullable=False, ondelete="CASCADE"
    )
    document: Document = Relationship(back_populates="chunks")

class Summary(SQLModel, table=True):
    document_id: int = Field(
        foreign_key="document.id", primary_key=True, ondelete="CASCADE"
    )

    text: str

    document: Document = Relationship(back_populates="summary")

class Memory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    created_at: datetime.datetime | None
    modified_at: datetime.datetime | None
    used_model: str

    content: str
    embedding: list[float] = Field(sa_column=Column(Vector(1024)))
