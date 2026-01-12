from fastapi.testclient import TestClient
from main import app # Wir importieren deine FastAPI-Instanz aus der main.py

# Wir erstellen einen 'client', der wie ein Browser Anfragen schicken kann
client = TestClient(app)

# --- POSITIVER TEST ---
def test_read_docs():
    """Prüft, ob die API-Dokumentation (Swagger) geladen werden kann."""
    # 1. Simulator schickt eine GET-Anfrage an /docs
    response = client.get("/docs")
    
    # 2. Status 200 bedeutet: Seite wurde gefunden und erfolgreich geladen
    assert response.status_code == 200

# --- NEGATIVER TEST ---
def test_route_not_found():
    """Prüft, ob die API korrekt reagiert, wenn eine URL nicht existiert."""
    # 1. Wir rufen eine Fantasie-URL auf
    response = client.get("/nicht-existierende-seite")
    
    # 2. Status 404 bedeutet: 'Not Found'. 
    # Das ist hier das gewünschte Ergebnis (Negativ-Check).
    assert response.status_code == 404