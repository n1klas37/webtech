import random
from datetime import datetime, timedelta
from database import SessionLocal
import models

# --- Konfiguration ---
USER_NAME = "testuser"  # Hier deinen Benutzernamen eintragen
DAYS_BACK = 30          # Zeitraum in Tagen
ENTRIES_PER_CAT = 15    # Wie viele Einträge pro Kategorie?

# DB Session starten
db = SessionLocal()

def run():
    # 1. User finden
    user = db.query(models.User).filter(models.User.name == USER_NAME).first()
    if not user:
        print(f"Fehler: User '{USER_NAME}' nicht gefunden.")
        return

    print(f"Fülle Daten für User: {user.name} ({user.email})")

    # 2. Kategorien des Users laden
    categories = db.query(models.Category).filter(models.Category.user_id == user.id).all()
    if not categories:
        print("Keine Kategorien gefunden. Logge dich erst einmal ein, um die Standards zu erstellen.")
        return

    # 3. Zufallsdaten generieren
    for cat in categories:
        print(f"  -> Generiere {ENTRIES_PER_CAT} Einträge für '{cat.name}'...")
        
        for _ in range(ENTRIES_PER_CAT):
            entry_values = {}
            
            # Felder dynamisch befüllen
            for field in cat.fields:
                val = generate_smart_value(field.label, field.data_type)
                entry_values[field.label] = val

            # Eintrag speichern
            entry = models.Entry(
                user_id=user.id,
                category_id=cat.id,
                occurred_at=random_date(),
                note="Testdaten",
                data=entry_values
            )
            db.add(entry)
    
    db.commit()
    print("✅ Fertig! Datenbank wurde befüllt.")

def random_date():
    """Zufälliges Datum + Uhrzeit in den letzten X Tagen"""
    delta = timedelta(
        days=random.randint(0, DAYS_BACK),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59)
    )
    return datetime.now() - delta

def generate_smart_value(label, dtype):
    """Erzeugt passende Werte basierend auf dem Feldnamen"""
    l = label.lower()
    
    if dtype == 'text':
        if "übung" in l: return random.choice(["Bankdrücken", "Kniebeugen", "Laufen", "Kreuzheben", "Yoga"])
        if "essen" in l or "lebensmittel" in l: return random.choice(["Apfel", "Reis mit Huhn", "Proteinshake", "Pizza", "Salat"])
        if "highlight" in l: return random.choice(["Sonne genossen", "Gut geschlafen", "Sport gemacht", "Projekt beendet"])
        return "Test"

    if dtype == 'number':
        if "dauer" in l: return random.randint(20, 90)     # Minuten
        if "strecke" in l: return random.randint(3, 15)    # km
        if "gewicht" in l:
            # Unterscheidung Essen (g) vs Hantel (kg) anhand Kontext raten
            return random.randint(10, 100) if "übung" not in l else random.randint(40, 120) 
        if "energie" in l or "kcal" in l: return random.randint(150, 800)
        if "laune" in l or "erholung" in l: return random.randint(1, 10)
        return random.randint(1, 100)

    return ""

if __name__ == "__main__":
    run()
    db.close()