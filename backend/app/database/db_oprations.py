from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from .db_conn import get_engine
from .db_schema import Chat, Message, Document, Attachment, Chunk, Summary, Memory

from config import DbConfig, CONSTRAINT
import numpy as np

def add_chat(title: str = None):
    new_chat = Chat(title=title)

    with Session(get_engine()) as session:
        session.add(new_chat)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on add_chat -> {e}")

        session.refresh(new_chat)

    return new_chat.model_dump()

def get_chats():
    with Session(get_engine()) as session:
        chat_list = session.exec(select(Chat)).all()

        return [chat.model_dump() for chat in chat_list]

def get_chat(chat_id: int):
    with Session(get_engine()) as session:
        statement = select(Chat).where(Chat.id == chat_id)
        result = session.exec(statement)

        chat = result.first()

        return chat.model_dump() if chat is not None else None

def update_chat(chat_id: int, title):
    with Session(get_engine()) as session:
        result = session.exec(select(Chat).where(Chat.id == chat_id))
        chat = result.one_or_none()

        if chat is None:
            return None

        chat.title = title

        session.add(chat)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on update_chat -> {e}")

        session.refresh(chat)

        return chat.model_dump()

def delete_chat(chat_id: int):
    with Session(get_engine()) as session:
        statement = select(Chat).where(Chat.id == chat_id)
        result = session.exec(statement)
        session.delete(result.one())

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on delete_chat -> {e}")

        return bool(session.get(Chat, chat_id) is None)

def create_document(data):
    doc = Document(
        id=data['id'],
        hash=data['hash'],
        name=data['name'],
        size=data['size'],
        uri=data['uri'],
        timestamp=data['timestamp']
    )

    with Session(get_engine()) as session:
        session.add(doc)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on create_attachment -> {e}")

        session.refresh(doc)

        result = session.exec(select(Document).where(
            Document.id == doc.id
        )).one_or_none()

        return result.model_dump() if result else None

def update_document(file_name: str, new_data: str):
    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(
            Document.name == file_name
        )).one_or_none()

        if result is None:
            return None

        result.uri = new_data

        session.add(result)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on update_attachment -> {e}")

        session.refresh(result)

        return result.model_dump()

def delete_document(data):
    doc = None
    with Session(get_engine()) as session:
        if data.get('id', None):
            doc = session.exec(select(Document).where(
                Document.id == data['id']
            )).one_or_none()
        elif data.get('hash', None):
            doc = session.exec(select(Document).where(
                Document.hash == data['hash']
            )).one_or_none()
        elif data.get('name', None):
            doc = session.exec(select(Document).where(
                Document.name == data['name']
            )).one_or_none()

        if doc is None:
            return None

        session.delete(doc)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on delete_document -> {e}")

        return bool(session.get(Document, doc.id))

def get_documents():
    with Session(get_engine()) as session:
        documents = session.exec(select(Document)).all()

        return [doc.model_dump() for doc in documents]

def get_document_by_name(name: str):
    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(
            Document.name == name
        )).one_or_none()

        return result.model_dump() if result else None

def get_document_by_hash(doc_hash: str):
    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(
            Document.hash == doc_hash
        )).one_or_none()

        return result.model_dump() if result else None

def get_documents_by_msg_id(msg_id: int):
    with Session(get_engine()) as session:
        atts = session.exec(select(Attachment).where(
            Attachment.message_id == msg_id
        )).all()

        return [att.document.model_dump() for att in atts]

def add_message(chat_id: int, data):
    msg = Message(
        id=data['id'],
        role=data['role'],
        content=data['content'],
        timestamp=data['timestamp'],
        chat_id=chat_id
    )

    msg.attachments = []

    if data['attachments']:
        for att in data['attachments']:
            doc = get_document_by_name(att['name'])

            msg.attachments.append(
                Attachment(
                    message_id=data['id'],
                    document_id=doc['id']
                )
            )

    with Session(get_engine()) as session:
        result = session.exec(select(Chat).where(Chat.id == chat_id))

        msg.chat = result.one()

        session.add(msg)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on add_message -> {e}")

        session.refresh(msg) # OPITIONAL

        result = session.exec(select(Message).where(
            Message.chat_id == chat_id, Message.id == msg.id
        )).one_or_none()

        return result.model_dump() if result else None

def update_message(chat_id: int, data):
    with Session(get_engine()) as session:
        msg = session.exec(select(Message).where(
            Message.chat_id == chat_id, Message.id == data['id']
        )).one_or_none()

        if msg is None:
            return None

        msg.role = data['role']
        msg.content = data['content']
        msg.timestamp = data['timestamp']

        if isinstance(data.get('attachments'), list):
            for att in data['attachments']:
                doc = get_document_by_name(att['name'])

                msg.attachments.append(
                    Attachment(
                        message_id=msg.id,
                        document_id=doc['id']
                    )
                )

        session.add(msg)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on update_message -> {e}")

        session.refresh(msg)

        return msg.model_dump()

def get_messages(chat_id: int):
    with Session(get_engine()) as session:
        msg_obj_list = session.exec(
            select(Message).where(
                Message.chat_id == chat_id
            ).options(
                selectinload(Message.attachments)
                .selectinload(Attachment.document)
            )
        ).all()

        return [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'timestamp': msg.timestamp,
            'attachments': [
                {
                    'id': att.document.id,
                    'name': att.document.name,
                    'size': att.document.size,
                    'uri': att.document.uri
                } for att in msg.attachments
            ]
        } for msg in msg_obj_list]

