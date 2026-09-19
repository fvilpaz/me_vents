/**
 * ME_VENTS - Main Application Orchestrator (ES Module)
 * Brand Identity: ME by Meliá Málaga
 */

import { initDate, loadEventsFromStorage, syncWithBackend, clearAllEvents } from './modules/state.js';
import { renderTimeline, setupTimelineControls } from './modules/timeline.js';
import { renderCards, setupFilterControls } from './modules/cards.js';
import { setupTouchGestures } from './modules/gestures.js';
import { setupUploaderListeners } from './modules/uploader.js';
import { initGlossary } from './modules/glossary.js';

// Inicialización de la App al cargar el DOM
document.addEventListener('DOMContentLoaded', async () => {
  initDate();
  loadEventsFromStorage();
  await syncWithBackend();
  
  // Inicializar componentes modulares
  setupThemeToggle();
  setupTimelineControls();
  setupFilterControls();
  setupTouchGestures();
  setupUploaderListeners();
  
  // Botón Limpiar
  const clearBtn = document.getElementById('clearAllBtn');
  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (confirm('¿Deseas limpiar todos los eventos de la agenda para empezar de cero?')) {
        await clearAllEvents();
        renderTimeline();
        renderCards();
      }
    });
  }

  // Renderizar vistas
  renderTimeline();
  renderCards();
  
  // Inicializar Glosario
  await initGlossary();
});

/**
 * Control del selector de tema (Claro / Oscuro)
 * Oscuro por defecto; persiste la elección en localStorage
 */
function setupThemeToggle() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('me_vents_theme', newTheme);
    // La barra del navegador del móvil sigue el color del cabecero (oscuro / azul del tema claro)
    const themeColor = document.querySelector('meta[name="theme-color"]');
    if (themeColor) themeColor.setAttribute('content', newTheme === 'light' ? '#0284c7' : '#080b11');
  });
}
