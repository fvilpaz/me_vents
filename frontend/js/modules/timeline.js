/**
 * ME_VENTS - Day Timeline Module
 */

import { state, formatDateKey } from './state.js';
import { renderCards } from './cards.js';

export function renderTimeline() {
  const slider = document.getElementById('daysSlider');
  if (!slider) return;
  slider.innerHTML = '';

  const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
  const today = new Date();
  const daysToShow = [];
  
  for (let i = -2; i <= 5; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    daysToShow.push(d);
  }

  daysToShow.forEach(dateObj => {
    const key = formatDateKey(dateObj);
    const dayName = dayNames[dateObj.getDay()];
    const dayNum = dateObj.getDate();
    
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

export function changeDay(delta) {
  const cur = new Date(state.selectedDate);
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
