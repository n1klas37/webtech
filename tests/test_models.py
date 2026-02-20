import pytest
from app.models import User, Entry

def test_user_model_email_storage():
    """PRÜFUNG: Speichert das User-Modell die E-Mail korrekt?"""
    u = User(email="test@web.de")
    assert u.email == "test@web.de"

def test_user_model_name_assignment():
    """PRÜFUNG: Können wir dem User einen Namen zuweisen? (Falls Feld existiert)"""
    try:
        u = User(name="niklas")
        assert u.name == "niklas"
    except TypeError:
        pytest.skip("Feld 'name' nicht im Modell vorhanden")

def test_entry_model_note_storage():
    """PRÜFUNG: Speichert das Entry-Datenmodell eine Notiz?"""
    e = Entry(note="Test-Notiz")
    assert e.note == "Test-Notiz"

def test_entry_model_foreign_key_logic():
    """PRÜFUNG: Kann ein Eintrag einer Kategorie-ID zugeordnet werden?"""
    e = Entry(category_id=5)
    assert e.category_id == 5

def test_model_id_is_none_before_db():
    """PRÜFUNG: Ein neues Objekt darf noch keine ID haben, bevor es in der DB ist."""
    u = User(email="new@test.de")
    assert u.id is None

def test_user_model_password_field():
    """PRÜFUNG: Hat das User-Modell ein Feld für den Passwort-Hash?"""
    u = User(password_hash="geheim_hash")
    assert u.password_hash == "geheim_hash"