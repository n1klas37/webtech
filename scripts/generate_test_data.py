import random
from datetime import datetime, timedelta
from app.database import SessionLocal
from app import models

# --- CONFIGURATION ---
TARGET_USERNAME = "Testuser"
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 3, 31)
SKIP_PROBABILITY = 0.3  # 30% chance to skip tracking for non-essential categories

db = SessionLocal()


def get_user(username):
    """Retrieves the user object from the database."""
    return db.query(models.User).filter(models.User.name == username).first()


def create_timestamp(target_date):
    """Generates a random time for a specific date within the defined range."""
    # Random time between 07:00 and 23:00
    hour = random.randint(7, 23)
    minute = random.randint(0, 59)
    return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


# --- LOGIC GENERATORS ---

def generate_fitness_data(available_labels):
    """
    Generates coherent fitness data.
    E.g.: Jogging includes distance, bench press includes weight.
    """
    activities = [
        {"name": "Joggen", "type": "cardio", "kcal_per_min": 10, "speed_kmh": 10},
        {"name": "Radfahren", "type": "cardio", "kcal_per_min": 8, "speed_kmh": 20},
        {"name": "Bankdrücken", "type": "kraft", "kcal_per_min": 5},
        {"name": "Kniebeugen", "type": "kraft", "kcal_per_min": 6},
        {"name": "Yoga", "type": "flex", "kcal_per_min": 3},
    ]

    act = random.choice(activities)
    duration = random.choice([20, 30, 45, 60, 90])  # Minutes

    # Calculate base data
    data = {}

    # Exercise
    data["Übung"] = act["name"]

    # Duration
    data["Dauer"] = duration

    # Energy (Calculation: duration * factor)
    kcal = duration * act["kcal_per_min"]
    # Add some variance (+/- 10%)
    kcal = int(kcal * random.uniform(0.9, 1.1))
    data["Energie"] = kcal

    # Distance (Logical only for cardio)
    if act["type"] == "cardio":
        # Distance = Time(h) * km/h
        dist = (duration / 60) * act["speed_kmh"]
        data["Strecke"] = round(dist, 2)
    else:
        data["Strecke"] = 0  # or None, depending on preference

    # Weight (Logical only for strength training)
    if act["type"] == "kraft":
        data["Gewicht"] = random.choice([40, 50, 60, 80, 100])
    else:
        data["Gewicht"] = 0

    # Map the calculated data to the ACTUAL fields of the category
    result_values = {}
    for label in available_labels:
        # Find the most appropriate piece of data for the label
        for key, val in data.items():
            if key.lower() in label.lower():
                result_values[label] = val
                break
        # Fallback for unrecognized fields
        if label not in result_values:
            result_values[label] = "-"

    return result_values


def generate_nutrition_data(available_labels):
    """Generates coherent nutrition data (calories match the amount)."""
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
    amount = random.choice([100, 150, 200, 300, 500])  # Grams

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
    """Generates sleep data (recovery slightly correlates with duration)."""
    duration = random.randint(5, 10)  # Hours

    # Logic: Longer sleep usually implies better recovery
    recovery = duration + random.randint(-2, 1)
    # Clamp value between 1 and 10
    recovery = max(1, min(10, recovery))

    result_values = {}
    for label in available_labels:
        l = label.lower()
        if "dauer" in l:
            result_values[label] = duration
        elif "erholung" in l or "qual" in l:  # Quality
            result_values[label] = recovery
        else:
            result_values[label] = 0
    return result_values


def generate_diary_data(available_labels):
    """Generates diary data with randomized moods and highlights."""
    highlights = ["Sport gemacht", "Projekt beendet", "Gut gegessen", "Freunde getroffen", "Film geschaut",
                  "Code geschrieben"]

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


# --- MAIN PROGRAM ---

def run():
    print(f"--- Starting Smart Data Generator for User: {TARGET_USERNAME} ---")

    user = get_user(TARGET_USERNAME)
    if not user:
        print(f"User '{TARGET_USERNAME}' not found. Please register/login first.")
        return

    categories = db.query(models.Category).filter(models.Category.user_id == user.id).all()
    if not categories:
        print("No categories found.")
        return

    total_entries = 0

    # Calculate the total number of days between start and end date
    delta = END_DATE - START_DATE

    # Iterate over all categories
    for cat in categories:
        cat_name_lower = cat.name.lower()
        field_labels = [f.label for f in cat.fields]

        print(f"Processing category: {cat.name}...")

        # Determine if the current category MUST be tracked every day
        is_essential = "ernährung" in cat_name_lower or "essen" in cat_name_lower or "schlaf" in cat_name_lower

        # Iterate through the specific date range
        for day_offset in range(delta.days + 1):
            current_date = START_DATE + timedelta(days=day_offset)

            # Apply random skip logic for non-essential categories
            if not is_essential:
                if random.random() < SKIP_PROBABILITY:
                    continue

            # Decide how many entries to create for this category today
            count = 1
            if "ernährung" in cat_name_lower:
                count = random.randint(1, 4)  # People eat multiple times a day

            for _ in range(count):
                ts = create_timestamp(current_date)
                values = {}
                note = ""

                # --- Choose strategy based on category name ---
                if "fitness" in cat_name_lower or "sport" in cat_name_lower:
                    values = generate_fitness_data(field_labels)
                    note = "Training"
                elif "ernährung" in cat_name_lower or "essen" in cat_name_lower:
                    values = generate_nutrition_data(field_labels)
                elif "schlaf" in cat_name_lower:
                    values = generate_sleep_data(field_labels)
                    # Sleep usually occurs only once per day
                    if _ > 0: continue
                elif "tagebuch" in cat_name_lower:
                    values = generate_diary_data(field_labels)
                    if _ > 0: continue
                else:
                    # Fallback for unknown categories (simple random values)
                    for l in field_labels:
                        values[l] = "Test-" + str(random.randint(1, 100))

                # Save the entry
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
    print(f"Done! {total_entries} entries were created.")
    db.close()


if __name__ == "__main__":
    run()