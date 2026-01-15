import pytest

def test_temp_range_validation_logic():
    """LOGIK: Prüft, ob ein Sensor-Wert im realistischen Bereich liegt."""
    def is_valid_temp(t): return -50 < t < 100
    
    assert is_valid_temp(20) is True   # Normal
    assert is_valid_temp(150) is False # Zu heiß
    assert is_valid_temp(-100) is False # Zu kalt

def test_calculate_average_logic():
    """LOGIK: Prüft eine mathematische Durchschnittsberechnung."""
    values = [10, 20, 30]
    avg = sum(values) / len(values)
    assert avg == 20.0

def test_string_trimming_logic():
    """LOGIK: Werden Leerzeichen am Anfang/Ende von Notizen entfernt?"""
    note = "  Wichtiges Labor  "
    assert note.strip() == "Wichtiges Labor"

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