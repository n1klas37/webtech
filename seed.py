import json
import os
from datetime import datetime
from database import SessionLocal, engine, Base
import models
from passlib.context import CryptContext

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
db = SessionLocal()


def seed():
    print("Starte Seeding...")

    db.query(models.Entry).delete()
    db.query(models.CategoryField).delete()
    db.query(models.Category).delete()
    db.query(models.Session).delete()
    db.query(models.User).delete()
    db.commit()

    print("Erstelle User: testuser / Test1234!")
    # ACHTUNG: Passwort muss jetzt stark sein!
    user = models.User(
        name="testuser",
        email="test@test.de",
        password_hash=pwd_context.hash("Test1234!")
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if not os.path.exists("test_data.json"):
        print("Keine test_data.json gefunden.")
        return

    with open("test_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for cat_data in data:
        print(f"Kategorie: {cat_data['name']}")

        cat = models.Category(
            user_id=user.id,
            name=cat_data['name'],
            description=cat_data['description']
        )
        db.add(cat)
        db.commit()

        for f_def in cat_data['fields']:
            field = models.CategoryField(
                category_id=cat.id,
                label=f_def['label'],
                data_type=f_def['data_type'],
                unit=f_def.get('unit')
            )
            db.add(field)
        db.commit()

        for e_data in cat_data['entries']:
            dt_obj = datetime.fromisoformat(e_data['occurred_at'])

            entry = models.Entry(
                user_id=user.id,
                category_id=cat.id,
                occurred_at=dt_obj,
                note=e_data.get('note', ''),
                data=e_data['values']
            )
            db.add(entry)

        db.commit()
        print(f"   {len(cat_data['entries'])} Eintraege importiert.")

    db.close()
    print("Fertig! Login mit: testuser / Test1234!")


if __name__ == "__main__":
    seed()