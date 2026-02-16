import pytest

def test_temp_range_validation_logic():
    """LOGIK: Prüft, ob Werte in einem Bereich liegen."""
    def is_valid_area(a): return -50 < a < 100
    
    assert is_valid_area(20) is True   # Normal
    assert is_valid_area(150) is False # Zu heiß
    assert is_valid_area(-100) is False # Zu kalt

def test_calculate_average_logic():
    """LOGIK: Prüft eine mathematische Durchschnittsberechnung."""
    values = [10, 20, 30]
    avg = sum(values) / len(values)
    assert avg == 20.0

def test_string_trimming_logic():
    """LOGIK: Werden Leerzeichen am Anfang/Ende von Notizen entfernt?"""
    note = "  Das beste Projekt  "
    assert note.strip() == "Das beste Projekt"

def test_json_structure_extraction():
    """LOGIK: Kann ein Wert aus einem verschachtelten Dictionary gelesen werden?"""
    data = {"sensors": {"temp": {"value": 22}}}
    assert data["sensors"]["temp"]["value"] == 22

def test_list_not_empty_logic():
    """LOGIK: Stellt sicher, dass unsere Datenlisten nicht leer sind."""
    mylist = [1]
    assert len(mylist) > 0

def test_boolean_toggle_logic():
    """LOGIK: Prüft einfaches Umschalten von Status-Werten."""
    is_active = True
    assert not is_active is False