/**
 * ME_VENTS - Core Application Controller
 * High performance, swipe-gesture enabled PWA for Banquets & Operations
 * ME by Meliá Málaga
 */

// Estado Global
const state = {
  events: [],
  selectedDate: null,
  activeFilterSpace: 'all',
  activeFilterSetup: 'all',
  searchQuery: '',
  spacesConfig: [],
  jargonConfig: {}
};

// Diccionario y Salones en memoria para funcionamiento 100% Offline
const DEFAULT_SPACES = [
  { id: "estudio-1", name: "Estudio 1", color_tag: "#0080ff", max_capacities: { u_shape: 16, escuela: 24, teatro: 35, banquete: 20, coctel: 35, imperial: 14 } },
  { id: "estudio-2", name: "Estudio 2", color_tag: "#00b4d8", max_capacities: { u_shape: 14, escuela: 20, teatro: 30, banquete: 18, coctel: 30, imperial: 12 } },
  { id: "estudio-3", name: "Estudio 3", color_tag: "#48cae4", max_capacities: { u_shape: 18, escuela: 28, teatro: 40, banquete: 24, coctel: 40, imperial: 16 } },
  { id: "estudio-4", name: "Estudio 4", color_tag: "#90e0ef", max_capacities: { u_shape: 12, escuela: 16, teatro: 25, banquete: 16, coctel: 25, imperial: 10 } },
  { id: "estudio-5", name: "Estudio 5", color_tag: "#0077b6", max_capacities: { u_shape: 20, escuela: 32, teatro: 45, banquete: 30, coctel: 50, imperial: 18 } },
  { id: "foyer", name: "Foyer", color_tag: "#d4af37", max_capacities: { coctel: 100, banquete: 50 } },
  { id: "multifuncional", name: "Multifuncional", color_tag: "#7b2cbf", max_capacities: { u_shape: 36, escuela: 90, teatro: 140, banquete: 100, coctel: 150 } },
  { id: "canitas-al-fresco", name: "Cañitas al Fresco", color_tag: "#2ec4b6", max_capacities: { coctel: 90, banquete: 60 } },
  { id: "terraza-rooftop", name: "Terraza / Rooftop", color_tag: "#e76f51", max_capacities: { coctel: 140, banquete: 70 } }
];

