import string
import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import uuid
import random
from datetime import datetime, timedelta, UTC
from typing import List, Optional

from database import engine, get_db, Base
from auth import get_current_user, get_password_hash, verify_password
import models
import schemas

load_dotenv()

# DB Init
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lifetracker API", version="1.0.0")

# Config
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_USERNAME"),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = False
)

EMAIL_VERIFICATION_ENABLED = os.getenv("EMAIL_VERIFICATION_ENABLED", "True") == "True"



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper ---

def create_defaults_for_user(user_id: int, db: Session):
    # 1. Fitness
    cat_fit = models.Category(user_id=user_id,
                              name="🚴 Fitness",
                              description="Hier kannst du dein Training tracken.",
                              is_system_default=True)

    db.add(cat_fit)
    db.commit()

    db.add(models.CategoryField(category_id=cat_fit.id, label="Übung", data_type="text"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Dauer", data_type="number", unit="Minuten"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Strecke", data_type="number", unit="km"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Gewicht", data_type="number", unit="kg"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Energie", data_type="number", unit="kcal"))

    # 2. Ernährung
    cat_fit = models.Category(user_id=user_id,
                              name="🍎 Ernährung",
                              description="Hier kannst du deine Ernährung tracken.",
                              is_system_default=True)
    db.add(cat_fit)
    db.commit()

    db.add(models.CategoryField(category_id=cat_fit.id, label="Lebensmittel", data_type="text"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Gewicht", data_type="number", unit="g"))
    db.add(models.CategoryField(category_id=cat_fit.id, label="Energie", data_type="number", unit="kcal"))
    db.commit()

    # 3. Laune
    cat_diary = models.Category(user_id=user_id,
                                name="📖 Tagebuch",
                                description="Hier kannst du deine Stimmung tracken.",
                                is_system_default=True)
    db.add(cat_diary)
    db.commit()

    db.add(models.CategoryField(category_id=cat_diary.id, label="Laune", data_type="number", unit="/10"))
    db.add(models.CategoryField(category_id=cat_diary.id, label="Highlight", data_type="text"))
    db.commit()

    # 4. Schlaf
    cat_diary = models.Category(user_id=user_id,
                                name="💤 Schlaf",
                                description="Hier kannst du deinen Schlaf tracken.",
                                is_system_default=True)
    db.add(cat_diary)
    db.commit()

    db.add(models.CategoryField(category_id=cat_diary.id, label="Dauer", data_type="number", unit="Stunden"))
    db.add(models.CategoryField(category_id=cat_diary.id, label="Erholung", data_type="number", unit="/10"))
    db.commit()



# --- Authentication routes (public) ---

@app.post("/register", response_model=schemas.LoginSuccess)
async def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.name == user_data.name) |
        (models.User.email ==user_data.email)
    ).first()

    # Check if user exists
    if existing_user:
        # If yes, and user is acive, reject registration
        if existing_user.is_active:
            raise HTTPException(400, "Benutername oder Email Adresse bereits vergeben.")
        # If yes, but user is not active, check if registration is expired (15min)
        else:
            expiry_limit = datetime.now(UTC) - timedelta(minutes=15)

            created_at_utc = existing_user.created_at
            # Ensure created_at is timezone-aware in UTC
            if created_at_utc.tzinfo is None:
                created_at_utc = created_at_utc.replace(tzinfo=UTC)

            # If registration is expired, delete old user and allow new registration
            if created_at_utc < expiry_limit:
                db.delete(existing_user)
                db.commit()
            # If registration is not expired, reject registration and ask user to check email or wait
            else:
                raise HTTPException(400, detail="Registrierung wurde gestartet. Bitte E-Mails überprüfen oder 15 Minuten warten.")


    # Email verification
    is_active_status = True
    verification_code = None

    if EMAIL_VERIFICATION_ENABLED:
        is_active_status = False
        verification_code = ''.join(random.choices(string.digits, k=6))

    html_content = f"""
            <h1>Willkommen beim Lifetracker!</h1>
            <p>Dein Verifizierungscode lautet:</p>
            <h2 style="background: #eee; padding: 10px; display: inline-block;">{verification_code}</h2>
            <p>Bitte gib diesen Code in der App ein.</p>
            """

    message = MessageSchema(
        subject="Dein Lifetracker Code",
        recipients=[user_data.email],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    new_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        is_active = is_active_status,
        verification_code=verification_code
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    create_defaults_for_user(new_user.id, db)

    if EMAIL_VERIFICATION_ENABLED:
        return {
            "success": True,
            "message": "Bitte E-Mail prüfen und Code eingeben.",
            "token": None,
            "name": new_user.name
        }

    token = str(uuid.uuid4())
    expires = datetime.now(UTC) + timedelta(days=30)
    db.add(models.Session(token=token, user_id=new_user.id, expires_at=expires))
    db.commit()

    return {"success": True, "token": token, "name": new_user.name}


@app.post("/verify")
def verify_email(data: schemas.UserVerify, db: Session = Depends(get_db)):
    """Prüft den Code und schaltet den Benutzer frei."""
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(404, "Benutzer nicht gefunden")

    if user.is_active:
        return {"message": "Bereits aktiviert"}

    if user.verification_code != data.code:
        raise HTTPException(400, "Falscher Verifizierungscode")

    user.is_active = True
    user.verification_code = None
    db.commit()

    return {"message": "Account wurde erfolgreich aktiviert, bitte mit Anmeldung fortfahren."}


@app.post("/login", response_model=schemas.LoginSuccess)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == user_data.name).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(401, "Benutzername oder Passwort falsch")
    
    if not user.is_active:
        raise HTTPException(401, "Account ist noch nicht aktiviert. Bitte E-Mail Verifizierung durchführen.")

    token = str(uuid.uuid4())
    expires = datetime.now(UTC) + timedelta(days=30)
    db.add(models.Session(token=token, user_id=user.id, expires_at=expires))
    db.commit()
    return {"success": True, "token": token, "name": user.name}


