/**
 * ME_VENTS - Day Timeline Module (Multi-day & Adaptive Calendar)
 */

import { state, formatDateKey, pickDefaultDate, todayKey } from './state.js';
import { renderCards } from './cards.js';

// La tira empieza en hoy; los días pasados solo se ven con el botón. No se guarda: cada vez que se abre, hoy.
let showPast = false;
let scrollToStart = false;

function keyToDate(key) {
  const [y, m, d] = key.split('-').map(Number);
  return new Date(y, m - 1, d);
}

function pastToggle(label, onClick) {
  const pill = document.createElement('div');
  pill.className = 'day-pill past-toggle';
  pill.innerHTML = `<span class="past-toggle-icon">🕘</span><span class="past-toggle-label">${label}</span>`;
  pill.addEventListener('click', () => {
    onClick();
    renderTimeline();
  });
  return pill;
}

export function renderTimeline() {
  const slider = document.getElementById('daysSlider');
  if (!slider) return;
  slider.innerHTML = '';

  const dayNames = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
  const daysToShow = [];
  let hiddenPastDays = 0;
  let pastEventDays = 0;

  // Recoger todas las fechas de eventos registrados
  const eventDates = [...new Set(state.events.map(e => e.date).filter(Boolean))].sort();

  if (eventDates.length > 0) {
    // Si no hay fecha seleccionada o no existe en los eventos, seleccionar hoy / el próximo día con eventos
    if (!state.selectedDate || !eventDates.includes(state.selectedDate)) {
      state.selectedDate = pickDefaultDate(eventDates);
    }

    // Rango: del primer al último día con eventos (+ 1 día de margen a cada lado). Sin el botón, desde hoy
    // (o desde el día elegido, si se ha ido hacia atrás con las flechas).
    const today = todayKey();
    const from = state.selectedDate < today ? state.selectedDate : today;
    pastEventDays = eventDates.filter(d => d < today).length;

    const startObj = keyToDate(eventDates[0]);
    startObj.setDate(startObj.getDate() - 1);
    if (!showPast && formatDateKey(startObj) < from) {
      startObj.setTime(keyToDate(from).getTime());
      hiddenPastDays = eventDates.filter(d => d < from).length;
    }

    const endObj = keyToDate(eventDates[eventDates.length - 1]);
    endObj.setDate(endObj.getDate() + 1);
    if (endObj < startObj) endObj.setTime(startObj.getTime());

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

  if (hiddenPastDays > 0) {
    slider.appendChild(pastToggle(
      `Ver ${hiddenPastDays} ${hiddenPastDays === 1 ? 'día pasado' : 'días pasados'}`,
      () => { showPast = true; scrollToStart = true; }
    ));
  } else if (showPast && pastEventDays > 0) {
    slider.appendChild(pastToggle('Ocultar pasados', () => {
      showPast = false;
      if (state.selectedDate < todayKey()) {
        state.selectedDate = pickDefaultDate([...new Set(state.events.map(e => e.date).filter(Boolean))].sort());
        renderCards();
      }
    }));
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

    // Si es la píldora activa, centrarla en la vista del slider (salvo recién abiertos los pasados: se ve el principio)
    if (isActive && !scrollToStart) {
      setTimeout(() => {
        pill.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }, 50);
    }
  });

  if (scrollToStart) {
    scrollToStart = false;
    setTimeout(() => slider.scrollTo({ left: 0, behavior: 'smooth' }), 50);
  }
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
