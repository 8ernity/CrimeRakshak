"""SQLAlchemy engine, session factory, and declarative base."""
from collections.abc import Generator
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger("database")


class Base(DeclarativeBase):
    """Declarative base shared by every ORM model."""


def _init_engine():
    try:
        eng = create_engine(
            settings.sqlalchemy_database_uri,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            future=True,
        )
        with eng.connect() as conn:
            pass
        return eng
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection failed ({e}). Falling back to local SQLite database."
        )
        sqlite_uri = "sqlite:///./crimerakshak.db"
        eng = create_engine(sqlite_uri, connect_args={"check_same_thread": False})
        import app.models.rbac  # ensure models are loaded
        try:
            import app.investigation_ai.models
        except Exception:
            pass
        Base.metadata.create_all(bind=eng)
        _ensure_sqlite_schema(sqlite_uri)
        return eng


def _ensure_sqlite_schema(sqlite_uri: str):
    """Ensure missing columns and tables in SQLite are created automatically."""
    try:
        import sqlite3
        db_path = sqlite_uri.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='investigation_events'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(investigation_events)")
            cols = {r[1] for r in cursor.fetchall()}
            if "tracking_id" not in cols:
                cursor.execute("ALTER TABLE investigation_events ADD COLUMN tracking_id INTEGER")
            if "confidence" not in cols:
                cursor.execute("ALTER TABLE investigation_events ADD COLUMN confidence FLOAT")
            conn.commit()

        # Create investigation_crime_decisions table if missing
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='investigation_crime_decisions'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE investigation_crime_decisions (
                    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    job_id INTEGER,
                    decision VARCHAR(50) NOT NULL,
                    confidence FLOAT NOT NULL,
                    evidence_score FLOAT NOT NULL,
                    reasons TEXT NOT NULL,
                    evidence_events TEXT,
                    timestamps TEXT,
                    track_ids TEXT,
                    safeguards_triggered TEXT,
                    is_video BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(media_id) REFERENCES investigation_media(media_id) ON DELETE CASCADE,
                    FOREIGN KEY(job_id) REFERENCES investigation_analysis_jobs(job_id) ON DELETE SET NULL
                )
            """)
            conn.commit()

        conn.close()
    except Exception as e:
        logger.warning(f"SQLite schema migration check skipped: {e}")


engine = _init_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator:
    """FastAPI dependency that yields a request-scoped database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

