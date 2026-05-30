import json
from contextlib import contextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL, DATA_DIR, KNOWLEDGE_SEED_PATH


class Base(DeclarativeBase):
    pass


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


def get_engine_options(database_url: str) -> dict:
    if make_url(database_url).get_backend_name() == "sqlite":
        return {"connect_args": {"check_same_thread": False}}

    return {}


ENGINE_DATABASE_URL = normalize_database_url(DATABASE_URL)
engine = create_engine(ENGINE_DATABASE_URL, **get_engine_options(ENGINE_DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope():
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database() -> None:
    from app.models import KnowledgeItem

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    with session_scope() as session:
        has_knowledge = session.scalar(select(KnowledgeItem.id).limit(1))

        if has_knowledge is not None:
            return

        with open(KNOWLEDGE_SEED_PATH, "r", encoding="utf-8") as file:
            seed_items = json.load(file)

        for item in seed_items:
            session.add(
                KnowledgeItem(
                    id=item["id"],
                    title=item["title"],
                    category=item["category"],
                    keywords=item.get("keywords", []),
                    content=item["content"],
                )
            )
