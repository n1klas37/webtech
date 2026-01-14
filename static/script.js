// =================================
// Konfiguration and global variables
// =================================
// set API_BASE to "" for same origin as the frontend
const API_BASE = ""; 

let authToken = sessionStorage.getItem('lifeos_token');
let currentUser = sessionStorage.getItem('lifeos_user');
let categories = [];
let entries = [];
let currentCategory = null;
let editingEntryId = null;   // saves the entry_id being edited
let editingEntryDate = null; // saves the original date of the entry being edited

// ==========================================
// Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    if (authToken && currentUser) {
        showAppScreen();
        loadData();
    } else {
        showLoginScreen();
    }
});

// Show login or app screen
function showLoginScreen() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-screen').classList.add('hidden');
}

function showAppScreen() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('hidden');
    document.getElementById('display-username').innerText = "Angemeldet als: " + currentUser;
}

// Centralized API fetch function with auth handling
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

// Helper for local ISO string (without seconds)
function toLocalISOString(dateObj) {
    const pad = (n) => n < 10 ? '0' + n : n;
    return dateObj.getFullYear() + '-' +
        pad(dateObj.getMonth() + 1) + '-' +
        pad(dateObj.getDate()) + 'T' +
        pad(dateObj.getHours()) + ':' +
        pad(dateObj.getMinutes());
}

// ==========================================
// Auth: Login, Logout & Register
// ==========================================

let isRegisterMode = false;