def get_message(chat_id: int, msg_id: int):
    with Session(get_engine()) as session:
        msg = session.exec(
            select(Message).where(
                Message.chat_id == chat_id,
                Message.id == msg_id
            )
        ).one_or_none()

        return msg.model_dump() if msg is not None else None

def save_chunk(document_id: int, data):
    chunk = Chunk(
        id=None,
        document_id=document_id,
        page=data['page'],
        section=data['section'],
        model=data['model'],
        index=data['index'],
        text=data['text'],
        embedding=data['embedding']
    )

    with Session(get_engine()) as session:
        result = session.exec(select(Document).where(Document.id == document_id))

        chunk.document = result.one()

        session.add(chunk)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on create_chunk -> {e}")

        return chunk.model_dump()

def delete_chunks(document_id: int):
    with Session(get_engine()) as session:
        chunks = session.exec(select(Chunk).where(
            Chunk.document_id == document_id
        )).all()

        session.delete(chunks)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on delete_chunk -> {e}")

def get_chunk(document_id: int, index: int):
    with Session(get_engine()) as session:
        result = session.exec(select(Chunk).where(
            Chunk.document_id == document_id, Chunk.index == index
        )).one_or_none()

        return result.model_dump() if result else None

def get_chunks(document_id: int):
    with Session(get_engine()) as session:
        chunks = session.exec(select(Chunk).where(Chunk.document_id  == document_id)).all()

        if chunks is None:
            return None

        return [chunk.model_dump() for chunk in chunks]

def chunk_similarity_search(document_id: int, query, top_k: int):
    with Session(get_engine()) as session:
        if DbConfig.DB_PERSISTANT in CONSTRAINT:
            chunks = session.exec(select(Chunk).where(
                Chunk.document_id == document_id
            ).order_by(
                # Common use is Chunk.embedding.cosine_distance(...)
                # Used an alternative to avoid error lint on IDE
                Chunk.__table__.columns.embedding.cosine_distance(query)).limit(top_k)
            ).all()

            return [chunk.model_dump() for chunk in chunks]
        else:
            all_chunks = session.exec(select(Chunk).where(
                Chunk.document_id == document_id
            )).all()

            scores = []

            for chunk in all_chunks:
                a = np.asarray(chunk.embedding)
                b = np.asarray(query)

                similarity = np.dot(a, b) / (
                    np.linalg.norm(a) * np.linalg.norm(b)
                )

                scores.append((similarity, chunk))

            scores.sort(
                key=lambda x: x[0],
                reverse=True
            )

            chunks = scores[:top_k]

            return [chunk.model_dump() for _, chunk in chunks]

def save_summary(document_id: int, **data):
    summary = Summary(
        document_id=document_id,
        text=data['text']
    )

    with Session(get_engine()) as session:
        session.add(summary)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on save_sumary -> {e}")

        session.refresh(summary)

        return summary.model_dump()

def get_summary(tag):
    summary = None
    with Session(get_engine()) as session:
        if tag.get('document_id', None):
            summary = session.exec(select(Summary).where(
                Summary.document_id == tag['document_id']
            )).one_or_none()
        elif tag.get('document_hash', None):
            result = session.exec(select(Document).where(
                Document.hash == tag['document_hash']
            )).one_or_none()

            summary = result.summary if result else None
        elif tag.get('document_name', None):
            result = session.exec(select(Document).where(
                Document.name == tag['document_name']
            )).one_or_none()

            summary = result.summary if result else None

        return summary.model_dump() if summary else None

def create_memory(**data):
    mem = Memory(
        created_at=None, # implement
        modified_at=None, # implement
        used_model=data['used_model'],
        content=data['content'],
        embedding=data['embedding']
    )

    with Session(get_engine()) as session:
        session.add(mem)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'Error on create_memory -> {e}')

        session.refresh(mem)

        return mem.model_dump()

def update_memory(mem_id: int, **data):
    with Session(get_engine()) as session:
        mem = session.exec(select(Memory).where(
            Memory.id == mem_id
        )).one_or_none()

        mem.content = data['content']
        mem.embedding = data['embedding']
        mem.used_model = data['used_model']

        session.add(mem)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'Error on update_memory -> {e}')

        session.refresh(mem)

        return mem.model_dump()

def delete_memory(mem_id: int):
    with Session(get_engine()) as session:
        mem = session.exec(select(Memory).where(
            Memory.id == mem_id
        )).one_or_none()

        if mem is None:
            return None

        session.delete(mem)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f'Erron on delete_memory -> {e}')

        return bool(session.get(Memory, mem.id))

def search_memory(query, top_k: int):
    with Session(get_engine()) as session:
        if DbConfig.DB_PERSISTANT in CONSTRAINT:
            memories = session.exec(select(Memory).order_by(
                # Common use is Memory.embedding.cosine_distance(...)
                # Used an alternative to avoid error lint on IDE
                Memory.__table__.columns.embedding.cosine_distance(query)).limit(top_k)
            ).all()

            return [memory.model_dump() for memory in memories]
        else:
            all_memories = session.exec(select(Memory)).all()

            scores = []

            for memory in all_memories:
                a = np.asarray(memory.embedding)
                b = np.asarray(query)

                similarity = np.dot(a, b) / (
                    np.linalg.norm(a) * np.linalg.norm(b)
                )

                scores.append((similarity, memory))

            scores.sort(
                key=lambda x: x[0],
                reverse=True
            )

            memories = scores[:top_k]

            return [memory.model_dump() for _, memory in memories]
