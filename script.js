// ==========================================
// Konfiguration & Globale Variablen
// ==========================================
// Hinweis: main.py läuft standardmäßig auf Port 8000
const API_BASE = "http://127.0.0.1:8000"; 

let authToken = sessionStorage.getItem('lifeos_token');
let currentUser = sessionStorage.getItem('lifeos_user');
let categories = [];
let entries = [];
let currentCategory = null;
let editingEntryId = null;   // Speichert die ID des Eintrags, den wir gerade bearbeiten
let editingEntryDate = null; // Speichert das ursprüngliche Datum

// ==========================================
// Initialisierung
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    if (authToken && currentUser) {
        showAppScreen();
        loadData();
    } else {
        showLoginScreen();
    }
});

function showLoginScreen() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-screen').classList.add('hidden');
}

function showAppScreen() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    document.getElementById('display-username').innerText = "Angemeldet als: " + currentUser;
}

// Zentrale Fetch-Funktion
async function apiFetch(endpoint, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['Content-Type'] = 'application/json';

    if (authToken) {
        options.headers['Authorization'] = 'Bearer ' + authToken;
    }

    try {
        const response = await fetch(API_BASE + endpoint, options);

        if (response.status === 401) {
            logout();
            return null;
        }
        return response;
    } catch (err) {
        console.error("Netzwerkfehler:", err);
        alert("Server nicht erreichbar. Läuft main.py?");
        return null;
    }
}

// ==========================================
// Auth: Login & Register
// ==========================================
let isRegisterMode = false;

function toggleAuthMode() {
    isRegisterMode = !isRegisterMode;
    document.getElementById('auth-error').classList.add('hidden');
    document.getElementById('auth-success').classList.add('hidden');

    if (isRegisterMode) {
        document.getElementById('auth-title').innerText = "Konto erstellen";
        document.getElementById('email-container').classList.remove('hidden');
        document.getElementById('btn-login').classList.add('hidden');
        document.getElementById('btn-register').classList.remove('hidden');
        document.getElementById('txt-toggle').innerText = "Bereits ein Konto?";
        document.getElementById('link-toggle').innerText = "Anmelden";
    } else {
        document.getElementById('auth-title').innerText = "Willkommen zurück";
        document.getElementById('email-container').classList.add('hidden');
        document.getElementById('btn-login').classList.remove('hidden');
        document.getElementById('btn-register').classList.add('hidden');
        document.getElementById('txt-toggle').innerText = "Noch kein Konto?";
        document.getElementById('link-toggle').innerText = "Jetzt registrieren";
    }
}

async function handleLogin() {
    const name = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const errorEl = document.getElementById('auth-error');

    if (!name || !pass) return;

    // Backend erwartet schemas.UserLogin: { name, password }
    const res = await fetch(API_BASE + '/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, password: pass })
    });

    const data = await res.json();

    if (res.ok && data.success) {
        authToken = data.token;
        currentUser = data.name;
        sessionStorage.setItem('lifeos_token', authToken);
        sessionStorage.setItem('lifeos_user', currentUser);
        showAppScreen();
        loadData();
    } else {
        errorEl.innerText = data.detail || "Login fehlgeschlagen.";
        errorEl.classList.remove('hidden');
    }
}

async function handleRegister() {
    const name = document.getElementById('username').value;
    const mail = document.getElementById('email').value;
    const pass = document.getElementById('password').value;
    const errorEl = document.getElementById('auth-error');
    const successEl = document.getElementById('auth-success');

    if (!name || !mail || !pass) {
        errorEl.innerText = "Bitte alle Felder ausfüllen.";
        errorEl.classList.remove('hidden');
        return;
    }

    // Backend erwartet schemas.UserRegister
    const res = await fetch(API_BASE + '/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, email: mail, password: pass })
    });

    const data = await res.json();

    if (res.ok && data.success) {
        successEl.innerText = "Registrierung erfolgreich! Bitte einloggen.";
        successEl.classList.remove('hidden');
        setTimeout(() => toggleAuthMode(), 1500);
    } else {
        errorEl.innerText = data.detail || "Fehler beim Registrieren.";
        errorEl.classList.remove('hidden');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    sessionStorage.clear();
    showLoginScreen();
}