function toggleAuthMode() {
    isRegisterMode = !isRegisterMode;
    document.getElementById('auth-error').classList.add('hidden');
    document.getElementById('auth-success').classList.add('hidden');

    const emailContainer = document.getElementById('email-container');
    const passConfirmContainer = document.getElementById('password-confirm-container');

    if (isRegisterMode) {
        document.getElementById('auth-title').innerText = "Konto erstellen";

        document.getElementById('email-container').classList.remove('hidden');
        passConfirmContainer.classList.remove('hidden');

        document.getElementById('btn-login').classList.add('hidden');
        document.getElementById('btn-register').classList.remove('hidden');
        document.getElementById('txt-toggle').innerText = "Bereits ein Konto?";
        document.getElementById('link-toggle').innerText = "Anmelden";
    } else {
        document.getElementById('auth-title').innerText = "Willkommen zurück";

        document.getElementById('email-container').classList.add('hidden');
        passConfirmContainer.classList.add('hidden');

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

    // Backend awaits schemas.UserLogin {name, password}
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
    const passConfirm = document.getElementById('password-confirm').value;
    const errorEl = document.getElementById('auth-error');
    const successEl = document.getElementById('auth-success');

    if (!name || !mail || !pass || !passConfirm) {
        errorEl.innerText = "Bitte alle Felder ausfüllen.";
        errorEl.classList.remove('hidden');
        return;
    }

    if (pass !== passConfirm) {
        errorEl.innerText = "Die Passwörter stimmen nicht überein!";
        errorEl.classList.remove('hidden');
        return;
    }

    // Backend awaits schemas.UserRegister {name, email, password}
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
        let msg = "Fehler beim Registrieren.";

        // Case 1: validationerror i.e. Array of errors from Pydantic
        if (Array.isArray(data.detail)) {
            // Take first error message
            msg = data.detail[0].msg; 
        } 
        // Case 2: single error message from main.py
        else if (data.detail) {
            msg = data.detail;
        }

        errorEl.innerText = "Fehler: " + msg;
        
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
// User Profile Load, Save & Delete
// ==========================================

async function loadUserProfile() {
    // Fetch user data from backend
    const res = await apiFetch('/user');
    if (res && res.ok) {
        const user = await res.json();
        
        // Fill in the form
        document.getElementById('settings-name').value = user.name;
        document.getElementById('settings-email').value = user.email;
        document.getElementById('settings-password').value = ''; // leave password empty for security reasons
    }
}

// Update user profile 
async function saveUserProfile() {
    const newName = document.getElementById('settings-name').value;
    const newEmail = document.getElementById('settings-email').value;
    const newPass = document.getElementById('settings-password').value;
    const newPassConfirm = document.getElementById('settings-password-confirm').value;

    if (!newName || !newEmail) {
        alert("Name und E-Mail dürfen nicht leer sein.");
        return;
    }

    if (newPass && newPass !== "") {
        if (newPass !== newPassConfirm) {
            alert("Die neuen Passwörter stimmen nicht überein.");
            return; // Abbruch
        }
    }

    // Build payload for user update schema
    const payload = {
        name: newName,
        email: newEmail
    };
    
    // Send password only if changed
    if (newPass && newPass.trim() !== "") {
        payload.password = newPass;
    }

    const res = await apiFetch('/user', {
        method: 'PUT',
        body: JSON.stringify(payload)
    });

    if (res && res.ok) {
        const updatedUser = await res.json();
        
        // Update currentUser if name changed
        currentUser = updatedUser.name;
        // Set session storage
        sessionStorage.setItem('lifeos_user', currentUser);
        //Update displayed username
        document.getElementById('display-username').innerText = "Angemeldet als: " + currentUser;
        
        alert("Profil erfolgreich aktualisiert!");
        document.getElementById('settings-password').value = '';
        document.getElementById('settings-password-confirm').value = '';
        
    } else {
        const err = await res.json();
        alert("Fehler: " + (err.detail || "Konnte Profil nicht speichern"));
    }
}

// DELETE user account
async function deleteUserAccount() {
    const confirmName = prompt(`WARNUNG: Dies löscht deinen Account und ALLE Daten endgültig!\n\nBitte tippe deinen Benutzernamen ("${currentUser}") zur Bestätigung:`);

    if (confirmName !== currentUser) {
        alert("Abbruch: Name stimmte nicht überein.");
        return;
    }

    const res = await apiFetch('/user', {
        method: 'DELETE'
    });

    if (res && res.ok) {
        alert("Account gelöscht. Auf Wiedersehen!");
        logout();
    } else {
        alert("Fehler beim Löschen des Accounts.");
    }
}

// ==================================================
// Load Data: Categories & Entries and render Sidebar
// ==================================================
async function loadData() {
    // Save current category ID to restore view later
    const savedId = currentCategory ? String(currentCategory.id) : null;
    console.log("Debug: savedID in loadData:", savedId);

    if (!authToken) return;

    // Get categories and entries from database
    const catRes = await apiFetch('/categories/');
    if (catRes && catRes.ok) {
        categories = await catRes.json();
    }

    const entRes = await apiFetch('/entries/');
    if (entRes && entRes.ok) {
        entries = await entRes.json();
    }
     
    renderSidebar();

    // Try to reopen the previously opened category
    let foundCategory = null;

    if (savedId) {
        // Try to find category by saved ID
        foundCategory = categories.find(c => String(c.id) === savedId);
    }

    if (foundCategory) {
        openCategory(foundCategory);
    } else {
        // Fallback: open homepage if no category found
        switchTab('homepage');
    }
}

// Render sidebar with categories of current user
function renderSidebar() {
    const nav = document.getElementById('nav-container');
    nav.innerHTML = ''; 

    categories.forEach(cat => {
        const btn = document.createElement('a');
        btn.href = '#';
        btn.className = 'nav-item';
        btn.id = 'nav-cat-' + cat.id;

        btn.innerText = `${cat.name}`;
        btn.onclick = () => openCategory(cat);
        nav.appendChild(btn);
    });
}

// Open a category view
function openCategory(cat) {
    // RESET Edit Mode
    editingEntryId = null;
    editingEntryDate = null;
    const btn = document.getElementById('btn-save-entry');
    if(btn) btn.innerText = "Speichern";

    document.getElementById('entry-ts').value = toLocalISOString(new Date());

    currentCategory = cat;
    switchTab('generic');
    
    document.getElementById('gen-title').innerText = cat.name;
    document.getElementById('gen-desc').innerText = cat.description;
    
    // Render input fields
    const container = document.getElementById('gen-inputs-container');
    container.innerHTML = '';
    document.getElementById('entry-note').value = ''; // Reset note field

    // Show OpenFoodFacts API widget for "ernährung" category
    const widgetContainer = document.getElementById('special-widget-container');
    widgetContainer.innerHTML = '';
    if(cat.name.toLowerCase().includes('ernährung')) {
        renderNutritionWidget(widgetContainer);
    }

    // Dynamically create input fields based on category definition
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
            input.dataset.label = field.label;
            input.placeholder = field.label;
            
            wrapper.appendChild(label);
            wrapper.appendChild(input);
            container.appendChild(wrapper);
        });
    } else {
        container.innerHTML = '<p style="color:#888;">Keine Felder definiert.</p>';
    }

    renderEntryList();

    // Show active category in sidebar as active
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeBtn = document.getElementById('nav-cat-' + cat.id);
    if(activeBtn) activeBtn.classList.add('active');
}

