from models import User # Importiert deine User-Tabelle aus models.py

def test_new_user_model():
    """Prüft, ob das User-Modell im Speicher korrekt angelegt werden kann."""
    # 1. Wir erstellen eine Test-Instanz des Users
    # Wir nutzen nur 'email', da wir wissen, dass dieses Feld existiert
    user = User(email="niklas@test.de")
    
    # 2. Wir prüfen, ob SQLAlchemy den Wert im Objekt gespeichert hat
    assert user.email == "niklas@test.de"

def test_user_model_invalid_field():
    """Negativ-Test: Was passiert bei einem Feld, das es nicht gibt?"""
    import pytest
    # 1. SQLAlchemy wirft einen TypeError, wenn man ein unbekanntes Feld nutzt
    with pytest.raises(TypeError):
        # 2. Wir versuchen 'falsches_feld' zu füllen, das in models.py nicht existiert
        User(falsches_feld="Gibt es nicht")