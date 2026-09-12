/**
 * ME_VENTS - Cards Rendering & Filtering Module
 */

import { state, saveEventsToStorage } from './state.js';
import { renderTimeline } from './timeline.js';

export function renderCards() {
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

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🛋️</div>
        <div class="empty-title">No hay montajes para este día</div>
        <div class="empty-desc">Todo despejado en salones. Puedes subir una nueva Orden de Servicio (BEO) o añadir un evento con el botón superior.</div>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(evt => createEventCardHTML(evt)).join('');

  // Vincular eventos de acordeón
  container.querySelectorAll('.accordion-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const body = btn.nextElementSibling;
      body.classList.toggle('open');
      btn.querySelector('.acc-icon').textContent = body.classList.contains('open') ? '▲' : '▼';
    });
  });

  // Vincular botón eliminar
  container.querySelectorAll('.del-card-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      deleteEvent(id);
    });
  });
}

export function createEventCardHTML(evt) {
  const spaceColor = evt.space?.color_tag || '#0080ff';
  const spaceName = evt.space?.name || 'Salón no asignado';
  const setupLabel = evt.setup?.label || 'Estándar';
  const setupIcon = evt.setup?.icon || '📋';
  const pax = evt.pax || 0;
  const time = `${evt.time_start || '09:00'} - ${evt.time_end || '14:00'}`;

  const servicesHTML = (evt.services || []).map(s => {
    const isFb = s.type === 'fb';
    return `<span class="badge ${isFb ? 'badge-fb' : 'badge-eq'}">${s.icon || '✨'} ${s.label}</span>`;
  }).join('');

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

export async function deleteEvent(id) {
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

export function setupFilterControls() {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      renderCards();
    });
  }

  document.querySelectorAll('.filter-chip[data-space]').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip[data-space]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.activeFilterSpace = chip.getAttribute('data-space');
      renderCards();
    });
  });
}
