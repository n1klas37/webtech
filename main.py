from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from database import engine, get_db, Base
import models
import schemas

# DB Init
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Life-OS API", version="1.0.0")

# Config
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper ---

def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_defaults_for_user(user_id: int, db: Session):
    # 1. Fitness
    cat_fit = models.Category(user_id=user_id, name="🚴 Fitness", description="Training")
    db.add(cat_fit)
    db.commit()
    db.add(models.CategoryField(category_id=cat_fit.id, label="Übung", data_type="text"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Dauer", data_type="number", unit="Minuten"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Strecke", data_type="number", unit="km"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Gewicht", data_type="number", unit="kg"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Energie", data_type="number", unit="kcal"))

    # 2. Ernährung
    cat_fit = models.Category(user_id=user_id, name="🍎 Ernährung", description="Ernährung")
    db.add(cat_fit)
    db.commit()
    db.add(models.CategoryField(category_id=cat_fit.id, label="Lebensmittel", data_type="text"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Gewicht", data_type="number", unit="g"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Energie", data_type="number", unit="kcal"))

    # 3. Laune
    cat_diary = models.Category(user_id=user_id, name="📖 Tagebuch", description="Gedanken")
    db.add(cat_diary)
    db.commit()
    db.add(models.CategoryField(category_id=cat_diary.id, label="Laune", data_type="number", unit="1-10"))
    db.add(models.CategoryField(category_id=cat_diary.id, label="Highlight", data_type="text"))
    db.commit()

    # 4. Schlaf
    cat_diary = models.Category(user_id=user_id, name="💤 Schlaf", description="Hier kannst du deinen Schlaf tracken.")
    db.add(cat_diary)
    db.commit()
    db.add(models.CategoryField(category_id=cat_diary.id, label="Dauer", data_type="number", unit="Stunden"))
    db.add(models.CategoryField(category_id=cat_diary.id, label="Erholung", data_type="number", unit="1-10"))
    db.commit()


# --- Security dependency ---

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    session = db.query(models.Session).filter(models.Session.token == token).first()

    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session.user


# --- Authentication routes (public) ---

@app.post("/register", response_model=schemas.LoginSuccess)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    # 1. Name Check
    if db.query(models.User).filter(models.User.name == user_data.name).first():
        raise HTTPException(400, "Name already exists")
    # 2. Email Check
    if db.query(models.User).filter(models.User.email == user_data.email).first():
        raise HTTPException(400, "Email already exists")

    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    create_defaults_for_user(new_user.id, db)

    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=30)
    db.add(models.Session(token=token, user_id=new_user.id, expires_at=expires))
    db.commit()

    return {"success": True, "token": token, "name": new_user.name}


@app.post("/login", response_model=schemas.LoginSuccess)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == user_data.name).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(401, "Incorrect name or password")

    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(days=30)
    db.add(models.Session(token=token, user_id=user.id, expires_at=expires))
    db.commit()
    return {"success": True, "token": token, "name": user.name}


# --- User routes ---

@app.get("/user", response_model=schemas.UserOut)
def get_user_profile(user: models.User = Depends(get_current_user)):
    return user


@app.put("/user", response_model=schemas.UserOut)
def update_user_profile(
        user_data: schemas.UserUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(get_current_user)
):
    if user_data.name:
        existing = db.query(models.User).filter(models.User.name == user_data.name).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(400, "Name already taken")
        current_user.name = user_data.name

    if user_data.email:
        existing = db.query(models.User).filter(models.User.email == user_data.email).first()
        if existing and existing.id != current_user.id:
            raise HTTPException(400, "Email already taken")
        current_user.email = user_data.email

    if user_data.password:
        current_user.password_hash = get_password_hash(user_data.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@app.delete("/user")
def delete_user_account(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user_id = current_user.id
    db.delete(current_user)
    db.commit()
    return {"status": "deleted", "id": user_id}


# --- Category routes ---

@app.get("/categories/", response_model=List[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Category).filter(models.Category.user_id == user.id).order_by(models.Category.id).all()


@app.post("/categories/", response_model=schemas.CategoryOut)
def create_category(cat: schemas.CategoryCreate, db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    db_cat = models.Category(name=cat.name, description=cat.description, user_id=user.id)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    for f in cat.fields:
        db.add(models.CategoryField(category_id=db_cat.id, label=f.label, data_type=f.data_type, unit=f.unit))
    db.commit()
    db.refresh(db_cat)
    return db_cat


@app.put("/categories/{category_id}", response_model=schemas.CategoryOut)
def update_category(
        category_id: int,
        cat_update: schemas.CategoryUpdate,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    cat = db.query(models.Category).filter(models.Category.id == category_id,
                                           models.Category.user_id == user.id).first()
    if not cat: raise HTTPException(404, "Category not found")

    if cat_update.name is not None:
        cat.name = cat_update.name
    if cat_update.description is not None:
        cat.description = cat_update.description

    db.commit()
    db.refresh(cat)
    return cat


@app.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    cat = db.query(models.Category).filter(models.Category.id == category_id,
                                           models.Category.user_id == user.id).first()
    if not cat: raise HTTPException(404, "Not found")
    db.delete(cat)  # Cascading delete löscht Felder & Einträge
    db.commit()
    return {"status": "deleted", "id": category_id}


# --- Entry routes ---

@app.get("/entries/", response_model=List[schemas.EntryOut])
def get_entries(
        category_id: Optional[int] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    query = db.query(models.Entry).filter(models.Entry.user_id == user.id)
    if category_id: query = query.filter(models.Entry.category_id == category_id)
    if start: query = query.filter(models.Entry.occurred_at >= start)
    if end: query = query.filter(models.Entry.occurred_at <= end)

    return query.order_by(models.Entry.occurred_at.desc()).all()


@app.post("/entries/", response_model=schemas.EntryOut)
def create_entry(item: schemas.EntryCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(get_current_user)):
    if not db.query(models.Category).filter(models.Category.id == item.category_id,
                                            models.Category.user_id == user.id).first():
        raise HTTPException(404, "Category not found")

    new_entry = models.Entry(
        category_id=item.category_id,
        user_id=user.id,
        occurred_at=item.occurred_at,
        note=item.note,
        data=item.values
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


@app.put("/entries/{entry_id}", response_model=schemas.EntryOut)
def update_entry(
        entry_id: int,
        item: schemas.EntryCreate,
        db: Session = Depends(get_db),
        user: models.User = Depends(get_current_user)
):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id, models.Entry.user_id == user.id).first()
    if not entry: raise HTTPException(404, "Entry not found")

    if item.category_id != entry.category_id:
        if not db.query(models.Category).filter(models.Category.id == item.category_id,
                                                models.Category.user_id == user.id).first():
            raise HTTPException(404, "Category not found")

    entry.category_id = item.category_id
    entry.occurred_at = item.occurred_at
    entry.note = item.note
    entry.data = item.values

    db.commit()
    db.refresh(entry)
    return entry


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id, models.Entry.user_id == user.id).first()
    if not entry: raise HTTPException(404, "Not found")
    db.delete(entry)
    db.commit()
    return {"status": "deleted", "id": entry_id}


# --- Reports (Placeholder for future extensions) ---

@app.get("/reports/")
def get_reports(): return []


@app.post("/reports/")
def create_report(): return {}


@app.delete("/reports/{report_id}")
def delete_report(report_id: int): return {}




app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
