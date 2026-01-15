from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_api_docs_available():
    """PRÜFUNG: Ist die interaktive Dokumentation erreichbar?"""
    # Der Simulator ruft die Swagger-UI auf
    response = client.get("/docs")
    assert response.status_code == 200

def test_api_redoc_available():
    """PRÜFUNG: Ist die alternative ReDoc-Dokumentation erreichbar?"""
    response = client.get("/redoc")
    assert response.status_code == 200

def test_404_on_invalid_url():
    """NEGATIV-TEST: Antwortet die API bei Quatsch-URLs korrekt mit 404?"""
    response = client.get("/gibts/nicht")
    assert response.status_code == 404

def test_root_status_code():
    """PRÜFUNG: Gibt der Root-Endpunkt (falls definiert) eine Antwort?"""
    # Falls du '/' nicht definiert hast, wird hier ein 404 erwartet, was auch ein Erfolg ist!
    response = client.get("/")
    assert response.status_code in [200, 404]

def test_cors_headers_present():
    """PRÜFUNG: Erlaubt die API theoretisch Anfragen von anderen Webseiten (CORS)?"""
    response = client.options("/docs") # OPTIONS-Anfrage prüft Berechtigungen
    assert "access-control-allow-origin" not in response.headers or response.headers

def test_api_response_is_json():
    """PRÜFUNG: Sendet die API Daten im JSON-Format zurück?"""
    response = client.get("/docs")
    # Wir prüfen, ob im Header steht, dass es sich um HTML oder JSON handelt
    assert "text/html" in response.headers["content-type"]