// ==========================================
// Daten Laden
// ==========================================
async function loadData() {
    // 1. ID sichern & Debugging
    // Wir wandeln die ID in einen String um, um Typ-Probleme zu vermeiden
    const savedId = currentCategory ? String(currentCategory.id) : null;
    console.log("🔄 loadData: Versuche ID wiederherzustellen:", savedId);

    if (!authToken) return;

    // 2. Daten neu laden
    const catRes = await apiFetch('/categories/');
    if (catRes && catRes.ok) {
        categories = await catRes.json();
    }

    const entRes = await apiFetch('/entries/');
    if (entRes && entRes.ok) {
        entries = await entRes.json();
    }
     
    renderSidebar();

    // 3. Ansicht wiederherstellen
    let foundCategory = null;

    if (savedId) {
        // Robuster Vergleich: Beides als String vergleichen
        foundCategory = categories.find(c => String(c.id) === savedId);
    }

    if (foundCategory) {
        console.log("✅ Kategorie wiedergefunden:", foundCategory.name);
        openCategory(foundCategory);
    } else if (categories.length > 0) {
        console.log("⚠️ Kategorie nicht gefunden, lade Erste:", categories[0].name);
        openCategory(categories[0]);
    }
}

function renderSidebar() {
    const nav = document.getElementById('nav-container');
    nav.innerHTML = ''; 

    categories.forEach(cat => {
        const btn = document.createElement('a');
        btn.href = '#';
        btn.className = 'nav-item';
        btn.id = 'nav-cat-' + cat.id;
        
        // Icon basierend auf Name
        let icon = '';
        const n = cat.name.toLowerCase();
        if(n.includes('fit') || n.includes('sport')) icon = '🏃';
        if(n.includes('essen') || n.includes('ernährung')) icon = '🍎';
        if(n.includes('tagebuch') || n.includes('gedanken')) icon = '📖';

        btn.innerText = `${icon} ${cat.name}`;
        btn.onclick = () => openCategory(cat);
        nav.appendChild(btn);
    });
}

// ==========================================
// Hauptansicht: Kategorie & Einträge
// ==========================================
function openCategory(cat) {
    // RESET Edit Mode
    editingEntryId = null;
    editingEntryDate = null;
    const btn = document.getElementById('btn-save-entry');
    if(btn) btn.innerText = "Speichern";

    currentCategory = cat;
    switchTab('generic');
    
    document.getElementById('gen-title').innerText = cat.name;
    
    // Inputs bauen
    const container = document.getElementById('gen-inputs-container');
    container.innerHTML = '';
    document.getElementById('entry-note').value = ''; // Notiz leeren

    // Nutrition Widget prüfen
    const widgetContainer = document.getElementById('special-widget-container');
    widgetContainer.innerHTML = '';
    if(cat.name.toLowerCase().includes('ernährung')) {
        renderNutritionWidget(widgetContainer);
    }

    // Felder rendern
    if(cat.fields && cat.fields.length > 0) {
        cat.fields.forEach(field => {
            const wrapper = document.createElement('div');
            wrapper.style.marginBottom = '15px';
            
            const label = document.createElement('label');
            label.innerText = field.unit ? `${field.label} (${field.unit})` : field.label;
            label.style.display = 'block';
            label.style.fontWeight = 'bold';
            
            const input = document.createElement('input');
            input.type = field.data_type === 'number' ? 'number' : 'text';
            input.className = 'gen-input'; 
            input.dataset.label = field.label; // Wichtig für Mapping
            input.placeholder = field.label;
            
            wrapper.appendChild(label);
            wrapper.appendChild(input);
            container.appendChild(wrapper);
        });
    } else {
        container.innerHTML = '<p style="color:#888;">Keine Felder definiert.</p>';
    }

    renderEntryList();

    // Sidebar Active State
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeBtn = document.getElementById('nav-cat-' + cat.id);
    if(activeBtn) activeBtn.classList.add('active');
}