async function saveEntry() {
    if (!currentCategory) return;

    const inputs = document.querySelectorAll('.gen-input');
    const values = {};
    let hasContent = false;

    // Input validation for correct data type
    for (const input of inputs) {
        const label = input.dataset.label;
        
        // input.validity.badInput is true if there is a type mismatch (e.g., non-number in number field)
        if (input.validity && input.validity.badInput) {
            alert(`Fehler im Feld "${label}": Der eingegebene Wert ist keine gültige Zahl!`);
            input.focus(); // set focus to the invalid input
            return; // abort saving
        }

        const val = input.value.trim();

        // Only include non-empty values
        if (val !== '') {
            values[label] = val;
            hasContent = true;
        }
    }

    if (!hasContent) {
        alert("Bitte mindestens ein Feld ausfüllen.");
        return;
    };

    // Leave timestamp as it is if editing, else set to now
    const tsInput = document.getElementById('entry-ts').value;
    let finalDate = tsInput;
    if (!finalDate) {
        finalDate = toLocalISOString(new Date());
    };

    // Build payload for backend
    const payload = {
        category_id: currentCategory.id,
        occurred_at: finalDate,
        note: document.getElementById('entry-note').value,
        values: values
    };

    let res;
    
    // Differentiate between CREATE and UPDATE
    if (editingEntryId) {
        // UPDATE (PUT)
        res = await apiFetch('/entries/' + editingEntryId, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    } else {
        // CREATE (POST)
        res = await apiFetch('/entries/', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    if (res && res.ok) {
        // Reset Inputs & Mode if saved successfully
        inputs.forEach(i => i.value = '');
        document.getElementById('entry-note').value = '';

        // Set timestamp to now for new entries
        document.getElementById('entry-ts').value = toLocalISOString(new Date());
        
        // Reset edit mode
        editingEntryId = null;
        editingEntryDate = null;
        document.getElementById('btn-save-entry').innerText = "Speichern";

        await loadData(); // Reload data to see changes
    } else {
        alert("Fehler beim Speichern.");
    }
}

function startEditEntry(id) {
    // Search for the entry by ID in the local entries array
    const entry = entries.find(e => e.id === id);
    if (!entry) return;

    // Set global editingEntryId
    editingEntryId = entry.id;

    // Change button text to show edit mode
    document.getElementById('btn-save-entry').innerText = "Ändern ✅";

    // Load note
    document.getElementById('entry-note').value = entry.note || '';

    // Set timestamp as the entry's occurred_at
    if (entry.occurred_at) {
        const dateObj = new Date(entry.occurred_at);
        document.getElementById('entry-ts').value = toLocalISOString(dateObj);
    }

    // Fill in input fields with existing data
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
    
    // Scroll to inputs
    document.getElementById('gen-inputs-container').scrollIntoView({behavior: 'smooth'});
}

// Render the list of entries for the current category
function renderEntryList() {
    const tbody = document.getElementById('list-generic');
    
    // Read limit from input dropdown
    const limitInput = document.getElementById('entry-limit');
    // Fallback to 10 if not found
    const limit = limitInput ? parseInt(limitInput.value) : 10;

    // Only show entries of the current category
    const catEntries = entries.filter(e => e.category_id === currentCategory.id);

    // Sort by occurred_at descending and slice at limit
    const displayedEntries = catEntries.slice(0, limit);

    tbody.innerHTML = displayedEntries.map(e => {
        // e.data is an object with key-value pairs
        let detailsHtml = '';
        if (e.data) {
            for (const [key, val] of Object.entries(e.data)) {
                // Search for field definition in current category to get unit
                const fieldDef = currentCategory.fields.find(f => f.label === key);
                // If fieldDef has unit, append it, if not, leave empty
                const unit = (fieldDef && fieldDef.unit) ? ` ${fieldDef.unit}` : '';

                detailsHtml += `<span style="white-space: nowrap; margin-right:8px; padding:2px 6px; background:#e2e8f0; border-radius:8px; font-size:0.85rem;">
                    <b>${key}:</b> ${val}${unit}
                </span> `;
            }
        }

        // Format occurred_at date to local time
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


// DELETE an entry by ID
async function deleteEntry(id) {
    if(!confirm("Eintrag wirklich löschen?")) return;
    
    const res = await apiFetch('/entries/' + id, { method: 'DELETE' });
    if(res && res.ok) {
        await loadData();
    }
}

// ==========================================
// Category Creation, Editing & Deletion
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
    
    // Align items horizontally for a better layout
    div.style.cssText = "display:flex; gap:10px; margin-bottom:10px; align-items:stretch;";
    const fieldStyle = "padding:10px; border:1px solid #ddd; border-radius:8px; box-sizing:border-box; height:42px;"; 

    // Inner HTML for the field row
    div.innerHTML = `
        <input type="text" class="f-label" placeholder="Feldname (z.B. Einnahmen)" 
            style="flex:2; ${fieldStyle}">
        
        <select class="f-type" style="flex:1; ${fieldStyle} background-color:white;">
            <option value="number">Zahl</option>
            <option value="text">Text</option>
        </select>
        
        <input type="text" class="f-unit" placeholder="Einheit (z.B. €)" 
            style="flex:1; ${fieldStyle}">
        
        <button onclick="this.closest('.field-row').remove()" 
                style="background:#ef4444; color:white; border:none; border-radius:8px; cursor:pointer; width:40px; padding:0; display:flex; justify-content:center; align-items:center; height:42px;">
            X
        </button>
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

    // Payload for backend (CategoryCreate Schema)
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
        // Open the newly created category (last in the list)
        if (categories.length > 0) {
            openCategory(categories[categories.length - 1]);
        }
    } else {
        alert("Fehler beim Erstellen der Kategorie.");
    }
}

async function editCurrentCategory() {
    if(!currentCategory) return;

    // Prompt for new name and description with current values as default
    const newName = prompt("Neuer Name für die Kategorie:", currentCategory.name);
    if (newName === null) return; // Abbrechen gedrückt

    const newDesc = prompt("Neue Beschreibung:", currentCategory.description);
    if (newDesc === null) return; 

    // Payload for backend (CategoryUpdate Schema)
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
        await loadData(); // Reload data to see changes
    } else {
        alert("Fehler beim Aktualisieren.");
    }
}

// DELETE current category
async function deleteCurrentCategory() {
    if (!currentCategory) return;

    const confirmMsg = `Möchtest du die Kategorie "${currentCategory.name}" und ALLE zugehörigen Einträge wirklich unwiderruflich löschen?`;
    
    if (!confirm(confirmMsg)) return;

    // API call to delete category
    const res = await apiFetch('/categories/' + currentCategory.id, {
        method: 'DELETE'
    });

    if (res && res.ok) {
        // Reset currentCategory
        currentCategory = null; 
        alert("Kategorie gelöscht.");
        await loadData(); 
    } else {
        alert("Fehler beim Löschen der Kategorie.");
    }
    loadData();
}

// Reporting and Charts
let myChart;
let sleepChart;
let kcalChart;

function renderReporting() {
    
    renderEntryCountChart();
    renderKcalChart();
    renderSleepChart();
}

// Chart 1: Sleeping hours past 5 days ---
function renderSleepChart() {
    const ctx = document.getElementById('chart-sleep');
    if (!ctx) return;

    // Find category "schlaf"
    const sleepCat = categories.find(c => c.name.toLowerCase().includes('schlaf'));
    
    const labels = [];
    const dataPoints = [];
    const today = new Date();

    // go through last 5 days
    for (let i = 4; i >= 0; i--) {
        const d = new Date();
        d.setDate(today.getDate() - i);
        const dateStr = d.toISOString().split('T')[0]; 
        
        // set label
        const label = d.toLocaleDateString('de-DE', { weekday: 'short', day: '2-digit', month: '2-digit' });
        labels.push(label);

        // sum up sleeping hours for that day
        let hours = 0;
        if (sleepCat) {
            const daysEntries = entries.filter(e => 
                e.category_id === sleepCat.id && 
                e.occurred_at.startsWith(dateStr)
            );
            
            daysEntries.forEach(e => {
                for (const [key, val] of Object.entries(e.data || {})) {
                    if (key.toLowerCase().includes('dauer')) {
                        hours += parseFloat(val) || 0;
                    }
                }
            });
        }
        dataPoints.push(hours);
    }

    // Calculate average sleep hours over the past 5 days
    const totalHours = dataPoints.reduce((a, b) => a + b, 0);
    const avgHours = (totalHours / 5).toFixed(1);

    if (sleepChart) sleepChart.destroy();

    sleepChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Stunden',
                data: dataPoints,
                backgroundColor: '#a855f7',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, suggestedMax: 8 } },
            plugins: {
                title: {
                    display: true,
                    text: `Schlaf (Letzte 5 Tage) - Ø ${avgHours} Std.`,
                    font: { size: 16 }
                },
                legend: { display: false } // Legend can be omitted
            }
        }
    });
}


// Chart 2: Calorie balance today ---
function renderKcalChart() {
    const ctx = document.getElementById('chart-kcal');
    if (!ctx) return;

    // Find cat "ernährung" and "fitness"
    const foodCat = categories.find(c => c.name.toLowerCase().includes('ernährung') || c.name.toLowerCase().includes('essen'));
    const fitCat = categories.find(c => c.name.toLowerCase().includes('fitness') || c.name.toLowerCase().includes('sport'));

    // Set today's date string
    const todayStr = new Date().toISOString().split('T')[0];

    // Sum up kcal for a given category today
    const sumKcal = (cat) => {
        if (!cat) return 0;
        let sum = 0;
        const relevantEntries = entries.filter(e => 
            e.category_id === cat.id && 
            e.occurred_at.startsWith(todayStr)
        );
        relevantEntries.forEach(e => {
            for (const [key, val] of Object.entries(e.data || {})) {
                const k = key.toLowerCase();
                if (k.includes('energie') || k.includes('kcal') || k.includes('kalorien')) {
                    sum += parseFloat(val) || 0;
                }
            }
        });
        return sum;
    };

    const kcalIn = sumKcal(foodCat);
    const kcalOut = sumKcal(fitCat);

    // calculate balance
    const balance = kcalIn - kcalOut;
    // format balance with + or - sign
    const sign = balance > 0 ? '+' : ''; 
    const balanceText = `${sign}${balance}`;

    if (kcalChart) kcalChart.destroy();

    kcalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Eingenommen', 'Verbrannt'],
            datasets: [{
                data: [kcalIn, kcalOut],
                backgroundColor: ['#22c55e', '#3b82f6'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            scales: { x: { beginAtZero: true } },
            plugins: {
                title: {
                    display: true,
                    text: `Kalorien Heute (Bilanz: ${balanceText} kcal)`,
                    font: { size: 16 }
                },
                legend: { display: false } // Legend can be omitted
            }
        }
    });
}

// Chart 3: Count of entries per category
function renderEntryCountChart() {
const ctx = document.getElementById('chart-balance');
    if(!ctx) return;
    
    // Calculate counts per category
    const counts = {};
    const catNames = {};

    // Map category IDs to names
    categories.forEach(c => catNames[c.id] = c.name);

    // Count entries per category
    entries.forEach(e => {
        const name = catNames[e.category_id] || "Unbekannt";
        counts[name] = (counts[name] || 0) + 1;
    });

    if(countChart) countChart.destroy();

    countChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                label: 'Anzahl Einträge',
                data: Object.values(counts),
                backgroundColor: '#3b82f6',
                borderRadius: 8
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
// Navigation and extras
// ==========================================
function switchTab(tabId) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
    const target = document.getElementById('view-' + tabId);
    if (target) target.classList.remove('hidden');

    // Sidebar Reset
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    if (tabId === 'settings'){
        loadUserProfile();
        currentCategory = null;

    }else if (tabId === 'create-category') {
        initCreateCategoryView();
        currentCategory = null;

    } else if (tabId === 'reporting') {
        renderReporting();
        document.getElementById('nav-reporting').classList.add('active');
        currentCategory = null;

    } else if (tabId === 'homepage') {
        const btn = document.getElementById('nav-homepage');
        if(btn) btn.classList.add('active');
        currentCategory = null;

        //Show username on homepage
        const nameElement = document.getElementById('home-user-name');
        if (nameElement && currentUser) {
            nameElement.innerText = currentUser;
        }
    }
}

// Show nutrition widget for food category
function renderNutritionWidget(container) {
    container.innerHTML = `
        <div style="background:#f0fdf4; padding:15px; border-radius:8px; border:1px solid #bbf7d0; margin-bottom:20px;">
            <h4 style="margin-top:0; color:#166534;">Produktsuche (OpenFoodFacts)</h4>
            <div style="display:flex; gap:10px;">
                <input id="api-search-input" type="text" placeholder="z.B. Vollmilch, Salami..." style="flex:1; margin:0;">
                <button onclick="runApiSearch()" class="btn-green" style="width:auto; margin:0;">Suchen</button>
            </div>
            <p id="api-msg" style="margin:5px 0 0 0; font-size:0.85rem; color:#666;">Hinweis: Die API ist nicht zuverlässig. Etwas rumprobieren ist empfehlenswert ;)</p>
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
            
            // Get kcal per 100g
            const kcal100 = p.nutriments['energy-kcal_100g'] || p.nutriments['energy-kcal'];
            
            let weightInput = null;
            let energyInput = null;

            // Find inputs
            const inputs = document.querySelectorAll('.gen-input');
            inputs.forEach(input => {
                const lbl = input.dataset.label.toLowerCase();
                
                // Product Name
                if(lbl.includes('lebensmittel')) {
                    input.value = p.product_name || "";
                }

                // Weight
                if(lbl.includes('gewicht')) {
                    weightInput = input;
                }

                // Energy / Calories
                if(lbl.includes('energie')) {
                    energyInput = input;
                }
            });

            // Set values and calculate based on weight
            if(energyInput && kcal100) {
                // Store kcal per 100g in dataset for later calculations
                energyInput.dataset.kcalPer100 = kcal100;

                if(weightInput) {
                    // Standard: 100g
                    weightInput.value = 100;
                    energyInput.value = kcal100; 

                    // Event-Listener: calculate kcal based on weight when changed
                    weightInput.oninput = function() {
                        const weight = parseFloat(this.value);
                        const baseKcal = parseFloat(energyInput.dataset.kcalPer100);
                        
                        if(!isNaN(weight) && !isNaN(baseKcal)) {
                            const result = (weight / 100) * baseKcal;
                            energyInput.value = Math.round(result);
                        }
                    };
                } else {
                    // If no weight input, just set kcal per 100g
                    energyInput.value = kcal100;
                }
            }
        // If no products were found
        } else {
            msg.innerText = "Nichts gefunden.";
        }
    } catch(e) {
        console.error(e);
        msg.innerText = "Fehler bei der API-Suche.";
    }
}