from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# local SQLite database file
DATABASE_URL = "sqlite:///./tracker.db"


# connect_args={"check_same_thread": False} is necessary for the SQLite database
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


# Dependency for FastAPI Endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()