/**
 * ME_VENTS - Main Application Orchestrator (ES Module)
 * Brand Identity: ME by Meliá Málaga
 */

import { initDate, loadEventsFromStorage, syncWithBackend } from './modules/state.js';
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
  setupTimelineControls();
  setupFilterControls();
  setupTouchGestures();
  setupUploaderListeners();
  
  // Renderizar vistas
  renderTimeline();
  renderCards();
  
  // Inicializar Glosario
  await initGlossary();
});