// Eventos iniciales de demostración
const SEED_EVENTS = [
  {
    id: "evt-seed-1",
    title: "Junta Ejecutiva Telefónica Tech",
    date: "2026-09-12",
    time_start: "09:00",
    time_end: "13:30",
    space: { id: "estudio-1", name: "Estudio 1", color_tag: "#0080ff" },
    setup: { key: "u_shape", label: "Herradura / U-Shape", icon: "🧲" },
    pax: 12,
    services: [
      { type: "fb", key: "coffee_break", label: "Coffee Break", icon: "☕" },
      { type: "equipment", key: "audiovisuales", label: "Audiovisuales (AV)", icon: "🎥" }
    ],
    operational: {
      furniture: { mesas_rectangulares: 7, mesas_redondas: 0, mesas_altas: 0, sillas: 12 },
      times: { setup_minutes: 25, breakdown_minutes: 15 }
    },
    raw_snippet: "Salón Estudio 1 montaje U-shape 12 pax CB continuo y pantalla HDMI."
  },
  {
    id: "evt-seed-2",
    title: "Workshop Innovación & Liderazgo Meliá",
    date: "2026-09-12",
    time_start: "10:00",
    time_end: "18:00",
    space: { id: "multifuncional", name: "Multifuncional", color_tag: "#7b2cbf" },
    setup: { key: "escuela", label: "Escuela (Classroom)", icon: "🎓" },
    pax: 38,
    services: [
      { type: "fb", key: "coffee_break", label: "Coffee Break", icon: "☕" },
      { type: "fb", key: "almuerzo_trabajo", label: "Almuerzo de Trabajo", icon: "🥪" },
      { type: "equipment", key: "audiovisuales", label: "Audiovisuales (AV)", icon: "🎥" },
      { type: "equipment", key: "microfonia", label: "Microfonía", icon: "🎙️" }
    ],
    operational: {
      furniture: { mesas_rectangulares: 19, mesas_redondas: 0, mesas_altas: 0, sillas: 38 },
      times: { setup_minutes: 45, breakdown_minutes: 25 }
    },
    raw_snippet: "Sala Multifuncional montaje escuela 38 pax, CB mañana y tarde + almuerzo buffet."
  },
  {
    id: "evt-seed-3",
    title: "Sunset Cocktail & Art Gallery Opening",
    date: "2026-09-12",
    time_start: "19:30",
    time_end: "22:30",
    space: { id: "foyer", name: "Foyer", color_tag: "#d4af37" },
    setup: { key: "coctel", label: "Cóctel (Cocktail)", icon: "🍸" },
    pax: 70,
    services: [
      { type: "fb", key: "welcome_drink", label: "Welcome Drink / Cava", icon: "🥂" }
    ],
    operational: {
      furniture: { mesas_rectangulares: 0, mesas_redondas: 0, mesas_altas: 7, sillas: 5 },
      times: { setup_minutes: 45, breakdown_minutes: 25 }
    },
    raw_snippet: "Inauguración exposición ME Gallery en el Foyer. Formato cóctel 70 pax welcome drink cava."
  },
  {
    id: "evt-seed-4",
    title: "Comité Financiero Banco Santander",
    date: "2026-09-13",
    time_start: "09:30",
    time_end: "14:00",
    space: { id: "estudio-3", name: "Estudio 3", color_tag: "#48cae4" },
    setup: { key: "imperial", label: "Mesa Imperial", icon: "🏛️" },
    pax: 14,
    services: [
      { type: "fb", key: "coffee_break", label: "Coffee Break", icon: "☕" },
      { type: "equipment", key: "audiovisuales", label: "Audiovisuales (AV)", icon: "🎥" }
    ],
    operational: {
      furniture: { mesas_rectangulares: 7, mesas_redondas: 0, mesas_altas: 0, sillas: 14 },
      times: { setup_minutes: 25, breakdown_minutes: 15 }
    },
    raw_snippet: "Estudio 3 mesa imperial 14 pax CB continuo aguas y pantalla proyector."
  },
  {
    id: "evt-seed-5",
    title: "Lanzamiento Colección L'Oréal Professionnel",
    date: "2026-09-13",
    time_start: "16:00",
    time_end: "20:00",
    space: { id: "estudio-5", name: "Estudio 5", color_tag: "#0077b6" },
    setup: { key: "teatro", label: "Teatro (Auditorio)", icon: "🎭" },
    pax: 40,
    services: [
      { type: "equipment", key: "tarima_atril", label: "Tarima / Atril", icon: "🎤" },
      { type: "equipment", key: "microfonia", label: "Microfonía", icon: "🎙️" }
    ],
    operational: {
      furniture: { mesas_rectangulares: 0, mesas_redondas: 0, mesas_altas: 0, sillas: 42 },
      times: { setup_minutes: 45, breakdown_minutes: 25 }
    },
    raw_snippet: "Estudio 5 montaje teatro 40 pax con micro inalámbrico y atril central."
  },
  {
    id: "evt-seed-6",
    title: "Simposio QuirónSalud Málaga",
    date: "2026-09-14",
    time_start: "08:30",
    time_end: "15:00",
    space: { id: "multifuncional", name: "Multifuncional", color_tag: "#7b2cbf" },
    setup: { key: "u_shape", label: "Herradura / U-Shape", icon: "🧲" },
    pax: 24,
    services: [
      { type: "fb", key: "coffee_break", label: "Coffee Break", icon: "☕" },
      { type: "equipment", key: "audiovisuales", label: "Audiovisuales (AV)", icon: "🎥" }
    ],
    operational: {
      furniture: { mesas_rectangulares: 13, mesas_redondas: 0, mesas_altas: 0, sillas: 24 },
      times: { setup_minutes: 45, breakdown_minutes: 25 }
    },
    raw_snippet: "Sala Multifuncional U-Shape 24 pax CB mañana y AV."
  }
];

