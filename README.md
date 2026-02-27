# Lifetracker: Webbasierte Tracking-Anwendung

Repository zur Seminararbeit **Konzeption und Entwicklung einer Webanwendung zur flexiblen Erfassung von Gesund-heits- und Lifestyledaten**.

## Projektbeschreibung

Die Anwendung ist eine Single Page Application (SPA) mit zustandslosem REST-Backend zur Erfassung und Auswertung persönlicher Kennzahlen. Das System nutzt ein hybrides Datenbankmodell (Kombination aus relationalen Strukturen und schemalosen JSON-Feldern), um eine maximale Flexibilität bei der Erstellung benutzerdefinierter Tracking-Kategorien zu gewährleisten, ohne Schema-Migrationen durchführen zu müssen.

## Kernfunktionen

* **Sichere Authentifizierung:** Zustandslose JWT-Authentifizierung (Bearer Token) und Passwort-Hashing mittels Argon2.
* **Double-Opt-In Verifizierung:** Asynchroner E-Mail-Versand (via `fastapi-mail`) zur Validierung neuer Benutzerkonten.
* **Dynamische Datenstrukturen:** Erstellung individueller Tracking-Kategorien durch das Frontend; Persistierung über eine generische JSON-Spalte im Backend.
* **Externe API-Integration:** Anbindung der *OpenFoodFacts*-API zur clientseitigen Berechnung von Nährwerten.
* **Clientseitige Visualisierung:** Datenaggregation und grafische Aufbereitung im Browser mittels `Chart.js` zur Entlastung des Servers.

## Technologie-Stack

* **Backend:** Python, FastAPI
* **Datenbank-ORM & Validierung:** SQLAlchemy, Pydantic
* **Datenbank:** SQLite (Entwicklung) / PostgreSQL (Produktion)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API)
* **Sicherheit & Kryptografie:** passlib (Argon2)

## Funktionen und Benutzeroberfläche

### 1. Dynamische Kategorieverwaltung

Der Lifetracker beschränkt sich nicht auf vordefinierte Metriken, sondern erlaubt die vollständige Individualisierung des Trackings.

* **Individuelle Kategorien:** Benutzer können eigene Lebensbereiche (z. B. „Gitarre spielen“, „Finanzen“ oder „Lesen“) als neue Kategorie anlegen.
* **Flexible Eingabefelder:** Pro Kategorie lassen sich beliebig viele maßgeschneiderte Datenfelder definieren.
* **Datentypen und Einheiten:** Die Felder können als Text- oder Zahlenfelder konfiguriert und mit spezifischen Einheiten (z. B. Minuten, Euro, Seiten) versehen werden.

![Kategorie erstellen](/docs/assets/kategorie-erstellen.png)

### 2. Smarte Datenerfassung (Beispiel: Ernährung)

Die Erfassung von Transaktionsdaten wird durch Automatisierung und die Anbindung externer Datenbanken vereinfacht.

* **OpenFoodFacts-Integration:** In der Kategorie Ernährung ist eine Live-Produktsuche implementiert.
* **Automatische Nährwertberechnung:** Nach Auswahl eines Lebensmittels und Eingabe der verzehrten Menge (in Gramm) ermittelt das System die Nährwerte (kcal/100g) über die Schnittstelle und berechnet den absoluten Energiegehalt vollautomatisch.
* **Zeitersparnis:** Manuelle Recherchen von Nährwerttabellen und eigene mathematische Berechnungen durch den Nutzer entfallen.

![Eintrag erstellen](/docs/assets/eintrag-erstellen-essen.png)

### 3. Interaktive Auswertungen

Die gesammelten Datenpunkte werden aufbereitet, um den Fortschritt und mögliche Korrelationen visuell nachvollziehen zu können.

* **Grafische Aufbereitung:** Darstellung der Tracking-Historie in Form von interaktiven Diagrammen.
* **Übergreifende Metriken:** Die Auswertungen umfassen sowohl Aktivitäts-Level (absolute Anzahl der Einträge pro Kategorie) als auch spezifische Detail-Metriken (z. B. durchschnittliche Schlafdauer der letzten 5 Tage oder tagesaktuelle Kalorienbilanz).
* **Dynamische Anpassung:** Die Visualisierungen basieren in Echtzeit auf den individuellen Einträgen des eingeloggten Nutzers.

![Auswertungen](/docs/assets/auswertungen.png)

## Installation und lokale Entwicklung

#### Systemvoraussetzungen

* Python 3.10 oder höher
* Git

**1. Repository klonen**

```bash
git clone [Github-Repo]
cd webtech

```

**2. Virtuelle Umgebung erstellen und aktivieren**

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

```

**3. Abhängigkeiten installieren**

```bash
pip install -r requirements.txt

```

**4. Umgebungsvariablen konfigurieren**
Erstellen einer Datei mit dem Namen `.env` im Hauptverzeichnis. Folgende Parameter müssen definiert werden:

| Variable | Beschreibung | Beispielwert |
| --- | --- | --- |
| `EMAIL_VERIFICATION_ENABLED` | Steuert den Double-Opt-In-Zwang | `True` oder `False` |
| `MAIL_USERNAME` | SMTP-Benutzername für den Mailversand | `beispiel@gmail.com` |
| `MAIL_PASSWORD` | App-Passwort des SMTP-Servers | `xxxx xxxx xxxx xxxx` |

**5. Applikation starten**
Der Start des lokalen Entwicklungsservers erfolgt über Uvicorn. Die Datenbanktabellen werden beim Start automatisch generiert.

```bash
cd app
uvicorn main:app --reload

```

Die Anwendung ist unter `http://127.0.0.1:8000` erreichbar. Die interaktive API-Dokumentation (Swagger-UI) befindet sich unter `http://127.0.0.1:8000/docs`.

## Projektstruktur

* **`app/`**: Serverseitige Logik (Routen, ORM-Modelle, Validierungsschemata, Kryptografie).
* **`static/`**: Clientseitige Ressourcen der SPA (HTML, CSS, JavaScript).
* **`scripts/`**: Systemskripte zur Datenbankbereinigung (`cleanup.py`) und Testdatengenerierung.
* **`tests/`**: Unit- und Integrationstests (Ausführung via `pytest`).