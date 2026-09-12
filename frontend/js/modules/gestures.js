/**
 * ME_VENTS - Touch Gestures & Swipe Detection Module (Bulletproof)
 */

import { changeDay } from './timeline.js';

export function setupTouchGestures() {
  const container = document.getElementById('swipeContainer');
  if (!container) return;

  let startX = 0;
  let startY = 0;
  let currentX = 0;
  let currentY = 0;
  let isSwiping = false;

  container.addEventListener('touchstart', (e) => {
    // Si el usuario toca dentro de un botón, input o dentro del acordeón operativo, NO iniciar swipe
    if (e.target.closest('button') || e.target.closest('input') || e.target.closest('.accordion-body') || e.target.closest('.accordion-toggle')) {
      isSwiping = false;
      return;
    }

    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    currentX = startX;
    currentY = startY;
    isSwiping = true;
  }, { passive: true });

  container.addEventListener('touchmove', (e) => {
    if (!isSwiping) return;
    currentX = e.touches[0].clientX;
    currentY = e.touches[0].clientY;
  }, { passive: true });

  container.addEventListener('touchend', () => {
    if (!isSwiping) return;
    isSwiping = false;

    const deltaX = currentX - startX;
    const deltaY = currentY - startY;

    // Solo considerar swipe si fue predominantemente HORIZONTAL y significativo
    // (al menos 75px en X y el doble que el desplazamiento en Y para no confundir con scroll vertical)
    if (Math.abs(deltaX) > 75 && Math.abs(deltaX) > Math.abs(deltaY) * 1.8) {
      if (deltaX > 0) {
        changeDay(-1); // Hacia la derecha: día anterior
      } else {
        changeDay(1);  // Hacia la izquierda: día siguiente
      }
    }
  });
}