// Inicialización de la App
document.addEventListener('DOMContentLoaded', async () => {
  initDate();
  loadEventsFromStorage();
  await syncWithBackend();
  setupEventListeners();
  setupTouchGestures();
  renderTimeline();
  renderCards();
});

function initDate() {
  // Fecha seleccionada por defecto: fecha actual en formato YYYY-MM-DD
  const now = new Date();
  state.selectedDate = formatDateKey(now);
}

function formatDateKey(dateObj) {
  const y = dateObj.getFullYear();
  const m = String(dateObj.getMonth() + 1).padStart(2, '0');
  const d = String(dateObj.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function loadEventsFromStorage() {
  const saved = localStorage.getItem('me_vents_data');
  if (saved) {
    try {
      state.events = JSON.parse(saved);
    } catch (e) {
      state.events = SEED_EVENTS;
    }
  } else {
    state.events = SEED_EVENTS;
    saveEventsToStorage();
  }
}

function saveEventsToStorage() {
  localStorage.setItem('me_vents_data', JSON.stringify(state.events));
}

async function syncWithBackend() {
  try {
    const res = await fetch('/api/events');
    if (res.ok) {
      const serverEvents = await res.json();
      if (serverEvents && serverEvents.length > 0) {
        state.events = serverEvents;
        saveEventsToStorage();
      }
    }
  } catch (err) {
    console.log('Operando en modo local/offline.');
  }
}

// ==========================================================================
// RENDERIZADO DEL TIMELINE DE DÍAS
// ==========================================================================
function renderTimeline() {
  const slider = document.getElementById('daysSlider');
  if (!slider) return;
  slider.innerHTML = '';

  const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  
  // Generar rango de 7 días: 2 días antes hasta 4 días después de hoy
  const today = new Date();
  const daysToShow = [];
  
  for (let i = -2; i <= 4; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    daysToShow.push(d);
  }

  daysToShow.forEach(dateObj => {
    const key = formatDateKey(dateObj);
    const dayName = dayNames[dateObj.getDay()];
    const dayNum = dateObj.getDate();
    
    // Contar eventos para este día
    const count = state.events.filter(e => e.date === key).length;
    const isActive = key === state.selectedDate;

    const pill = document.createElement('div');
    pill.className = `day-pill ${isActive ? 'active' : ''}`;
    pill.innerHTML = `
      <span class="day-name">${dayName}</span>
      <span class="day-number">${dayNum}</span>
      <span class="event-indicator">${count} ${count === 1 ? 'evento' : 'eventos'}</span>
    `;

    pill.addEventListener('click', () => {
      state.selectedDate = key;
      renderTimeline();
      renderCards();
    });

    slider.appendChild(pill);
  });
}

// ==========================================================================
// RENDERIZADO DE CARDS DE MONTAJE
// ==========================================================================
function renderCards() {
  const container = document.getElementById('cardsContainer');
  const totalCountEl = document.getElementById('todayTotalCount');
  const paxCountEl = document.getElementById('todayPaxCount');
  if (!container) return;

  // Filtrar eventos por fecha seleccionada
  let filtered = state.events.filter(e => e.date === state.selectedDate);

  // Filtro por salón
  if (state.activeFilterSpace !== 'all') {
    filtered = filtered.filter(e => e.space && e.space.id === state.activeFilterSpace);
  }

  // Filtro por tipo de montaje
  if (state.activeFilterSetup !== 'all') {
    filtered = filtered.filter(e => e.setup && e.setup.key === state.activeFilterSetup);
  }

  // Filtro por búsqueda de texto
  if (state.searchQuery.trim() !== '') {
    const q = state.searchQuery.toLowerCase();
    filtered = filtered.filter(e => 
      e.title.toLowerCase().includes(q) ||
      (e.space && e.space.name.toLowerCase().includes(q)) ||
      (e.setup && e.setup.label.toLowerCase().includes(q))
    );
  }

  // Actualizar métricas del día en la barra superior
  const dayEvents = state.events.filter(e => e.date === state.selectedDate);
  const totalPax = dayEvents.reduce((acc, cur) => acc + (cur.pax || 0), 0);
  if (totalCountEl) totalCountEl.textContent = dayEvents.length;
  if (paxCountEl) paxCountEl.textContent = totalPax;

  // Renderizar o Mostrar Empty State
  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🛋️</div>
        <div class="empty-title">No hay montajes para este día</div>
        <div class="empty-desc">Todo despejado en salones. Puedes subir una nueva Orden de Servicio (BEO) o añadir un evento con el botón de abajo.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(evt => createEventCardHTML(evt)).join('');

  // Vincular eventos de accordions y eliminación
  container.querySelectorAll('.accordion-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const body = btn.nextElementSibling;
      body.classList.toggle('open');
      btn.querySelector('.acc-icon').textContent = body.classList.contains('open') ? '▲' : '▼';
    });
  });

  container.querySelectorAll('.del-card-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      deleteEvent(id);
    });
  });
}

