import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app import models

# --- KONFIGURATION ---
TARGET_USERNAME = "marc"  # <--- Hier deinen Usernamen eintragen
DAYS_TO_FILL = 300000             # Für wie viele Tage rückwirkend Daten erzeugen?
ENTRIES_PER_DAY = 20           # Ungefähre Anzahl Einträge pro Kategorie/Tag

db = SessionLocal()

def get_user(username):
    return db.query(models.User).filter(models.User.name == username).first()

def create_timestamp(day_offset):
    """Erzeugt eine zufällige Zeit an einem bestimmten Tag in der Vergangenheit"""
    base_date = datetime.now() - timedelta(days=day_offset)
    # Zufällige Uhrzeit zwischen 07:00 und 23:00
    hour = random.randint(7, 23)
    minute = random.randint(0, 59)
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

# --- LOGIK-GENERATOREN ---

def generate_fitness_data(available_labels):
    """
    Erzeugt in sich schlüssige Sport-Daten.
    Z.B.: Joggen hat Strecke, Bankdrücken hat Gewicht.
    """
    activities = [
        {"name": "Joggen", "type": "cardio", "kcal_per_min": 10, "speed_kmh": 10},
        {"name": "Radfahren", "type": "cardio", "kcal_per_min": 8, "speed_kmh": 20},
        {"name": "Bankdrücken", "type": "kraft", "kcal_per_min": 5},
        {"name": "Kniebeugen", "type": "kraft", "kcal_per_min": 6},
        {"name": "Yoga", "type": "flex", "kcal_per_min": 3},
    ]
    
    act = random.choice(activities)
    duration = random.choice([20, 30, 45, 60, 90]) # Minuten
    
    # Basis-Daten berechnen
    data = {}
    
    # 1. Übung
    data["Übung"] = act["name"]
    
    # 2. Dauer
    data["Dauer"] = duration
    
    # 3. Energie (Berechnung: Dauer * Faktor)
    kcal = duration * act["kcal_per_min"]
    # Bisschen Varianz reinbringen (+/- 10%)
    kcal = int(kcal * random.uniform(0.9, 1.1))
    data["Energie"] = kcal
    
    # 4. Strecke (Nur für Cardio logisch)
    if act["type"] == "cardio":
        # Strecke = Zeit(h) * km/h
        dist = (duration / 60) * act["speed_kmh"]
        data["Strecke"] = round(dist, 2)
    else:
        data["Strecke"] = 0 # oder None, je nach Wunsch
        
    # 5. Gewicht (Nur für Kraft logisch)
    if act["type"] == "kraft":
        data["Gewicht"] = random.choice([40, 50, 60, 80, 100])
    else:
        data["Gewicht"] = 0

    # Jetzt mappen wir die berechneten Daten auf die TATSÄCHLICHEN Felder der Kategorie
    result_values = {}
    for label in available_labels:
        # Wir suchen das passendste Stück Daten für das Label
        for key, val in data.items():
            if key.lower() in label.lower():
                result_values[label] = val
                break
        # Fallback für nicht erkannte Felder
        if label not in result_values:
            result_values[label] = "-"
            
    return result_values

def generate_nutrition_data(available_labels):
    """Erzeugt schlüssige Ernährungsdaten (Kalorien passen zur Menge)."""
    foods = [
        {"name": "Apfel", "kcal_100g": 52},
        {"name": "Banane", "kcal_100g": 89},
        {"name": "Hähnchenbrust", "kcal_100g": 165},
        {"name": "Reis (gekocht)", "kcal_100g": 130},
        {"name": "Pizza", "kcal_100g": 266},
        {"name": "Salat", "kcal_100g": 15},
        {"name": "Schokolade", "kcal_100g": 546},
    ]
    
    food = random.choice(foods)
    amount = random.choice([100, 150, 200, 300, 500]) # Gramm
    
    total_kcal = int((amount / 100) * food["kcal_100g"])
    
    result_values = {}
    for label in available_labels:
        l = label.lower()
        if "lebensmittel" in l or "essen" in l:
            result_values[label] = food["name"]
        elif "gewicht" in l or "menge" in l:
            result_values[label] = amount
        elif "energie" in l or "kcal" in l:
            result_values[label] = total_kcal
        else:
            result_values[label] = ""
            
    return result_values

