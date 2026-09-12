import { state, saveEventsToStorage } from './state.js';
import { renderTimeline } from './timeline.js';
import { escapeHTML } from './security.js';

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
  const spaceName = escapeHTML(evt.space?.name || 'Salón no asignado');
  const setupLabel = escapeHTML(evt.setup?.label || 'Estándar');
  const setupIcon = evt.setup?.icon || '📋';
  const pax = parseInt(evt.pax, 10) || 0;
  const time = escapeHTML(`${evt.time_start || '09:00'} - ${evt.time_end || '14:00'}`);
  const title = escapeHTML(evt.title || 'Evento');

  const servicesHTML = (evt.services || []).map(s => {
    const isFb = s.type === 'fb';
    return `<span class="badge ${isFb ? 'badge-fb' : 'badge-eq'}">${s.icon || '✨'} ${escapeHTML(s.label)}</span>`;
  }).join('');

  const op = evt.operational || {};
  const furniture = op.furniture || { mesas_rectangulares: 0, mesas_redondas: 0, mesas_altas: 0, sillas: pax };
  const times = op.times || { setup_minutes: 30, breakdown_minutes: 20 };
  const layoutSummary = op.furniture_summary || '';
  const montajeNotes = op.montaje_notes || '';
  const ssttNotes = op.sstt_notes || '';
  const fbNotes = op.fb_notes || '';
  const pisosNotes = [op.timing_notes, op.pisos_notes].filter(Boolean).join('\n');
  const warningAforo = op.warning_aforo || '';

  return `
    <div class="event-card">
      <div class="card-top">
        <span class="salon-tag" style="color: ${spaceColor}; border-color: ${spaceColor}40;">
          <span style="width: 7px; height: 7px; border-radius: 50%; background: ${spaceColor};"></span>
          ${spaceName}
        </span>
        <span class="time-badge">🕒 ${time}</span>
      </div>

      ${evt.multi_day && evt.multi_day.is_multi_day ? `
        <div class="multiday-badge">
          <span>🗓️</span> <strong>${escapeHTML(evt.multi_day.day_label)}</strong> · ${escapeHTML(evt.multi_day.group_name)} (${escapeHTML(evt.multi_day.date_start)} al ${escapeHTML(evt.multi_day.date_end)})
        </div>
      ` : ''}

      <div class="event-title">${title}</div>

      <div class="badges-row">
        <span class="badge badge-setup">${setupIcon} ${setupLabel}</span>
        <span class="badge badge-pax">👥 ${pax} PAX</span>
        ${servicesHTML}
      </div>

      <div class="operational-accordion">
        <button class="accordion-toggle" type="button">
          <span>📋 Plan Operativo de Sala</span>
          <span class="acc-icon">▼</span>
        </button>
        <div class="accordion-body">
          ${warningAforo ? `
            <div style="font-size: 0.73rem; color: #f87171; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.45rem 0.65rem; border-radius: 4px;">
              ${escapeHTML(warningAforo)}
            </div>
          ` : ''}

          ${layoutSummary ? `
            <div class="op-layout-summary">
              <span>📐</span> ${escapeHTML(layoutSummary)}
            </div>
          ` : ''}

          ${montajeNotes ? `
            <div class="op-detail-block op-montaje">
              <div class="op-detail-header"><span>📐 Montaje & Distribución BEO</span></div>
              <div class="op-detail-content">${escapeHTML(montajeNotes)}</div>
            </div>
          ` : ''}

          ${ssttNotes ? `
            <div class="op-detail-block op-sstt">
              <div class="op-detail-header"><span>📺 SSTT & Audiovisuales</span></div>
              <div class="op-detail-content">${escapeHTML(ssttNotes)}</div>
            </div>
          ` : ''}

          ${fbNotes ? `
            <div class="op-detail-block op-fb">
              <div class="op-detail-header"><span>☕ Alimentos & Bebidas (F&B)</span></div>
              <div class="op-detail-content">${escapeHTML(fbNotes)}</div>
            </div>
          ` : ''}

          ${pisosNotes ? `
            <div class="op-detail-block op-pisos">
              <div class="op-detail-header"><span>✨ Pisos, AURA & Timing</span></div>
              <div class="op-detail-content">${escapeHTML(pisosNotes)}</div>
            </div>
          ` : ''}

          ${op.menu_notes ? `
            <div class="op-detail-block op-menu">
              <div class="op-detail-header"><span>🍽️ Gastronomía & Menú Completo (BEO)</span></div>
              <div class="op-detail-content op-menu-content">${escapeHTML(op.menu_notes)}</div>
            </div>
          ` : ''}

          <div class="timing-row">
            <span>⏱️ Montaje previsto: <strong>${parseInt(times.setup_minutes, 10)} min</strong></span>
            <span>🧹 Desmontaje: <strong>${parseInt(times.breakdown_minutes, 10)} min</strong></span>
          </div>

          ${(evt.manager || evt.block_id || evt.pm) ? `
            <div class="op-meta-row">
              ${evt.manager ? `<span class="op-tag">👤 Catering: <strong>${escapeHTML(evt.manager)}</strong></span>` : ''}
              ${evt.block_id ? `<span class="op-tag">📋 BEO: <strong>${escapeHTML(evt.block_id)}</strong></span>` : ''}
              ${evt.pm ? `<span class="op-tag">PM: <strong>${escapeHTML(evt.pm)}</strong></span>` : ''}
            </div>
          ` : ''}
        </div>
      </div>

      <div class="card-actions">
        <label class="setup-check-label">
          <input type="checkbox" class="setup-check-input">
          <span>Montaje listo en sala</span>
        </label>
        <button class="del-card-btn" data-id="${escapeHTML(evt.id)}" title="Eliminar orden">🗑️ Eliminar</button>
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