function createEventCardHTML(evt) {
  const spaceColor = evt.space?.color_tag || '#0080ff';
  const spaceName = evt.space?.name || 'Salón no asignado';
  const setupLabel = evt.setup?.label || 'Estándar';
  const setupIcon = evt.setup?.icon || '📋';
  const pax = evt.pax || 0;
  const time = `${evt.time_start || '09:00'} - ${evt.time_end || '14:00'}`;

  // Badges de Servicios F&B y Equipamiento
  const servicesHTML = (evt.services || []).map(s => {
    const isFb = s.type === 'fb';
    return `<span class="badge ${isFb ? 'badge-fb' : 'badge-eq'}">${s.icon || '✨'} ${s.label}</span>`;
  }).join('');

  // Datos operativos de mobiliario
  const furniture = evt.operational?.furniture || { mesas_rectangulares: 0, mesas_redondas: 0, mesas_altas: 0, sillas: pax };
  const times = evt.operational?.times || { setup_minutes: 30, breakdown_minutes: 20 };

  return `
    <div class="event-card">
      <div class="card-top">
        <span class="salon-tag" style="color: ${spaceColor}; border-color: ${spaceColor}40;">
          <span style="width: 7px; height: 7px; border-radius: 50%; background: ${spaceColor};"></span>
          ${spaceName}
        </span>
        <span class="time-badge">🕒 ${time}</span>
      </div>

      <div class="event-title">${evt.title}</div>

      <div class="badges-row">
        <span class="badge badge-setup">${setupIcon} ${setupLabel}</span>
        <span class="badge badge-pax">👥 ${pax} PAX</span>
        ${servicesHTML}
      </div>

      <div class="operational-accordion">
        <button class="accordion-toggle" type="button">
          <span>📦 Plan Operativo de Montaje</span>
          <span class="acc-icon">▼</span>
        </button>
        <div class="accordion-body">
          <div class="furniture-metrics">
            ${furniture.mesas_rectangulares > 0 ? `
              <div class="metric-box">
                <span class="metric-val">${furniture.mesas_rectangulares}</span>
                <span class="metric-label">Mesas Rectangulares</span>
              </div>
            ` : ''}
            ${furniture.mesas_redondas > 0 ? `
              <div class="metric-box">
                <span class="metric-val">${furniture.mesas_redondas}</span>
                <span class="metric-label">Mesas Redondas</span>
              </div>
            ` : ''}
            ${furniture.mesas_altas > 0 ? `
              <div class="metric-box">
                <span class="metric-val">${furniture.mesas_altas}</span>
                <span class="metric-label">Mesas Altas Cóctel</span>
              </div>
            ` : ''}
            <div class="metric-box">
              <span class="metric-val">${furniture.sillas}</span>
              <span class="metric-label">Sillas Requeridas</span>
            </div>
          </div>

          <div class="timing-row">
            <span>⏱️ Montaje: <strong>${times.setup_minutes} min</strong></span>
            <span>🧹 Desmontaje: <strong>${times.breakdown_minutes} min</strong></span>
          </div>

          ${evt.raw_snippet ? `
            <div style="font-size: 0.72rem; color: var(--text-muted); background: rgba(0,0,0,0.2); padding: 0.4rem; border-radius: 4px;">
              📄 <em>"${evt.raw_snippet}"</em>
            </div>
          ` : ''}
        </div>
      </div>

      <div class="card-actions">
        <label class="setup-check-label">
          <input type="checkbox" class="setup-check-input">
          <span>Montaje listo en sala</span>
        </label>
        <button class="del-card-btn" data-id="${evt.id}" title="Eliminar orden">🗑️ Eliminar</button>
      </div>
    </div>
  `;
}

