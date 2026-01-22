import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. URL aus den Environment Variables holen (für Render)
# Wenn keine Variable da ist (lokal), Fallback auf SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tracker.db")

# 2. Fix für Render/SQLAlchemy: 
# Render liefert oft URLs mit "postgres://", SQLAlchemy erwartet aber "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 3. Argumente konfigurieren
# check_same_thread ist NUR für SQLite notwendig, bei Postgres führt es zu Fehlern
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# 4. Engine erstellen
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()