def generate_sleep_data(available_labels):
    """Erzeugt Schlafdaten (Erholung korreliert leicht mit Dauer)."""
    duration = random.randint(5, 10) # Stunden
    
    # Logik: Wer länger schläft, ist meist erholter (einfache Logik)
    recovery = duration + random.randint(-2, 1)
    # Clamp value 1-10
    recovery = max(1, min(10, recovery))
    
    result_values = {}
    for label in available_labels:
        l = label.lower()
        if "dauer" in l:
            result_values[label] = duration
        elif "erholung" in l or "qual" in l: # Qualität
            result_values[label] = recovery
        else:
            result_values[label] = 0
    return result_values

def generate_diary_data(available_labels):
    highlights = ["Sport gemacht", "Projekt beendet", "Gut gegessen", "Freunde getroffen", "Film geschaut", "Code geschrieben"]
    
    result_values = {}
    for label in available_labels:
        l = label.lower()
        if "laune" in l or "stimmung" in l:
            result_values[label] = random.randint(3, 10)
        elif "highlight" in l or "notiz" in l:
            result_values[label] = random.choice(highlights)
        else:
            result_values[label] = "-"
    return result_values


# --- HAUPTPROGRAMM ---

def run():
    print(f"--- Starte Smart Data Generator für User: {TARGET_USERNAME} ---")
    
    user = get_user(TARGET_USERNAME)
    if not user:
        print(f"❌ User '{TARGET_USERNAME}' nicht gefunden. Bitte erst registrieren/einloggen.")
        return

    categories = db.query(models.Category).filter(models.Category.user_id == user.id).all()
    if not categories:
        print("❌ Keine Kategorien gefunden.")
        return

    total_entries = 0

    # Über alle Kategorien iterieren
    for cat in categories:
        cat_name_lower = cat.name.lower()
        field_labels = [f.label for f in cat.fields]
        
        print(f"Verarbeite Kategorie: {cat.name}...")
        
        # Für jeden Tag in der Vergangenheit
        for day in range(DAYS_TO_FILL):
            
            # Manchmal aussetzen (damit es realistischer wirkt)
            if random.random() < 0.3: 
                continue

            # Entscheiden, wie viele Einträge heute für diese Kategorie
            count = 1
            if "ernährung" in cat_name_lower: count = random.randint(1, 4) # Man isst öfter
            
            for _ in range(count):
                ts = create_timestamp(day)
                values = {}
                note = ""

                # --- Strategie wählen basierend auf Name ---
                if "fitness" in cat_name_lower or "sport" in cat_name_lower:
                    values = generate_fitness_data(field_labels)
                    note = "Training"
                elif "ernährung" in cat_name_lower or "essen" in cat_name_lower:
                    values = generate_nutrition_data(field_labels)
                elif "schlaf" in cat_name_lower:
                    values = generate_sleep_data(field_labels)
                    # Schlaf ist meist nur 1x pro Tag
                    if _ > 0: continue 
                elif "tagebuch" in cat_name_lower:
                    values = generate_diary_data(field_labels)
                    if _ > 0: continue
                else:
                    # Fallback für unbekannte Kategorien (einfache Zufallswerte)
                    for l in field_labels:
                        values[l] = "Test-" + str(random.randint(1,100))
                
                # Speichern
                entry = models.Entry(
                    user_id=user.id,
                    category_id=cat.id,
                    occurred_at=ts,
                    note=note,
                    data=values
                )
                db.add(entry)
                total_entries += 1
                
    db.commit()
    print(f"✅ Fertig! {total_entries} logische Einträge wurden erstellt.")
    db.close()

if __name__ == "__main__":
    run()