// ==========================================================================
// GESTOS TÁCTILES Y DESLIZAMIENTO CON EL DEDO (SWIPE)
// ==========================================================================
function setupTouchGestures() {
  const container = document.getElementById('swipeContainer');
  if (!container) return;

  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let isSwiping = false;

  container.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    isSwiping = true;
  }, { passive: true });

  container.addEventListener('touchmove', (e) => {
    if (!isSwiping) return;
    currentX = e.touches[0].clientX;
  }, { passive: true });

  container.addEventListener('touchend', (e) => {
    if (!isSwiping) return;
    isSwiping = false;
    const deltaX = currentX - startX;
    
    // Si el deslizamiento horizontal fue suficiente (más de 60px)
    if (Math.abs(deltaX) > 60) {
      if (deltaX > 0) {
        // Deslizar hacia la derecha -> Día anterior
        changeDay(-1);
      } else {
        // Deslizar hacia la izquierda -> Día siguiente
        changeDay(1);
      }
    }
  });

  // Flechas de navegación del teclado o botones
  const prevBtn = document.getElementById('prevDayBtn');
  const nextBtn = document.getElementById('nextDayBtn');
  if (prevBtn) prevBtn.addEventListener('click', () => changeDay(-1));
  if (nextBtn) nextBtn.addEventListener('click', () => changeDay(1));
}

function changeDay(delta) {
  const cur = new Date(state.selectedDate);
  cur.setDate(cur.getDate() + delta);
  state.selectedDate = formatDateKey(cur);

  // Animación suave de transición
  const container = document.getElementById('swipeContainer');
  if (container) {
    container.style.opacity = '0.3';
    container.style.transform = `translateX(${delta * -25}px)`;
    setTimeout(() => {
      renderTimeline();
      renderCards();
      container.style.opacity = '1';
      container.style.transform = 'translateX(0)';
    }, 150);
  } else {
    renderTimeline();
    renderCards();
  }
}