async function saveEntry() {
    if (!currentCategory) return;

    const inputs = document.querySelectorAll('.gen-input');
    const values = {};
    let hasContent = false;

    // Werte auslesen
    inputs.forEach(input => {
        if (input.value.trim() !== '') {
            values[input.dataset.label] = input.value;
            hasContent = true;
        }
    });

    if (!hasContent) {
        alert("Bitte mindestens ein Feld ausfüllen.");
        return;
    }

    // Payload bauen
    const payload = {
        category_id: currentCategory.id,
        // Wenn wir bearbeiten, nimm das alte Datum, sonst JETZT
        occurred_at: editingEntryId ? editingEntryDate : new Date().toISOString(),
        note: document.getElementById('entry-note').value,
        values: values
    };

    let res;
    
    if (editingEntryId) {
        // --- UPDATE (PUT) ---
        res = await apiFetch('/entries/' + editingEntryId, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    } else {
        // --- CREATE (POST) ---
        res = await apiFetch('/entries/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    if (res && res.ok) {
        // Reset Inputs & Mode
        inputs.forEach(i => i.value = '');
        document.getElementById('entry-note').value = '';
        
        // Modus zurücksetzen
        editingEntryId = null;
        editingEntryDate = null;
        document.getElementById('btn-save-entry').innerText = "Speichern";

        await loadData(); // Tabelle neu laden
    } else {
        alert("Fehler beim Speichern.");
    }
}

function startEditEntry(id) {
    // Eintrag in der lokalen Liste finden
    const entry = entries.find(e => e.id === id);
    if (!entry) return;

    // Globale Variablen setzen
    editingEntryId = entry.id;
    editingEntryDate = entry.occurred_at; // Datum beibehalten!

    // Button Text ändern
    document.getElementById('btn-save-entry').innerText = "Ändern ✅";

    // Notiz füllen
    document.getElementById('entry-note').value = entry.note || '';

    // Felder füllen
    const inputs = document.querySelectorAll('.gen-input');
    inputs.forEach(input => {
        const label = input.dataset.label;
        // Wenn der Eintrag Daten für dieses Label hat, einfügen
        if (entry.data && entry.data[label] !== undefined) {
            input.value = entry.data[label];
        } else {
            input.value = '';
        }
    });
    
    // Nach oben scrollen, damit der User sieht, wo er editiert
    document.getElementById('gen-inputs-container').scrollIntoView({behavior: 'smooth'});
}

function renderEntryList() {
    const tbody = document.getElementById('list-generic');
    
    // 1. Limit aus dem Dropdown holen
    const limitInput = document.getElementById('entry-limit');
    // Fallback auf 10, falls Element noch nicht geladen (Sicherheitshalber)
    const limit = limitInput ? parseInt(limitInput.value) : 10;

    // 2. Filtern: Nur Einträge dieser Kategorie
    const catEntries = entries.filter(e => e.category_id === currentCategory.id);

    // 3. Begrenzen der Anzeige (slice von 0 bis limit)
    const displayedEntries = catEntries.slice(0, limit);

    tbody.innerHTML = displayedEntries.map(e => {
        // e.data enthält die Werte { "Gewicht": "80", ... }
        let detailsHtml = '';
        if (e.data) {
            for (const [key, val] of Object.entries(e.data)) {
                detailsHtml += `<span style="white-space: nowrap; margin-right:8px; padding:2px 6px; background:#e2e8f0; border-radius:4px; font-size:0.85rem;">
                    <b>${key}:</b> ${val}
                </span> `;
            }
        }

        const date = new Date(e.occurred_at);
        const timeStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        return `
        <tr>
            <td>${detailsHtml}</td>
            <td style="font-style:italic; color:#666;">${e.note || '-'}</td>
            <td style="font-size:0.8rem;">${timeStr}</td>
            <td>
                <button onclick="startEditEntry(${e.id})" class="btn-small btn-blue" style="margin:0; margin-bottom:5px;">✏️</button>
                <button onclick="deleteEntry(${e.id})" class="btn-small btn-red" style="margin:0;">🗑️</button>
            </td>
        </tr>
    `;
    }).join('');
}

async function deleteEntry(id) {
    if(!confirm("Eintrag wirklich löschen?")) return;
    
    const res = await apiFetch('/entries/' + id, { method: 'DELETE' });
    if(res && res.ok) {
        await loadData();
    }
}

// ==========================================
// Kategorie Erstellen
// ==========================================
function initCreateCategoryView() {
    document.getElementById('new-cat-name').value = '';
    document.getElementById('new-cat-desc').value = '';
    document.getElementById('field-list-container').innerHTML = '';
    addFieldRow(); 
}

function addFieldRow() {
    const container = document.getElementById('field-list-container');
    const div = document.createElement('div');
    div.className = 'field-row';
    div.style.cssText = "display:flex; gap:10px; margin-bottom:10px;";
    
    div.innerHTML = `
        <input type="text" class="f-label" placeholder="Feldname (z.B. Gewicht)" style="flex:2;">
        <select class="f-type" style="flex:1; padding:10px; border:1px solid #ddd; border-radius:6px;">
            <option value="number">Zahl</option>
            <option value="text">Text</option>
        </select>
        <input type="text" class="f-unit" placeholder="Einheit (z.B. kg)" style="flex:1;">
        <button onclick="this.parentElement.remove()" style="background:#ef4444; color:white; border:none; border-radius:4px; cursor:pointer; width:40px;">X</button>
    `;
    container.appendChild(div);
}

async function createCategory() {
    const name = document.getElementById('new-cat-name').value;
    const desc = document.getElementById('new-cat-desc').value;

    if (!name) return alert("Name ist Pflicht.");

    const fields = [];
    document.querySelectorAll('.field-row').forEach(row => {
        const label = row.querySelector('.f-label').value.trim();
        const type = row.querySelector('.f-type').value;
        const unit = row.querySelector('.f-unit').value.trim();

        if (label) {
            fields.push({ label, data_type: type, unit });
        }
    });

    if (fields.length === 0) return alert("Mindestens ein Feld definieren.");

    // Backend: CategoryCreate Schema
    const payload = {
        name: name,
        description: desc,
        fields: fields
    };

    const res = await apiFetch('/categories/', {
        method: 'POST',
        body: JSON.stringify(payload)
    });

    if (res && res.ok) {
        await loadData();
        // Zurück zur letzten (neuen) Kategorie springen
        if (categories.length > 0) {
            openCategory(categories[categories.length - 1]);
        }
    } else {
        alert("Fehler beim Erstellen der Kategorie.");
    }
}

async function editCurrentCategory() {
    if(!currentCategory) return;

    // Aktuelle Werte als Vorschlag anzeigen
    const newName = prompt("Neuer Name für die Kategorie:", currentCategory.name);
    if (newName === null) return; // Abbrechen gedrückt

    const newDesc = prompt("Neue Beschreibung:", currentCategory.description);
    if (newDesc === null) return; 

    // Payload für Backend (CategoryUpdate Schema)
    const payload = {
        name: newName,
        description: newDesc
    };

    const res = await apiFetch('/categories/' + currentCategory.id, {
        method: 'PUT',
        body: JSON.stringify(payload)
    });

    if (res && res.ok) {
        alert("Kategorie aktualisiert!");
        await loadData(); // Alles neu laden (Sidebar & Titel aktualisieren sich dann)
    } else {
        alert("Fehler beim Aktualisieren.");
    }
}

// ==========================================
// Reporting & Charts
// ==========================================
let myChart;

function renderReporting() {
    const ctx = document.getElementById('chart-balance');
    if(!ctx) return;
    
    // Daten aggregieren: Anzahl Einträge pro Kategorie
    const counts = {};
    const catNames = {};

    // Map ID -> Name
    categories.forEach(c => catNames[c.id] = c.name);

    entries.forEach(e => {
        const name = catNames[e.category_id] || "Unbekannt";
        counts[name] = (counts[name] || 0) + 1;
    });

    if(myChart) myChart.destroy();
    
    myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                label: 'Anzahl Einträge',
                data: Object.values(counts),
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true, ticks: { stepSize: 1 } }
            }
        }
    });
}

