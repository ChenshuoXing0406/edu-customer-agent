import os
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"
STATIC_DIR = APP_DIR / "static"

load_dotenv(APP_DIR.parent / ".env")

DATABASE_PATH = DATA_DIR / "app.db"
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DATABASE_PATH.as_posix()}"
KNOWLEDGE_SEED_PATH = DATA_DIR / "knowledge_base.json"
SESSION_SECRET_KEY = (
    os.getenv("SESSION_SECRET_KEY") or "local-development-session-secret"
)
