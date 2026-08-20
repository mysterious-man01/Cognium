from sqlmodel import create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from config import DbConfig, CONSTRAINT

_engine = None

def get_engine():
    global _engine

    if _engine is None:
        _engine = init_db()

    return _engine

def init_db():
    echo = bool(DbConfig.DB_ECHO and DbConfig.DB_ECHO in CONSTRAINT)
    if DbConfig.DB_PERSISTANT.strip().lower() in CONSTRAINT:
        url = (
            f"postgresql+psycopg://"
            f"{DbConfig.DB_USER}:{DbConfig.DB_PASSWORD}"
            f"@{DbConfig.DB_HOST}:{DbConfig.DB_PORT}"
            f"/{DbConfig.DB_NAME}"
        )
        eng = create_engine(url, echo=echo)
    else:
        eng = create_engine(
            "sqlite://",
            connect_args={
                'check_same_thread': False,
            },
            poolclass=StaticPool,
            echo=echo
        )

    SQLModel.metadata.create_all(eng)

    return eng
