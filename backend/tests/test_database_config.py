from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.core.database import Base, get_engine_options, normalize_database_url


def test_sqlite_engine_options_keep_local_development_compatibility():
    database_url = "sqlite:///app/data/app.db"

    assert normalize_database_url(database_url) == database_url
    assert get_engine_options(database_url) == {
        "connect_args": {
            "check_same_thread": False,
        }
    }


def test_postgresql_urls_use_psycopg_driver_without_sqlite_options():
    assert normalize_database_url(
        "postgresql://user:password@localhost:5432/edu_agent"
    ) == "postgresql+psycopg://user:password@localhost:5432/edu_agent"
    assert normalize_database_url(
        "postgres://user:password@localhost:5432/edu_agent"
    ) == "postgresql+psycopg://user:password@localhost:5432/edu_agent"
    assert get_engine_options(
        "postgresql+psycopg://user:password@localhost:5432/edu_agent"
    ) == {}


def test_all_models_compile_with_postgresql_dialect():
    compiled_tables = {
        table.name: str(CreateTable(table).compile(dialect=postgresql.dialect()))
        for table in Base.metadata.sorted_tables
    }

    assert set(compiled_tables) == {
        "knowledge_items",
        "conversations",
        "handoff_tickets",
        "unanswered_questions",
        "feedback",
    }

    assert "JSON" in compiled_tables["knowledge_items"]
    assert "BOOLEAN" in compiled_tables["conversations"]
