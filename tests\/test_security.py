import pytest
from pydantic import ValidationError
from schemas import UserUpdate as UserCreate 

# --- SICHERHEITS- UND VALIDIERUNGSTESTS ---

def test_password_validation_rules():
    """
    ERKLÄRUNG: Deine App hat strikte Passwort-Regeln.
    Dieser Test prüft, ob Passwörter ohne Großbuchstaben abgelehnt werden.
    """
    with pytest.raises(ValidationError) as exc:
        # 'geheim123' hat keinen Großbuchstaben -> Fehler erwartet
        UserCreate(password="geheim123")
    assert "Großbuchstaben" in str(exc.value)

@pytest.mark.parametrize("short_pw", ["Short1", "123", "Abc"])
def test_password_min_length_rejected(short_pw):
    """ERKLÄRUNG: Prüft, ob Passwörter unter 8 Zeichen abgelehnt werden."""
    with pytest.raises(ValidationError):
        UserCreate(password=short_pw)

def test_password_valid_format():
    """
    ERKLÄRUNG: Positiv-Test mit einem Passwort, das alle Regeln erfüllt:
    Mindestens 8 Zeichen UND ein Großbuchstabe.
    """
    user = UserCreate(password="SicheresPasswort123")
    assert len(user.password) >= 8

def test_security_name_storage():
    """
    ERKLÄRUNG: Prüft das Namensfeld. 
    Hinweis: In deiner 'UserUpdate' Klasse heißt das Feld 'name' statt 'username'.
    """
    u = UserCreate(name="Niklas", password="SicheresPasswort123")
    assert u.name == "Niklas"

def test_name_max_length_logic():
    """ERKLÄRUNG: Testet die Aufnahme eines langen Namens."""
    long_name = "A" * 50
    user = UserCreate(name=long_name, password="SicheresPasswort123")
    assert user.name == long_name

def test_email_optional_in_update():
    """
    ERKLÄRUNG: In Update-Schemas ist die E-Mail oft optional.
    Dieser Test bestätigt, dass das Schema auch ohne E-Mail gültig ist.
    """
    user = UserCreate(password="SicheresPasswort123")
    assert user.email is None or user.email == ""