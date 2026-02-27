"""
Database configuration and session management module.
Handles connection strings, environment variables, and provides the dependency
injection for isolated database sessions per request.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# Retrieve the database connection string from environment variables.
# If no variable is set (e.g., in local development), fallback to a local SQLite database.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tracker.db")

# Dialect compatibility fix for Render hosting.
# Render often provides URLs starting with "postgres://", but modern SQLAlchemy
# explicitly requires the "postgresql://" dialect.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure connection arguments based on the active database system.
# The 'check_same_thread' argument must be False for SQLite in FastAPI's asynchronous
# environment to prevent thread-sharing errors. This argument is invalid for PostgreSQL.
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy engine which acts as the central source of database connections.
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Configure the local session factory (disabled autocommit and autoflush for transaction safety).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative ORM models.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that provides an isolated database session per request.
    Utilizes a yield/finally block to guarantee the session is closed,
    preventing resource leaks regardless of the transaction's success.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()