// auth.js

const LOGIN_KEY = 'lifetracker_is_logged_in';

// Funktionen zur Steuerung der UI (Global definiert, um von index.html aus erreichbar zu sein)
// Diese Funktionen rufen nun die globalen Funktionen der Haupt-App (z.B. loadData, switchTab) auf.

function showLoginScreen() {
    document.getElementById('login-screen').classList.remove('initial-hidden', 'hidden');
    // Versteckt die Haupt-App, falls sie aus Versehen sichtbar ist
    const mainApp = document.getElementById('main-app');
    if (mainApp) mainApp.classList.add('hidden');
}

function showMainApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('main-app').classList.remove('initial-hidden', 'hidden');
    
    // Stellt sicher, dass die Haupt-App korrekt initialisiert wird
    if (typeof loadData === 'function') loadData(); // Lade Daten (aus index.html)
    if (typeof switchTab === 'function') switchTab('fitness'); // Zeige ersten Tab (aus index.html)
}

function handleLogin() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorEl = document.getElementById('login-error');

    // HIER: Harte Kodierung für die Demo
    const VALID_USERNAME = 'test';
    const VALID_PASSWORD = '1234';

    if (username === VALID_USERNAME && password === VALID_PASSWORD) {
        localStorage.setItem(LOGIN_KEY, 'true');
        errorEl.classList.add('hidden');
        showMainApp();
    } else {
        errorEl.innerText = "Benutzername oder Passwort falsch. (Benutzer: test, Passwort: 1234)";
        errorEl.classList.remove('hidden');
    }
}

function logout() {
    if (confirm("Möchtest du dich wirklich abmelden?")) {
        localStorage.removeItem(LOGIN_KEY);
        // Zusätzlich alle App-Daten löschen, falls gewünscht (optional)
        // localStorage.removeItem(STORAGE_KEY); 
        showLoginScreen();
    }
}

// Initialer Check beim Laden der Seite
document.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = localStorage.getItem(LOGIN_KEY) === 'true';
    
    // Die App-Elemente sind initial per CSS (.initial-hidden) versteckt, 
    // um ein Aufblitzen zu verhindern. Hier machen wir den ersten Check.
    if (isLoggedIn) {
        showMainApp();
    } else {
        showLoginScreen();
    }
});