# --- User routes ---

@app.get("/user", response_model=schemas.UserOut)
def get_user_profile(user: models.User = Depends(get_current_user)):
    return user


@app.put("/user", response_model=schemas.UserOut)
def update_user_profile(user_data: schemas.UserUpdate, db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    # 1. Frisch aus dieser Session laden
    user_in_db = db.query(models.User).filter(models.User.id == current_user.id).first()

    if not user_in_db:
        raise HTTPException(404, "Benutzer nicht gefunden!")

    # 2. Prüfungen (Name doppelt?)
    if user_data.name:
        existing = db.query(models.User).filter(models.User.name == user_data.name).first()
        if existing and existing.id != user_in_db.id:
            raise HTTPException(400, "Name bereits vergeben!")
        user_in_db.name = user_data.name

    if user_data.email:
        existing = db.query(models.User).filter(models.User.email == user_data.email).first()
        if existing and existing.id != user_in_db.id:
            raise HTTPException(400, "Email bereits vergeben!")
        user_in_db.email = user_data.email

    if user_data.password:
        user_in_db.password_hash = get_password_hash(user_data.password)

    db.commit()
    db.refresh(user_in_db)
    return user_in_db


@app.delete("/user")
def delete_user_account(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    user_to_delete = db.query(models.User).filter(models.User.id == current_user.id).first()

    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()

    return {"status": "deleted", "id": current_user.id}


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
        user: models.User = Depends(get_current_user)):

    cat = db.query(models.Category).filter(models.Category.id == category_id,
                                           models.Category.user_id == user.id).first()

    if not cat: raise HTTPException(404, "Category not found")

    if cat.is_system_default:
        raise HTTPException(status_code=400,
                            detail="Standard-Kategorien können nicht bearbeitet werden, da sie für die Auswertung benötigt werden.")

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

    if cat.is_system_default:
        raise HTTPException(status_code=400,
                            detail="Standard-Kategorien können nicht gelöscht werden, da sie für die Auswertung benötigt werden.")

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

# --- Static files (frontend) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
static_files_path = os.path.join(script_dir, "../static")

app.mount("/", StaticFiles(directory=static_files_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
