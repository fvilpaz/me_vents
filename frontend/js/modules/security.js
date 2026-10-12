/**
 * ME_VENTS - Security & Sanitization Utilities
 * Defense-in-depth against XSS, HTML injection and malformed inputs
 */

export function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

export function sanitizeInput(str, maxLength = 250) {
  if (!str) return '';
  return String(str)
    .trim()
    .slice(0, maxLength);
}
