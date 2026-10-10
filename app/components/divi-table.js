class DiviTable extends HTMLElement {
  connectedCallback() {
    const idPrefix = this.getAttribute('id-prefix') || 'table';
    const legendText = this.getAttribute('legend') || '';
    const legendColor = this.getAttribute('legend-color') || '#facc15';
    const legendKeyAttr = this.getAttribute('legend-key') || '';

    const texts = legendText ? legendText.split(',').map(s => s.trim()).filter(Boolean) : [];
    const colors = legendColor ? legendColor.split(',').map(s => s.trim()).filter(Boolean) : ['#facc15'];
    const keys = legendKeyAttr ? legendKeyAttr.split(',').map(s => s.trim()).filter(Boolean) : [];
    const hasLegend = texts.length > 0;

    const legendItemsHtml = texts.map((text, idx) => {
      const color = colors[idx] || colors[colors.length - 1] || '#facc15';
      const key = keys[idx] || `idx-${idx}`;
      return `
        <div class="legend-item" data-legend-key="${key}" data-legend-index="${idx}" style="display: flex; align-items: center; gap: 8px;">
          <span style="display: inline-block; width: 14px; height: 14px; background: ${color}; border-radius: 2px; flex-shrink: 0;"></span>
          <span>${text}</span>
        </div>
      `;
    }).join('');

    this.innerHTML = `
      <div class="table-container ${hasLegend ? 'has-legend' : ''}">
        <div class="table-legend" style="${hasLegend ? '' : 'display:none;'} display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
          ${legendItemsHtml}
        </div>
        <table>
          <thead>
            <tr id="${idPrefix}-header"></tr>
          </thead>
          <tbody id="${idPrefix}-body">
            <tr><td class="loading">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    `;

    this.updateStickyHeader();
  }

  updateStickyHeader() {
    const legendItems = this.querySelectorAll('.legend-item');
    if (legendItems.length === 0) return;

    legendItems.forEach(item => {
      const key = item.getAttribute('data-legend-key');
      const idx = item.getAttribute('data-legend-index');

      const matches = this.querySelectorAll(
        `tbody [data-legend-key~="${key}"], tbody [data-legend-key="${key}"], tbody [data-legend-index="${idx}"]`
      );
      const count = matches.length;

      item.style.display = count > 0 ? 'flex' : 'none';
    });
  }
}

customElements.define('divi-table', DiviTable);
