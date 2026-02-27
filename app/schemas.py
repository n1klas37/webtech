"""
Data validation and serialization module.
Utilizes Pydantic to define Data Transfer Objects (DTOs) ensuring strict typing
for incoming requests and filtering sensitive information from outgoing responses.
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


# Helper for validation
def validate_strong_password(v: str) -> str:
    """
    Checks password policies using regular expressions.
    Enforces minimum length (8), at least one digit, and one uppercase letter.
    """
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
    """
    Schema for incoming user registration requests.
    Validates email format and password complexity before hitting the database.
    """
    name: str = Field(..., min_length=3)
    email: EmailStr = Field(...)
    password: str = Field(...)

    @field_validator('password')
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)


class UserLogin(BaseModel):
    """Schema for incoming login credentials."""
    name: str
    password: str


class UserVerify(BaseModel):
    """Schema for the double opt-in verification process."""
    email: EmailStr
    code: str


class LoginSuccess(BaseModel):
    """Response schema upon successful authentication, containing the Bearer token."""
    success: bool
    token: Optional[str] = None
    name: Optional[str] = None
    message: Optional[str] = None


class UserOut(BaseModel):
    """
    Response schema for user data.
    Acts as a filter preventing sensitive data (like password_hash) from being exposed.
    """
    id: int
    name: str
    email: str
    created_at: datetime
    is_active: bool

    # Enables automatic conversion from SQLAlchemy ORM objects to Pydantic models
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """
    Schema for partial user profile updates.
    All fields are optional to allow selective patching.
    """
    name: Optional[str] = Field(None, min_length=3)
    email: Optional[EmailStr] = Field(None)
    password: Optional[str] = Field(None)

    @field_validator('password')
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)


# --- Categories ---

class FieldSchema(BaseModel):
    """
    Defines the structural metadata for a specific tracking field.
    Passed to the frontend to render dynamic input forms.
    """
    label: str
    data_type: str
    unit: Optional[str] = ""

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    """Schema for creating a new custom tracking category including its nested fields."""
    name: str
    description: Optional[str] = ""
    fields: List[FieldSchema]


class CategoryUpdate(BaseModel):
    """Schema for updating basic category metadata."""
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryOut(CategoryCreate):
    """
    Response schema representing a full category.
    Inherits fields from CategoryCreate and adds system-specific identifiers.
    """
    id: int
    is_system_default: bool

    model_config = {"from_attributes": True}


# --- Entries ---

class EntryCreate(BaseModel):
    """
    Schema for incoming tracking entries.
    Demonstrates the hybrid data approach: structured metadata combined with
    a highly flexible 'values' dictionary for arbitrary JSON payloads.
    """
    category_id: int
    occurred_at: datetime
    note: Optional[str] = ""
    values: Dict[str, Any]


class EntryOut(BaseModel):
    """Response schema for returning tracking entries to the client."""
    id: int
    category_id: int
    occurred_at: datetime
    note: Optional[str]
    data: Dict[str, Any]

    model_config = {"from_attributes": True}