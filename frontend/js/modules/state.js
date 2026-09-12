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
  { id: "terraza-rooftop", name: "Terraza / Rooftop", color_tag: "#e76f51", max_capacities: { coctel: 140, banquete: 70 } }
];

export const SEED_EVENTS = [
  {
    id: "evt-seed-1",
    title: "Junta Ejecutiva Telefónica Tech",
    date: "2026-09-12",
    time_start: "09:00",
    time_end: "13:30",
    space: { id: "estudio-1", name: "Estudio 1", color_tag: "#0080ff" },
    setup: { key: "forma_u", label: "Forma U (U-Shape)", icon: "🏛️" },
    pax: 12,
    services: [
      { type: "fb", key: "coffee_break", label: "Coffee Break", icon: "☕" },
      { type: "equipment", key: "audiovisuales", label: "Audiovisuales (AV)", icon: "🎥" }
    ],
    operational: {
      furniture_summary: "Montaje en U (U-Shape) para 12 pax",
      montaje_notes: "Mesas en U orientadas a pantalla TV.\nBlocs de notas ME y bolígrafo por persona.\nAgua mineral en cada puesto.",
      sstt_notes: "TV 86 pulgadas encendida con HDMI y ClickShare preparado.\nCalefacción/AC regulado a 22ºC.",
      fb_notes: "Coffee break permanente en el anexo con café, leche vegetal y fruta.",
      pisos_notes: "Protocolo AURA aplicado 20 min antes. Sala perfumada.",
      furniture: { mesas_rectangulares: 7, mesas_redondas: 0, mesas_altas: 0, sillas: 12 },
      times: { setup_minutes: 25, breakdown_minutes: 15 }
    },
    manager: "Marta Delange",
    block_id: "681200",
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
  }
];

export function formatDateKey(dateObj) {
  const y = dateObj.getFullYear();
  const m = String(dateObj.getMonth() + 1).padStart(2, '0');
  const d = String(dateObj.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function initDate() {
  const now = new Date();
  state.selectedDate = formatDateKey(now);
}

export function loadEventsFromStorage() {
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

export function saveEventsToStorage() {
  localStorage.setItem('me_vents_data', JSON.stringify(state.events));
}

export async function syncWithBackend() {
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
