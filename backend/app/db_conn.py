import os
from db_schema import Chat, Message, Attachment
from sqlmodel import create_engine, SQLModel, Session, select

_CONSTRAINT = ('1', 'y', 'yes', 'true')

class DbConfig:
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = os.getenv('DB_PORT')

    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    DB_PERSISTANT = os.getenv('DB_PERSISTANT', default="true")
    DB_ECHO = os.getenv('DB_ECHO', default="false")

echo = bool(DbConfig.DB_ECHO and DbConfig.DB_ECHO in _CONSTRAINT)

engine = None
if DbConfig.DB_PERSISTANT.strip().lower() in _CONSTRAINT:
    url = (
        f"postgresql+psycopg://"
        f"{DbConfig.DB_USER}:{DbConfig.DB_PASSWORD}"
        f"@{DbConfig.DB_HOST}:{DbConfig.DB_PORT}"
        f"/{DbConfig.DB_NAME}"
    )
    engine = create_engine(url, echo=echo)
else:
    engine = create_engine("sqlite://", echo=echo)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def add_chat():
    new_chat = Chat()

    with Session(engine) as session:
        session.add(new_chat)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on add_chat -> {e}")

        session.refresh(new_chat)

    return new_chat.model_dump()

def get_chats():
    with Session(engine) as session:
        chat_list = session.exec(select(Chat)).all()

        return [chat.model_dump() for chat in chat_list]

def get_chat(chat_id: int):
    with Session(engine) as session:
        statement = select(Chat).where(Chat.id == chat_id)
        result = session.exec(statement)

        chat = result.first()

        return chat.model_dump() if chat is not None else None

def update_chat(chat_id: int, title):
    with Session(engine) as session:
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
    with Session(engine) as session:
        statement = select(Chat).where(Chat.id == chat_id)
        result = session.exec(statement)
        session.delete(result.one())

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on delete_chat -> {e}")

        return bool(session.get(Chat, chat_id) is None)

def create_attachment(message_id: int, data):
    att = Attachment(
        id=data['id'],
        name=data['name'],
        size=data['size'],
        path=data['path'],
        message_id=message_id
    )

    with Session(engine) as session:
        result = session.exec(select(Message).where(Message.id == message_id))

        att.message = result.one()

        session.add(att)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on create_attachment -> {e}")

        session.refresh(att)

        result = session.exec(select(Attachment).where(
            Attachment.message_id == message_id, Attachment.id == att.id
        )).one_or_none()

        return result.model_dump() if result is not None else None

def get_attachment_by_name(chat_id: int, name: str):
    with Session(engine) as session:
        result = session.exec(select(Attachment).where(
            Attachment.chat_id == chat_id, Attachment.name == name
        )).one_or_none()

        return result.model_dump() if result is not None else None

def get_attachments_by_chat_id(chat_id: int):
    with Session(engine) as session:
        result = session.exec(select(Attachment).where(
            Attachment.chat_id == chat_id
        )).all()

        return [r.model_dump() for r in result]

def get_attachments_by_msg_id(chat_id: int, msg_id: int):
    with Session(engine) as session:
        result = session.exec(select(Attachment).where(
            Attachment.chat_id == chat_id, Attachment.message_id == msg_id
        )).all()

        return [r.model_dump() for r in result]

def update_attachment(chat_id: int, file_name: str, new_data: str):
    with Session(engine) as session:
        result = session.exec(select(Attachment).where(
            Attachment.chat_id == chat_id, Attachment.name == file_name
        )).one_or_none()

        if result is None:
            return None

        result.path = new_data

        session.add(result)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on update_attachment -> {e}")

        session.refresh(result)

        return result.model_dump()

def add_message(chat_id: int, data):
    msg = Message(
        id=data['id'],
        role=data['role'],
        content=data['content'],
        timestamp=data['timestamp'],
        chat_id=chat_id
    )

    if data['attachments']:
        msg.attachments = [
            Attachment(
                name=att['name'],
                size=att['size'],
                path=att['path'],
                chat_id=chat_id
            ) for att in data['attachments']
        ]
    else:
        msg.attachments = []

    with Session(engine) as session:
        result = session.exec(select(Chat).where(Chat.id == chat_id))

        msg.chat = result.one()

        session.add(msg)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on add_message -> {e}")

        session.refresh(msg)

        result = session.exec(select(Message).where(
            Message.chat_id == chat_id, Message.id == msg.id
        )).one_or_none()

        return result.model_dump() if result is not None else None

def update_message(chat_id: int, data):
    with Session(engine) as session:
        msg = session.exec(select(Message).where(
            Message.chat_id == chat_id, Message.id == data['id']
        )).one_or_none()

        if msg is None:
            return None

        msg.role = data['role']
        msg.content = data['content']
        msg.timestamp = data['timestamp']

        session.add(msg)

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error on update_message -> {e}")

        session.refresh(msg)

        return msg.model_dump()

def get_messages(chat_id: int):
    with Session(engine) as session:
        msg_obj_list = session.exec(select(Message).where(Message.chat_id == chat_id)).all()

        return [msg.model_dump() for msg in msg_obj_list]

if __name__ != '__main__':
    create_db_and_tables()
