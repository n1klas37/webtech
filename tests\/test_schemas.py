import pytest
from schemas import EntryCreate
from pydantic import ValidationError
from datetime import datetime

# --- POSITIVER TEST ---
def test_entry_schema_valid():
    """
    Dieser Test prüft den 'Happy Path' (Erfolgsfall).
    Wir simulieren hier eine korrekte Eingabe, wie sie von einem Sensor
    oder einem Frontend kommen würde.
    """
    
    # 1. Wir erstellen ein Dictionary mit gültigen Testdaten.
    # Wichtig: Wir nutzen 'note', da der vorherige Test gezeigt hat, 
    # dass dein Modell dieses Feld statt 'title' erwartet.
    valid_data = {
        "category_id": 1,           # Die ID der Kategorie (Muss vorhanden sein)
        "occurred_at": datetime.now(), # Der Zeitpunkt der Messung (Muss vorhanden sein)
        "values": {"temp": 22.5},   # Die eigentlichen Messwerte (Muss vorhanden sein)
        "note": "Test-Messung"      # Eine zusätzliche Notiz (Optional)
    }
    
    # 2. Wir übergeben die Daten an das Pydantic-Schema (EntryCreate).
    # Das '**' entpackt das Dictionary in einzelne Argumente.
    entry = EntryCreate(**valid_data)
    
    # 3. Wir stellen sicher, dass die Daten korrekt im Objekt gespeichert wurden.
    # Wenn diese Behauptungen (asserts) stimmen, ist der Test erfolgreich.
    assert entry.category_id == 1
    assert entry.note == "Test-Messung"

# --- NEGATIVER TEST ---
def test_entry_schema_missing_fields():
    """
    Dieser Test prüft, ob unser 'Türsteher' (Pydantic) aufpasst.
    Wir provozieren absichtlich einen Fehler, um sicherzugehen, dass
    unvollständige Daten abgelehnt werden.
    """
    
    # 1. Wir sagen pytest: 'Achtung, die nächste Zeile MUSS einen Fehler werfen'.
    # Ein ValidationError tritt auf, wenn Pflichtfelder im Schema fehlen.
    with pytest.raises(ValidationError):
        
        # 2. Wir versuchen, einen Eintrag NUR mit einer Notiz zu erstellen.
        # Da 'category_id', 'occurred_at' und 'values' fehlen, muss
        # Pydantic hier den Dienst verweigern.
        EntryCreate(note="Hier fehlen fast alle wichtigen Daten")