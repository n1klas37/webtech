import os.path
import sys
from datetime import datetime, timedelta, UTC

from app.database import SessionLocal
from app.models import User

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def cleanup_unverified_users():
    db = SessionLocal()

    try:
        limit_time = datetime.now(UTC) - timedelta(minutes=15)

        zombies = db.query(User).filter(
            User.is_active == False,
            User.created_at < limit_time
        ). all()

        if zombies:
            print(f"{len(zombies)} inaktive Benutzer werden gelöscht\n")
            for z in zombies:
                db.delete(z)
            db.commit()
            print("Alle inaktiven Benutzer wurden gelöscht!")
        else:
            print("Keine inaktiven Nutzer vorhanden")

    except Exception as e:
        print(f"Fehler {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_unverified_users()