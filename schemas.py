from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# --- AUTH ---
class UserRegister(BaseModel):
    # ÄNDERUNG: name statt username
    name: str = Field(..., min_length=3)
    email: str = Field(...)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    name: str  # Login jetzt via name
    password: str


class LoginSuccess(BaseModel):
    success: bool
    token: str
    name: str


# --- DATA ---
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


class CategoryOut(CategoryCreate):
    id: int


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