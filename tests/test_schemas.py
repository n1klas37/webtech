import pytest
from app.schemas import EntryCreate
from pydantic import ValidationError
from datetime import datetime

def test_entry_schema_full_valid():
    """POSITIV-TEST: Akzeptiert das Schema einen vollständigen Datensatz?"""
    data = {"category_id": 1, "occurred_at": datetime.now(), "values": {"t": 20}, "note": "Ok"}
    entry = EntryCreate(**data)
    assert entry.note == "Ok"

def test_entry_schema_missing_note():
    """POSITIV-TEST: Ist das Feld 'note' wirklich optional?"""
    data = {"category_id": 1, "occurred_at": datetime.now(), "values": {"t": 20}}
    entry = EntryCreate(**data)
    assert entry.note is None or entry.note == ""

def test_entry_schema_fails_without_values():
    """NEGATIV-TEST: Wird ein Eintrag ohne Messwerte (values) abgelehnt?"""
    with pytest.raises(ValidationError):
        EntryCreate(category_id=1, occurred_at=datetime.now())

def test_entry_schema_fails_with_wrong_id_type():
    """NEGATIV-TEST: Wird eine ID, die Text statt einer Zahl ist, abgelehnt?"""
    with pytest.raises(ValidationError):
        EntryCreate(category_id="Erste_Kategorie", occurred_at=datetime.now(), values={})

def test_entry_schema_fails_with_invalid_date():
    """NEGATIV-TEST: Wird ein ungültiges Datum abgelehnt?"""
    with pytest.raises(ValidationError):
        EntryCreate(category_id=1, occurred_at="gestern_mittag", values={})

def test_entry_schema_values_structure():
    """PRÜFUNG: Speichert das Schema die Dictionary-Werte korrekt?"""
    data = {"category_id": 1, "occurred_at": datetime.now(), "values": {"temp": 25.5, "hum": 60}}
    entry = EntryCreate(**data)
    assert entry.values["temp"] == 25.5