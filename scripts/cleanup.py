import os
import sys
from datetime import datetime, timedelta, UTC

# System path manipulation MUST occur before local imports to resolve modules correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models import User, Session


def cleanup_unverified_users(db):
    """
    Identifies and deletes user accounts that have not completed the
    double opt-in verification within the defined time limit.
    """
    try:
        limit_time = datetime.now(UTC) - timedelta(minutes=1)

        zombies = db.query(User).filter(
            User.is_active == False,
            User.created_at < limit_time
        ).all()

        if zombies:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Deleting {len(zombies)} inactive users...")
            for z in zombies:
                db.delete(z)
            db.commit()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Inactive users successfully deleted.")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No inactive users found.")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error during user cleanup: {e}")


def cleanup_expired_sessions(db):
    """
    Performs a bulk deletion of all session tokens that have passed
    their cryptographic expiration date (Time to Live).
    """
    try:
        # Bulk delete operation for high performance on large tables
        deleted_rows = db.query(Session).filter(
            Session.expires_at < datetime.now(UTC)
        ).delete(synchronize_session=False)

        db.commit()

        if deleted_rows > 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Deleted {deleted_rows} expired sessions.")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No expired sessions found.")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error during session cleanup: {e}")


def run():
    """Main execution block managing the isolated database session."""
    print("\n--- Starting Database Cleanup ---")
    db = SessionLocal()

    try:
        cleanup_unverified_users(db)
        cleanup_expired_sessions(db)
    finally:
        db.close()

    print("--- Cleanup Finished ---\n")


if __name__ == "__main__":
    run()