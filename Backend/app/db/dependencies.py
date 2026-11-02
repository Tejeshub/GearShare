from collections.abc import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional SQLAlchemy database session.
    Closes the session after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
