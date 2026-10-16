from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

Database_URL = "sqlite:///./enquiry_automation.db"

engine = create_engine(
    Database_URL, 
    connect_args={"check_same_thread": False}
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()