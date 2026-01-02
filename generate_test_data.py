import json
import random
import datetime

FILENAME = "test_data.json"
NUM_ENTRIES = 50

def random_date():
    start = datetime.datetime.now() - datetime.timedelta(days=60)
    dt = start + datetime.timedelta(days=random.randint(0, 60), seconds=random.randint(0, 86000))
    return dt.isoformat()

data = [
    {
        "name": "Kraftsport",
        "description": "Gym",
        "fields": [
            {"label": "Uebung", "data_type": "text"},
            {"label": "Gewicht", "data_type": "number", "unit": "kg"},
            {"label": "Gefuehl", "data_type": "number", "unit": "1-10"}
        ],
        "entries": [
            {
                "occurred_at": random_date(),
                "note": "Training",
                "values": {
                    "Uebung": random.choice(["Bankdruecken", "Kniebeugen"]),
                    "Gewicht": random.randint(60, 100),
                    "Gefuehl": random.randint(1, 10)
                }
            } for _ in range(NUM_ENTRIES)
        ]
    },
    {
        "name": "Ernaehrung",
        "description": "Tracking",
        "fields": [
            {"label": "Essen", "data_type": "text"},
            {"label": "Kalorien", "data_type": "number", "unit": "kcal"}
        ],
        "entries": [
            {
                "occurred_at": random_date(),
                "note": "Mahlzeit",
                "values": {
                    "Essen": random.choice(["Apfel", "Pizza", "Salat"]),
                    "Kalorien": random.randint(50, 800)
                }
            } for _ in range(NUM_ENTRIES)
        ]
    }
]

with open(FILENAME, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print(f"Datei {FILENAME} erstellt.")