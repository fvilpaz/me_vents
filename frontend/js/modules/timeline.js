/**
 * ME_VENTS - Day Timeline Module (Multi-day & Adaptive Calendar)
 */

import { state, formatDateKey } from './state.js';
import { renderCards } from './cards.js';

export function renderTimeline() {
  const slider = document.getElementById('daysSlider');
  if (!slider) return;
  slider.innerHTML = '';

  const dayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
  const daysToShow = [];

  // Recoger todas las fechas de eventos registrados
  const eventDates = [...new Set(state.events.map(e => e.date).filter(Boolean))].sort();

  if (eventDates.length > 0) {
    // Si no hay fecha seleccionada o no existe en los eventos, seleccionar la primera
    if (!state.selectedDate || !eventDates.includes(state.selectedDate)) {
      state.selectedDate = eventDates[0];
    }

    // Calcular rango abarcando desde el primer hasta el último día del evento/grupo (+ 1 día de margen a cada lado)
    const [minY, minM, minD] = eventDates[0].split('-').map(Number);
    const [maxY, maxM, maxD] = eventDates[eventDates.length - 1].split('-').map(Number);

    const startObj = new Date(minY, minM - 1, minD);
    startObj.setDate(startObj.getDate() - 1);

    const endObj = new Date(maxY, maxM - 1, maxD);
    endObj.setDate(endObj.getDate() + 1);

    const curObj = new Date(startObj);
    while (curObj <= endObj) {
      daysToShow.push(new Date(curObj));
      curObj.setDate(curObj.getDate() + 1);
    }
  } else {
    // Si no hay eventos, mostrar ventana alrededor de hoy
    const today = new Date();
    for (let i = -2; i <= 5; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      daysToShow.push(d);
    }
  }

  daysToShow.forEach(dateObj => {
    const key = formatDateKey(dateObj);
    const dayName = dayNames[dateObj.getDay()];
    const dayNum = dateObj.getDate();
    
    const count = state.events.filter(e => e.date === key).length;
    const isActive = key === state.selectedDate;

    // Detectar si este día pertenece a un evento multi-día
    const multiEvt = state.events.find(e => e.date === key && e.multi_day && e.multi_day.is_multi_day);
    const multiBadge = multiEvt ? `
      <span class="pill-multiday-badge" title="${multiEvt.multi_day.group_name} (${multiEvt.multi_day.day_label})">
        ${multiEvt.multi_day.day_label}
      </span>
    ` : '';

    const pill = document.createElement('div');
    pill.className = `day-pill ${isActive ? 'active' : ''} ${multiEvt ? 'has-multiday' : ''}`;
    pill.innerHTML = `
      <span class="day-name">${dayName}</span>
      <span class="day-number">${dayNum}</span>
      <span class="event-indicator">${count} ${count === 1 ? 'evento' : 'eventos'}</span>
      ${multiBadge}
    `;

    pill.addEventListener('click', () => {
      state.selectedDate = key;
      renderTimeline();
      renderCards();
    });

    slider.appendChild(pill);

    // Si es la píldora activa, centrarla en la vista del slider
    if (isActive) {
      setTimeout(() => {
        pill.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }, 50);
    }
  });
}

export function changeDay(delta) {
  if (!state.selectedDate) return;
  const [y, m, d] = state.selectedDate.split('-').map(Number);
  const cur = new Date(y, m - 1, d);
  cur.setDate(cur.getDate() + delta);
  state.selectedDate = formatDateKey(cur);

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

export function setupTimelineControls() {
  const prevBtn = document.getElementById('prevDayBtn');
  const nextBtn = document.getElementById('nextDayBtn');
  if (prevBtn) prevBtn.addEventListener('click', () => changeDay(-1));
  if (nextBtn) nextBtn.addEventListener('click', () => changeDay(1));
}
