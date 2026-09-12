import { escapeHTML, sanitizeInput } from './security.js';

export const glossaryState = {
  terms: [],
  categories: [],
  activeCategory: 'all',
  searchQuery: ''
};

export async function initGlossary() {
  await loadGlossaryData();
  setupGlossaryListeners();
  renderGlossaryTerms();
}

export async function loadGlossaryData() {
  try {
    const res = await fetch('/api/glossary');
    if (res.ok) {
      const data = await res.json();
      glossaryState.terms = data.terms || [];
      glossaryState.categories = data.categories || [];
      return;
    }
  } catch (err) {
    // Backend no disponible (GitHub Pages)
  }

  try {
    const staticRes = await fetch('./data/jargon_dictionary.json');
    if (staticRes.ok) {
      const data = await staticRes.json();
      glossaryState.terms = data.terms || [];
      glossaryState.categories = data.categories || [];
    }
  } catch (e) {
    console.log('Glosario offline no disponible');
  }
}

export function setupGlossaryListeners() {
  const openBtn = document.getElementById('openGlossaryBtn');
  const closeBtn = document.getElementById('closeGlossaryBtn');
  const modal = document.getElementById('glossaryModal');
  const searchInput = document.getElementById('glossarySearchInput');
  const toggleFormBtn = document.getElementById('toggleAddTermForm');
  const newTermForm = document.getElementById('newTermForm');

  if (openBtn && modal) {
    openBtn.addEventListener('click', () => modal.classList.add('open'));
  }
  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => modal.classList.remove('open'));
  }
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.remove('open');
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      glossaryState.searchQuery = e.target.value.toLowerCase().trim();
      renderGlossaryTerms();
    });
  }

  document.querySelectorAll('#glossaryCategoryPills .filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('#glossaryCategoryPills .filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      glossaryState.activeCategory = chip.getAttribute('data-cat');
      renderGlossaryTerms();
    });
  });

  if (toggleFormBtn && newTermForm) {
    toggleFormBtn.addEventListener('click', () => {
      newTermForm.classList.toggle('open');
      toggleFormBtn.querySelector('.acc-icon').textContent = newTermForm.classList.contains('open') ? '▲' : '▼';
    });
  }

  if (newTermForm) {
    newTermForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const termName = sanitizeInput(document.getElementById('newTermName')?.value, 80);
      const category = sanitizeInput(document.getElementById('newTermCategory')?.value, 30);
      const aliasesStr = sanitizeInput(document.getElementById('newTermAliases')?.value, 200);
      const definition = sanitizeInput(document.getElementById('newTermDefinition')?.value, 500);
      const tip = sanitizeInput(document.getElementById('newTermTip')?.value, 300);

      if (!termName || !definition) return;

      const aliases = aliasesStr ? aliasesStr.split(',').map(s => s.trim().toLowerCase()).filter(Boolean) : [termName.toLowerCase()];
      if (!aliases.includes(termName.toLowerCase())) {
        aliases.unshift(termName.toLowerCase());
      }

      const newTerm = {
        id: termName.toLowerCase().replace(/[^a-z0-9]/g, '-'),
        term: termName,
        category: category,
        aliases: aliases,
        definition: definition,
        operational_tip: tip || null,
        icon: category === 'montajes' ? '🧲' : (category === 'fb' ? '☕' : (category === 'av_equipamiento' ? '📺' : '✨'))
      };

      try {
        await fetch('/api/glossary', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newTerm)
        });
      } catch (err) {
        console.log('Guardado local de término.');
      }

      glossaryState.terms.push(newTerm);
      renderGlossaryTerms();
      newTermForm.reset();
      newTermForm.classList.remove('open');
      if (toggleFormBtn) toggleFormBtn.querySelector('.acc-icon').textContent = '▼';
      alert(`✨ Término "${termName}" añadido correctamente al Glosario de Me_vents.`);
    });
  }
}

export function renderGlossaryTerms() {
  const container = document.getElementById('glossaryTermsContainer');
  if (!container) return;

  let list = glossaryState.terms;

  if (glossaryState.activeCategory !== 'all') {
    list = list.filter(t => t.category === glossaryState.activeCategory);
  }

  if (glossaryState.searchQuery) {
    const q = glossaryState.searchQuery;
    list = list.filter(t => 
      t.term.toLowerCase().includes(q) ||
      t.definition.toLowerCase().includes(q) ||
      (t.aliases && t.aliases.some(a => a.toLowerCase().includes(q))) ||
      (t.operational_tip && t.operational_tip.toLowerCase().includes(q))
    );
  }

  if (list.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.9rem;">
        🔍 No se encontraron términos que coincidan con la búsqueda. Puedes añadirlo abajo en el formulario.
      </div>
    `;
    return;
  }

  const categoryLabels = {
    montajes: "🧲 Montajes de Sala",
    fb: "☕ Alimentos & Bebidas (F&B)",
    av_equipamiento: "📺 Audiovisuales & Técnica",
    mobiliario_menaje: "🪑 Mobiliario & Material",
    protocolo_hotel: "🏨 Protocolo Opera"
  };

  container.innerHTML = list.map(t => `
    <div class="glossary-card">
      <div class="glossary-card-header">
        <div class="glossary-term-title">
          <span>${t.icon || '✨'}</span> ${escapeHTML(t.term)}
        </div>
        <span class="glossary-cat-badge">${escapeHTML(categoryLabels[t.category] || t.category)}</span>
      </div>

      ${t.aliases && t.aliases.length > 0 ? `
        <div class="glossary-aliases-row">
          <span class="alias-label">Abreviaturas / Jerga:</span>
          ${t.aliases.map(a => `<span class="alias-chip">${escapeHTML(a)}</span>`).join('')}
        </div>
      ` : ''}

      <div class="glossary-definition">${escapeHTML(t.definition)}</div>

      ${t.operational_tip ? `
        <div class="glossary-tip-box">
          <span>💡</span>
          <span><strong>Regla de Sala:</strong> ${escapeHTML(t.operational_tip)}</span>
        </div>
      ` : ''}
    </div>
  `).join('');
}
