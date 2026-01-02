from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from database import Base

from datetime import datetime


# --- USER & SESSION ---

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    # ÄNDERUNG: name statt username, email hinzugefügt
    name = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationen
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "session"
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


# --- KATEGORIEN ---

class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text)

    user = relationship("User", back_populates="categories")
    fields = relationship("CategoryField", back_populates="category", cascade="all, delete-orphan")
    entries = relationship("Entry", back_populates="category", cascade="all, delete-orphan")


class CategoryField(Base):
    __tablename__ = "category_field"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id"))

    label = Column(String, nullable=False)
    data_type = Column(String, nullable=False)  # 'number', 'text', 'bool'
    unit = Column(String)

    category = relationship("Category", back_populates="fields")


# --- EINTRÄGE ---

class Entry(Base):
    __tablename__ = "entry"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"))

    # DateTime Objekt
    occurred_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text)

    # JSON Daten
    data = Column(JSON)

    user = relationship("User", back_populates="entries")
    category = relationship("Category", back_populates="entries")