// ==========================================================================
// EVENT LISTENERS & FILTROS
// ==========================================================================
function setupEventListeners() {
  // Buscador
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      renderCards();
    });
  }

  // Filtros de salón
  document.querySelectorAll('.filter-chip[data-space]').forEach(chip => {
    chip.addEventListener('click', (e) => {
      document.querySelectorAll('.filter-chip[data-space]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.activeFilterSpace = chip.getAttribute('data-space');
      renderCards();
    });
  });

  // Modal de Subida / Nueva Orden
  const openModalBtn = document.getElementById('openModalBtn');
  const fabBtn = document.getElementById('fabBtn');
  const closeModalBtn = document.getElementById('closeModalBtn');
  const uploadModal = document.getElementById('uploadModal');

  const openModal = () => uploadModal.classList.add('open');
  const closeModal = () => uploadModal.classList.remove('open');

  if (openModalBtn) openModalBtn.addEventListener('click', openModal);
  if (fabBtn) fabBtn.addEventListener('click', openModal);
  if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);

  if (uploadModal) {
    uploadModal.addEventListener('click', (e) => {
      if (e.target === uploadModal) closeModal();
    });
  }

  // Manejo de Dropzone y subida de archivos
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const quickInput = document.getElementById('quickTextInput');
  const processBtn = document.getElementById('processOrderBtn');

  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        dropzone.querySelector('.dropzone-label').textContent = `📄 ${fileInput.files[0].name}`;
      }
    });
  }

  if (processBtn) {
    processBtn.addEventListener('click', async () => {
      const file = fileInput?.files[0];
      const rawText = quickInput?.value.trim() || '';

      if (!file && !rawText) {
        alert('Por favor, selecciona un PDF o escribe el texto de la orden (ej: "Estudio 1 u shape 12 pax cb").');
        return;
      }

      processBtn.disabled = true;
      processBtn.textContent = '⚡ Analizando orden con IA...';

      try {
        await processAndAddOrder(file, rawText);
        closeModal();
        if (fileInput) fileInput.value = '';
        if (quickInput) quickInput.value = '';
        if (dropzone) dropzone.querySelector('.dropzone-label').textContent = 'Arrastra tu PDF o pulsa para examinar';
      } catch (err) {
        console.error(err);
      } finally {
        processBtn.disabled = false;
        processBtn.textContent = '✨ Procesar e Integrar en Agenda';
      }
    });
  }
}

