from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

# Importe aus unseren eigenen Modulen
from database import engine, get_db, Base
import models
import schemas

# Tabellen erstellen (falls nicht vorhanden)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Life-OS API", version="1.0.0")

# --- KONFIGURATION ---

# Passwort-Hashing Setup (Argon2 gegen den 72-byte Fehler)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Security Scheme für Swagger UI
# Das sagt der Doku: "Wir nutzen Token-Auth".
# 'tokenUrl' ist der Pfad, wo man sich einloggt (nur Info für Swagger).
security = HTTPBearer()

# CORS Setup (Damit Frontend & Backend reden dürfen)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- HELPER FUNKTIONEN ---

def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_defaults_for_user(user_id: int, db: Session):
    """Erstellt Standard-Kategorien für neue User"""
    # 1. Fitness
    cat_fit = models.Category(user_id=user_id, name="Fitness", description="Training")
    db.add(cat_fit)
    db.commit()
    db.add(models.CategoryField(category_id=cat_fit.id, label="Uebung", data_type="text"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Gewicht", data_type="number", unit="kg"))

    # 2. Tagebuch
    cat_diary = models.Category(user_id=user_id, name="Tagebuch", description="Gedanken")
    db.add(cat_diary)
    db.commit()
    db.add(models.CategoryField(category_id=cat_diary.id, label="Laune", data_type="number", unit="1-10"))
    db.commit()


# --- SECURITY DEPENDENCY (Der "Türsteher") ---

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    credentials.credentials enthält den reinen Token-String.
    FastAPI prüft automatisch, ob der Header "Authorization: Bearer <token>" vorhanden ist.
    """
    token = credentials.credentials

    # Ab hier bleibt alles gleich wie vorher!
    session = db.query(models.Session).filter(models.Session.token == token).first()

    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session.user


# --- AUTH ROUTES (Öffentlich) ---

@app.post("/api/register", response_model=schemas.LoginSuccess)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    # Check ob Name schon existiert
    if db.query(models.User).filter(models.User.name == user_data.name).first():
        raise HTTPException(status_code=400, detail="Name already exists")

    # User erstellen
    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Standard-Daten anlegen
    create_defaults_for_user(new_user.id, db)

    # Auto-Login (Token erstellen)
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=30)
    db.add(models.Session(token=token, user_id=new_user.id, expires_at=expires))
    db.commit()

    return {"success": True, "token": token, "name": new_user.name}


@app.post("/api/login", response_model=schemas.LoginSuccess)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # Suche nach name
    user = db.query(models.User).filter(models.User.name == user_data.name).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect name or password")

    # Neuen Token erstellen
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=30)
    db.add(models.Session(token=token, user_id=user.id, expires_at=expires))
    db.commit()

    return {"success": True, "token": token, "name": user.name}


# --- DATA ROUTES (Geschützt durch Token) ---

@app.get("/categories/", response_model=List[schemas.CategoryOut])
def get_categories(
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    return db.query(models.Category).filter(models.Category.user_id == user.id).all()


@app.post("/categories/", response_model=schemas.CategoryOut)
def create_category(
        cat: schemas.CategoryCreate,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    db_cat = models.Category(name=cat.name, description=cat.description, user_id=user.id)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)

    for f in cat.fields:
        db.add(models.CategoryField(
            category_id=db_cat.id,
            label=f.label,
            data_type=f.data_type,
            unit=f.unit
        ))
    db.commit()
    db.refresh(db_cat)
    return db_cat


@app.get("/entries/", response_model=List[schemas.EntryOut])
def get_entries(
        category_id: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    query = db.query(models.Entry).filter(models.Entry.user_id == user.id)

    if category_id:
        query = query.filter(models.Entry.category_id == category_id)
    if start:
        query = query.filter(models.Entry.occurred_at >= start)
    if end:
        query = query.filter(models.Entry.occurred_at <= end)

    return query.order_by(models.Entry.occurred_at.desc()).all()


@app.post("/entries/", response_model=schemas.EntryOut)
def create_entry(
        item: schemas.EntryCreate,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    # Security Check: Gehört die Kategorie dem User?
    if not db.query(models.Category).filter(models.Category.id == item.category_id,
                                            models.Category.user_id == user.id).first():
        raise HTTPException(status_code=404, detail="Category not found")

    new_entry = models.Entry(
        category_id=item.category_id,
        user_id=user.id,
        occurred_at=item.occurred_at,  # Pydantic hat hier schon ein datetime Objekt draus gemacht
        note=item.note,
        data=item.values
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


@app.delete("/entries/{entry_id}")
def delete_entry(
        entry_id: int,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    entry = db.query(models.Entry).filter(
        models.Entry.id == entry_id,
        models.Entry.user_id == user.id
    ).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()
    return {"status": "deleted", "id": entry_id}


# ... dein ganzer bisheriger Code ...

if __name__ == "__main__":
    import uvicorn
    # Startet den Server auf Port 8000
    # "main:app" bedeutet: Datei main.py, Variable app
    # reload=True sorgt dafür, dass der Server neu startet, wenn du Code änderst (nur für Entwicklung!)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)