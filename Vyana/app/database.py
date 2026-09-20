from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

DATABASE_URL = settings.database_url


def _create_db_engine():
    global DATABASE_URL
    if DATABASE_URL.startswith("sqlite"):
        return create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})

    try:
        test_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with test_engine.connect():
            pass
        return test_engine
    except Exception as exc:
        fallback = settings.sqlite_fallback_url or "sqlite:///./vyana.db"
        print(f"[DATABASE] Database connection failed ({exc}). Falling back to SQLite: {fallback}")
        DATABASE_URL = fallback
        return create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False})



engine = _create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

