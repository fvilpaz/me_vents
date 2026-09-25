/**
 * ME_VENTS - Global State & Data Store Module
 */

export const state = {
  events: [],
  selectedDate: null,
  activeFilterSpace: 'all',
  activeFilterSetup: 'all',
  searchQuery: '',
  spacesConfig: [],
  jargonConfig: {}
};

export const DEFAULT_SPACES = [
  { id: "estudio-1", name: "Estudio 1", color_tag: "#0080ff", max_capacities: { u_shape: 16, escuela: 24, teatro: 35, banquete: 20, coctel: 35, imperial: 14 } },
  { id: "estudio-2", name: "Estudio 2", color_tag: "#00b4d8", max_capacities: { u_shape: 14, escuela: 20, teatro: 30, banquete: 18, coctel: 30, imperial: 12 } },
  { id: "estudio-3", name: "Estudio 3", color_tag: "#48cae4", max_capacities: { u_shape: 18, escuela: 28, teatro: 40, banquete: 24, coctel: 40, imperial: 16 } },
  { id: "estudio-2-3", name: "Estudio 2 + 3", color_tag: "#0284c7", max_capacities: { u_shape: 26, escuela: 45, teatro: 65, banquete: 40, coctel: 65, imperial: 24 } },
  { id: "estudio-4", name: "Estudio 4", color_tag: "#90e0ef", max_capacities: { u_shape: 12, escuela: 16, teatro: 25, banquete: 16, coctel: 25, imperial: 10 } },
  { id: "estudio-5", name: "Estudio 5", color_tag: "#0077b6", max_capacities: { u_shape: 20, escuela: 32, teatro: 45, banquete: 30, coctel: 50, imperial: 18 } },
  { id: "foyer", name: "Foyer", color_tag: "#d4af37", max_capacities: { coctel: 100, banquete: 50 } },
  { id: "multifuncional", name: "Multifuncional", color_tag: "#7b2cbf", max_capacities: { u_shape: 36, escuela: 90, teatro: 140, banquete: 100, coctel: 150 } },
  { id: "canitas-al-fresco", name: "Cañitas al Fresco", color_tag: "#2ec4b6", max_capacities: { coctel: 90, banquete: 60 } },
  { id: "ene", name: "Eñe", color_tag: "#f59e0b", max_capacities: {} },
  { id: "terraza-rooftop", name: "Terraza / Rooftop", color_tag: "#e76f51", max_capacities: { coctel: 140, banquete: 70 } }
];

export function formatDateKey(dateObj) {
  const y = dateObj.getFullYear();
  const m = String(dateObj.getMonth() + 1).padStart(2, '0');
  const d = String(dateObj.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function todayKey() {
  return formatDateKey(new Date());
}

// Un grupo = mismo block_id (o, sin él, mismo nombre de grupo).
function groupKey(e) {
  return e.block_id || (e.multi_day && e.multi_day.group_name) || e.title;
}

// Si evt está en el ÚLTIMO día de su grupo devuelve { endTime } (hora a la que acaba su última sesión); si no, null.
export function groupEndInfo(evt) {
  if (!evt.date) return null;
  const group = state.events.filter(e => e.date && groupKey(e) === groupKey(evt));
  const lastDate = group.map(e => e.date).sort().pop();
  if (evt.date !== lastDate) return null;
  const ends = group
    .filter(e => e.date === lastDate)
    .map(e => e.time_end)
    .filter(t => /^\d{1,2}:\d{2}$/.test(t || ''))
    .sort();
  return { endTime: ends.length ? ends[ends.length - 1] : null };
}

// Fecha por defecto: hoy si tiene eventos; si no, el próximo día con eventos; si no, el último que hubo.
export function pickDefaultDate(sortedDates) {
  const today = todayKey();
  if (sortedDates.length === 0) return today;
  if (sortedDates.includes(today)) return today;
  return sortedDates.find(d => d > today) || sortedDates[sortedDates.length - 1];
}

function eventDates() {
  return [...new Set(state.events.map(e => e.date).filter(Boolean))].sort();
}

export function initDate() {
  state.selectedDate = pickDefaultDate(eventDates());
}

const DATA_VERSION = 'v2.0-clean';

export function loadEventsFromStorage() {
  const version = localStorage.getItem('me_vents_version');
  if (version !== DATA_VERSION) {
    localStorage.removeItem('me_vents_data');
    localStorage.removeItem('me_vents_cleared_by_user');
    localStorage.setItem('me_vents_version', DATA_VERSION);
    state.events = [];
    return;
  }
  
  const saved = localStorage.getItem('me_vents_data');
  if (saved) {
    try {
      state.events = JSON.parse(saved);
      // Purgado proactivo de eventos viejos con Estudio 2 o 3 Meeting
      const isStale = state.events.some(e => 
        (e.title && (e.title.includes('3 Meeting') || e.title.includes('Multifuncional Multifuntional'))) || 
        (e.space && e.space.id === 'estudio-2' && e.title && e.title.toLowerCase().includes('kevin'))
      );
      if (isStale) {
        state.events = [];
        localStorage.removeItem('me_vents_data');
      }
    } catch (e) {
      state.events = [];
    }
  } else {
    state.events = [];
  }
}

export function saveEventsToStorage() {
  localStorage.setItem('me_vents_data', JSON.stringify(state.events));
  localStorage.setItem('me_vents_version', DATA_VERSION);
}

export async function syncWithBackend() {
  // Si el usuario ha vaciado intencionadamente la agenda, respetamos su decisión y no forzamos la demo
  if (localStorage.getItem('me_vents_cleared_by_user') === 'true') {
    state.events = [];
    return;
  }

  try {
    const res = await fetch('/api/events');
    if (res.ok) {
      const serverEvents = await res.json();
      if (Array.isArray(serverEvents) && serverEvents.length > 0) {
        state.events = serverEvents;
        saveEventsToStorage();
        const dates = eventDates();
        if (dates.length > 0 && (!state.selectedDate || !dates.includes(state.selectedDate))) {
          state.selectedDate = pickDefaultDate(dates);
        }
        return;
      }
    }
  } catch (err) {
    // Backend no disponible (ej. GitHub Pages estático)
  }

  // Sincronización para GitHub Pages con cache-buster si no fue limpiado por el usuario
  try {
    const cacheBuster = `t=${Date.now()}`;
    const staticRes = await fetch(`./data/events.json?${cacheBuster}`, { cache: 'no-store' });
    if (staticRes.ok) {
      const staticEvents = await staticRes.json();
      if (Array.isArray(staticEvents) && staticEvents.length > 0) {
        state.events = staticEvents;
        saveEventsToStorage();
        const dates = eventDates();
        if (dates.length > 0 && (!state.selectedDate || !dates.includes(state.selectedDate))) {
          state.selectedDate = pickDefaultDate(dates);
        }
      }
    }
  } catch (e) {
    console.log('Operando en modo offline/cache.');
  }
}

export async function clearAllEvents() {
  state.events = [];
  saveEventsToStorage();
  localStorage.setItem('me_vents_cleared_by_user', 'true');
  try {
    await fetch('/api/events', { method: 'DELETE' });
  } catch (err) {
    console.log('Limpiado en local');
  }
}

