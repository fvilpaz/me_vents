/**
 * ME_VENTS - BEO Upload & Document Parser Module
 */

import { state, DEFAULT_SPACES, saveEventsToStorage, formatDateKey } from './state.js';
import { renderTimeline } from './timeline.js';
import { renderCards } from './cards.js';

export function setupUploaderListeners() {
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

export async function processAndAddOrder(file, rawText) {
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
      if (data.events && Array.isArray(data.events)) {
        localStorage.removeItem('me_vents_cleared_by_user');
        state.events = data.events;
        if (data.first_event?.date) {
          state.selectedDate = data.first_event.date;
        }
        saveEventsToStorage();
        renderTimeline();
        renderCards();
        alert(`✨ Se han identificado e integrado ${data.new_count || data.events.length} montajes y sesiones en la agenda.`);
        return;
      }
    }
  } catch (err) {
    console.log('Backend no disponible, ejecutando extractor local de emergencia...');
  }

  // Fallback local si el backend está offline
  const single = parseOrderClientSide(rawText, file ? file.name : null);
  localStorage.removeItem('me_vents_cleared_by_user');
  
  // Reemplazar o añadir sin duplicar por fecha, hora y sala
  const spId = single.space?.id || 'default';
  const key = `${single.date}_${single.time_start}_${spId}`;
  state.events = state.events.filter(e => `${e.date}_${e.time_start}_${e.space?.id || 'default'}` !== key);
  state.events.push(single);
  if (single.date) {
    state.selectedDate = single.date;
  }
  saveEventsToStorage();
  renderTimeline();
  renderCards();
}

export function parseOrderClientSide(text, filename) {
  const tLower = text.toLowerCase();

  let matchedSpace = DEFAULT_SPACES.find(s => tLower.includes(s.id.replace('-', ' ')) || tLower.includes(s.name.toLowerCase()));
  if (!matchedSpace) {
    if (tLower.includes('multi') || tLower.includes('multifuncional')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'multifuncional');
    else if (tLower.includes('foyer')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'foyer');
    else if (tLower.includes('cañitas') || tLower.includes('canitas')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'canitas-al-fresco');
    else if (tLower.includes('terraza') || tLower.includes('rooftop')) matchedSpace = DEFAULT_SPACES.find(s => s.id === 'terraza-rooftop');
    else matchedSpace = DEFAULT_SPACES[0];
  }

  let setup = { key: "estandar", label: "Montaje Estándar", icon: "📋" };
  if (tLower.includes('u shape') || tLower.includes('u-shape') || tLower.includes('forma u') || tLower.includes('forma de u') || tLower.includes('en u') || tLower.includes('ushape')) {
    setup = { key: "forma_u", label: "Forma U (U-Shape)", icon: "🏛️" };
  } else if (tLower.includes('workshop') || tLower.includes('trabajo en equipo')) {
    setup = { key: "workshop", label: "Workshop (Mesas de Trabajo)", icon: "🧩" };
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

  let pax = 15;
  const paxMatch = text.match(/(\d+)\s*(?:pax|personas|asistentes|comensales|pers)/i);
  if (paxMatch) pax = parseInt(paxMatch[1], 10);

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

  let timeStart = "09:00";
  let timeEnd = "14:00";
  const timeMatch = text.match(/(\d{1,2}[:.]\d{2})\s*(?:-|a)\s*(\d{1,2}[:.]\d{2})/);
  if (timeMatch) {
    timeStart = timeMatch[1].replace('.', ':');
    timeEnd = timeMatch[2].replace('.', ':');
  }

  let mesasRect = 0, mesasRed = 0, mesasAltas = 0;
  if (setup.key === 'forma_u' || setup.key === 'u_shape') mesasRect = Math.ceil(pax / 2) + 1;
  else if (setup.key === 'escuela') mesasRect = Math.ceil(pax / 2);
  else if (setup.key === 'banquete') mesasRed = Math.ceil(pax / 8);
  else if (setup.key === 'coctel') mesasAltas = Math.max(2, Math.ceil(pax / 10));
  else if (setup.key === 'imperial') mesasRect = Math.ceil(pax / 2);
  else if (setup.key === 'workshop') mesasRect = Math.ceil(pax / 4);

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