// ==========================================
// Navigation & Extras
// ==========================================
function switchTab(tabId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
    const target = document.getElementById('view-' + tabId);
    if (target) target.classList.remove('hidden');

    // Sidebar Reset
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    if (tabId === 'create-category') {
        initCreateCategoryView();
        currentCategory = null;
    } else if (tabId === 'reporting') {
        renderReporting();
        document.getElementById('nav-reporting').classList.add('active');
        currentCategory = null;
    }
}

// OpenFoodFacts Widget (bleibt gleich, hilft beim Ausfüllen)
function renderNutritionWidget(container) {
    container.innerHTML = `
        <div style="background:#f0fdf4; padding:15px; border-radius:8px; border:1px solid #bbf7d0; margin-bottom:20px;">
            <h4 style="margin-top:0; color:#166534;">🔍 Produktsuche (OpenFoodFacts)</h4>
            <div style="display:flex; gap:10px;">
                <input id="api-search-input" type="text" placeholder="z.B. Apfel, Cola..." style="flex:1; margin:0;">
                <button onclick="runApiSearch()" class="btn-green" style="width:auto; margin:0;">Suchen</button>
            </div>
            <p id="api-msg" style="margin:5px 0 0 0; font-size:0.85rem; color:#666;"></p>
        </div>
    `;
}

async function runApiSearch() {
    const q = document.getElementById('api-search-input').value;
    const msg = document.getElementById('api-msg');
    if(!q) return;
    msg.innerText = "Suche...";
    
    try {
        const res = await fetch(`https://world.openfoodfacts.org/cgi/search.pl?search_terms=${encodeURIComponent(q)}&search_simple=1&action=process&json=1&page_size=1`);
        const data = await res.json();

        if(data.products && data.products.length > 0) {
            const p = data.products[0];
            msg.innerText = `Gefunden: ${p.product_name}`;
            
            // Auto-Fill
            const inputs = document.querySelectorAll('.gen-input');
            inputs.forEach(input => {
                const lbl = input.dataset.label.toLowerCase();
                if(lbl.includes('kalorien') || lbl.includes('kcal')) {
                    const k = p.nutriments['energy-kcal_100g'] || p.nutriments['energy-kcal'];
                    if(k) input.value = k;
                }
                if(lbl.includes('produkt') || lbl.includes('name') || lbl.includes('essen')) {
                    input.value = p.product_name;
                }
            });
        } else {
            msg.innerText = "Nichts gefunden.";
        }
    } catch(e) {
        console.error(e);
        msg.innerText = "Fehler bei der API-Suche.";
    }
}