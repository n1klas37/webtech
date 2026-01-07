from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


# --- Helper for validation ---
def validate_strong_password(v: str) -> str:
    """Prüft Passwortrichtlinien (Min 8 Zeichen, Zahl, Großbuchstabe)"""
    if v is None: return v

    if len(v) < 8:
        raise ValueError('Passwort muss mindestens 8 Zeichen lang sein')
    if not re.search(r"\d", v):
        raise ValueError('Passwort muss mindestens eine Zahl enthalten')
    if not re.search(r"[A-Z]", v):
        raise ValueError('Passwort muss mindestens einen Großbuchstaben enthalten')
    return v


# --- Authentication & User ---

class UserRegister(BaseModel):
    name: str = Field(..., min_length=3)
    email: EmailStr = Field(...)
    password: str = Field(...)

    @field_validator('password')
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)


class UserLogin(BaseModel):
    name: str
    password: str


class LoginSuccess(BaseModel):
    success: bool
    token: str
    name: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3)
    email: Optional[EmailStr] = Field(None)
    password: Optional[str] = Field(None)

    @field_validator('password')
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)


# --- Categories ---

class FieldSchema(BaseModel):
    label: str
    data_type: str
    unit: Optional[str] = ""

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    fields: List[FieldSchema]


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryOut(CategoryCreate):
    id: int


# --- Entries ---

class EntryCreate(BaseModel):
    category_id: int
    occurred_at: datetime
    note: Optional[str] = ""
    values: Dict[str, Any]


class EntryOut(BaseModel):
    id: int
    category_id: int
    occurred_at: datetime
    note: Optional[str]
    data: Dict[str, Any]

    class Config:
        from_attributes = True