/**
 * ME_VENTS - Touch Gestures & Swipe Detection Module
 */

import { changeDay } from './timeline.js';

export function setupTouchGestures() {
  const container = document.getElementById('swipeContainer');
  if (!container) return;

  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let isSwiping = false;

  container.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    isSwiping = true;
  }, { passive: true });

  container.addEventListener('touchmove', (e) => {
    if (!isSwiping) return;
    currentX = e.touches[0].clientX;
  }, { passive: true });

  container.addEventListener('touchend', () => {
    if (!isSwiping) return;
    isSwiping = false;
    const deltaX = currentX - startX;
    
    // Si el deslizamiento horizontal fue de más de 60px
    if (Math.abs(deltaX) > 60) {
      if (deltaX > 0) {
        changeDay(-1); // Hacia la derecha: día anterior
      } else {
        changeDay(1);  // Hacia la izquierda: día siguiente
      }
    }
  });
}