// ==========================================================================
// MOTOR DE EXTRACCIÓN (CLIENTE / FALLBACK OFFLINE)
// ==========================================================================
async function processAndAddOrder(file, rawText) {
  // 1. Intentar con el Backend si está disponible
  let eventResult = null;
  try {
    const formData = new FormData();
    if (file) formData.append('file', file);
    if (rawText) formData.append('raw_text', rawText);

    const res = await fetch('/api/upload-beo', {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      eventResult = data.event;
    }
  } catch (err) {
    console.log('Backend no disponible, ejecutando extractor local de emergencia...');
  }

  // 2. Extracción Local en JS si el backend está offline
  if (!eventResult) {
    eventResult = parseOrderClientSide(rawText, file ? file.name : null);
  }

  // Agregar al estado y guardar
  state.events.push(eventResult);
  state.selectedDate = eventResult.date || state.selectedDate;
  saveEventsToStorage();
  renderTimeline();
  renderCards();
}

function parseOrderClientSide(text, filename) {
  const tLower = text.toLowerCase();

  // Salón
  let matchedSpace = DEFAULT_SPACES.find(s => tLower.includes(s.id.replace('-', ' ')) || tLower.includes(s.name.toLowerCase()));
  if (!matchedSpace) {
    if (tLower.includes('multi') || tLower.includes('multifuncional')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'multifuncional');
    else if (tLower.includes('foyer')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'foyer');
    else if (tLower.includes('cañitas') || tLower.includes('canitas')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'canitas-al-fresco');
    else if (tLower.includes('terraza') || tLower.includes('rooftop')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'terraza-rooftop');
    else matchedSpace = DEFAULT_SPACES[0]; // Estudio 1 por defecto
  }

  // Montaje
  let setup = { key: "estandar", label: "Montaje Estándar", icon: "📋" };
  if (tLower.includes('u shape') || tLower.includes('u-shape') || tLower.includes('herradura') || tLower.includes(' en u')) {
    setup = { key: "u_shape", label: "Herradura / U-Shape", icon: "🧲" };
  } else if (tLower.includes('escuela') || tLower.includes('classroom') || tLower.includes('aulas')) {
    setup = { key: "escuela", label: "Escuela (Classroom)", icon: "🎓" };
  } else if (tLower.includes('coctel') || tLower.includes('cóctel') || tLower.includes('cocktail') || tLower.includes('de pie')) {
    setup = { key: "coctel", label: "Cóctel (Cocktail)", icon: "🍸" };
  } else if (tLower.includes('banquete') || tLower.includes('redondas')) {
    setup = { key: "banquete", label: "Banquete (Mesas Redondas)", icon: "🍽️" };
  } else if (tLower.includes('teatro') || tLower.includes('auditorio')) {
    setup = { key: "teatro", label: "Teatro (Auditorio)", icon: "🎭" };
  } else if (tLower.includes('imperial') || tLower.includes('boardroom')) {
    setup = { key: "imperial", label: "Mesa Imperial", icon: "🏛️" };
  }

  // PAX
  let pax = 15;
  const paxMatch = text.match(/(\d+)\s*(?:pax|personas|asistentes|comensales|pers)/i);
  if (paxMatch) pax = parseInt(paxMatch[1], 10);

  // Servicios
  const services = [];
  if (tLower.includes('cb') || tLower.includes('c.b') || tLower.includes('coffee') || tLower.includes('café') || tLower.includes('cafe')) {
    services.push({ type: "fb", key: "coffee_break", label: "Coffee Break", icon: "☕" });
  }
  if (tLower.includes('lunch') || tLower.includes('almuerzo') || tLower.includes('buffet')) {
    services.push({ type: "fb", key: "almuerzo_trabajo", label: "Almuerzo de Trabajo", icon: "🥪" });
  }
  if (tLower.includes('welcome') || tLower.includes('bienvenida') || tLower.includes('cava')) {
    services.push({ type: "fb", key: "welcome_drink", label: "Welcome Drink", icon: "🥂" });
  }
  if (tLower.includes('av') || tLower.includes('a/v') || tLower.includes('pantalla') || tLower.includes('proyector') || tLower.includes('hdmi')) {
    services.push({ type: "equipment", key: "audiovisuales", label: "Audiovisuales (AV)", icon: "🎥" });
  }

  // Horario
  let timeStart = "09:00";
  let timeEnd = "14:00";
  const timeMatch = text.match(/(\d{1,2}[:.]\d{2})\s*(?:-|a)\s*(\d{1,2}[:.]\d{2})/);
  if (timeMatch) {
    timeStart = timeMatch[1].replace('.', ':');
    timeEnd = timeMatch[2].replace('.', ':');
  }

  // Mobiliario calculado
  let mesasRect = 0, mesasRed = 0, mesasAltas = 0;
  if (setup.key === 'u_shape') mesasRect = Math.ceil(pax / 2) + 1;
  else if (setup.key === 'escuela') mesasRect = Math.ceil(pax / 2);
  else if (setup.key === 'banquete') mesasRed = Math.ceil(pax / 8);
  else if (setup.key === 'coctel') mesasAltas = Math.max(2, Math.ceil(pax / 10));
  else if (setup.key === 'imperial') mesasRect = Math.ceil(pax / 2);

  return {
    id: `evt-${Date.now()}`,
    title: filename ? filename.replace(/\.(pdf|png|jpg)$/i, '') : `Evento en ${matchedSpace.name}`,
    date: state.selectedDate || formatDateKey(new Date()),
    time_start: timeStart,
    time_end: timeEnd,
    space: matchedSpace,
    setup: setup,
    pax: pax,
    services: services,
    operational: {
      furniture: { mesas_rectangulares: mesasRect, mesas_redondas: mesasRed, mesas_altas: mesasAltas, sillas: pax },
      times: { setup_minutes: 30, breakdown_minutes: 20 }
    },
    raw_snippet: text.substring(0, 150)
  };
}

async function deleteEvent(id) {
  if (confirm('¿Seguro que deseas eliminar este evento?')) {
    state.events = state.events.filter(e => e.id !== id);
    saveEventsToStorage();
    try {
      await fetch(`/api/events/${id}`, { method: 'DELETE' });
    } catch (e) {
      // offline ok
    }
    renderTimeline();
    renderCards();
  }
}
