class DiviTable extends HTMLElement {
  connectedCallback() {
    const idPrefix = this.getAttribute('id-prefix') || 'table';
    const legendText = this.getAttribute('legend') || '';
    const legendColor = this.getAttribute('legend-color') || '#facc15';
    const hasLegend = Boolean(legendText);

    this.innerHTML = `
      <div class="table-container ${hasLegend ? 'has-legend' : ''}">
        <div class="table-legend" style="${hasLegend ? '' : 'display:none;'}">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 14px; height: 14px; background: ${legendColor}; border-radius: 2px; flex-shrink: 0;"></span>
            <span id="${idPrefix}-legend-text">${legendText}</span>
          </div>
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
  }

  updateStickyHeader() {}
}

customElements.define('divi-table', DiviTable);
