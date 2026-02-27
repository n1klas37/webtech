"""
Database models definition module.
Utilizes SQLAlchemy's Object-Relational Mapping (ORM) to define the database schema,
relationships, and constraints using Python classes.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from app.database import Base


# --- User & Session ---

class User(Base):
    """
    Core identity model representing a system user.
    Stores authentication credentials and manages the double opt-in verification state.
    """
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Lambda ensures the datetime is evaluated at insertion time, not at module load
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    # Double opt-in fields
    is_active = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)

    # Relationships with cascading deletes: Removing a user removes all their associated data
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    """
    Session model for token-based authentication.
    Validates API requests by linking a Bearer token to a specific user and expiration date.
    """
    __tablename__ = "session"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


# --- Categories ---

class Category(Base):
    """
    Metadata model for tracking domains (e.g., 'Fitness', 'Nutrition').
    Acts as a schema provider dictating the structure of tracking entries to the frontend.
    """
    __tablename__ = "category"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text)

    # Protects system-generated core categories from being deleted or modified by the user
    is_system_default = Column(Boolean, default=False)

    user = relationship("User", back_populates="categories")
    fields = relationship("CategoryField", back_populates="category", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="category", cascade="all, delete-orphan")


class CategoryField(Base):
    """
    Defines individual data points within a Category (e.g., 'Duration' in minutes).
    Enables dynamic form generation in the frontend UI.
    """
    __tablename__ = "category_field"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id"))
    label = Column(String, nullable=False)
    data_type = Column(String, nullable=False) # Expected values: 'number' or 'text'
    unit = Column(String)

    category = relationship("Category", back_populates="fields")


# --- Entries ---

class Entry(Base):
    """
    Transactional tracking data model.
    Implements the hybrid database approach: Relational metadata combined with
    a schemaless JSON column for highly flexible data point storage.
    """
    __tablename__ = "entry"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"))

    # Lambda ensures the datetime is evaluated at insertion time, not at module load
    occurred_at = Column(DateTime, default=lambda: datetime.now(UTC))

    note = Column(Text)
    data = Column(JSON)

    user = relationship("User", back_populates="entries")
    category = relationship("Category", back_populates="entries")