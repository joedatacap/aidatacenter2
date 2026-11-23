// Use the accepted editorial observation. The historical debt denominator has its own date and scope.
function capObservationDay(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(value + 'T00:00:00Z');
  return Number.isFinite(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function capPlotOmission(company, cap) {
  if (!cap?.updated || !cap.eligible || !(company.size_observation.value_usd > 0)) {
    return 'No eligible market-cap observation.';
  }
  if (cap.source_values_disagree) return 'Sources disagree on the value.';
  if (cap.currency !== 'USD') return 'USD capitalization unavailable.';
  if (!capObservationDay(company.size_observation.as_of) || !capObservationDay(cap.source_date) || !safeURL(cap.source_url)?.startsWith('https://')) return 'A dated public source is unavailable.';
  return '';
}

function capPlotRow({company, cap}, maximum, sharedDate) {
  const group = tradingViewSizeName(company);
  const amount = money(cap.value, true);
  const shareNote = cap.qualification_label;
  const qualification = shareNote?.toLowerCase() === 'share basis unresolved'
    ? 'Provider-reported; share basis unresolved.' : shareNote;
  return `<li class="cap-row" data-cap-company="${esc(company.id)}" data-cap-date="${esc(cap.as_of)}">
    <div class="cap-identity">
      <a data-app data-cap-profile aria-label="${esc(company.name)} (${esc(company.ticker)}), company profile" href="${esc(profile(company))}"><strong>${esc(company.ticker)}</strong><span>${esc(company.name)}</span></a>
      <span class="cap-badge cap-${group.toLowerCase()}">${esc(group)}</span>
    </div>
    <div class="cap-track" data-cap-track aria-hidden="true"><span data-cap-bar class="cap-fill cap-${group.toLowerCase()}" style="width:${100 * cap.value / maximum}%"></span></div>
    <a class="cap-amount" data-cap-value href="${esc(cap.source_url)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(company.ticker)} ${amount} USD, capitalization source">${amount}</a>
    ${!sharedDate || qualification ? `<small class="cap-note">${!sharedDate ? sizeObservationDate(cap) : ''}${!sharedDate && qualification ? ' · ' : ''}${esc(qualification || '')}</small>` : ''}
  </li>`;
}

function marketCapChart(companies) {
  const plotted = [], omitted = [];
  for (const company of companies) {
    const cap = displaySizeObservation(company);
    const reason = capPlotOmission(company, cap);
    if (reason) omitted.push(`<li data-cap-omitted="${esc(company.id)}"><a data-app href="${esc(profile(company))}">${esc(company.ticker)}</a> · ${esc(reason)}</li>`);
    else plotted.push({company, cap});
  }
  plotted.sort((a, b) => b.cap.value - a.cap.value || a.company.ticker.localeCompare(b.company.ticker));
  const first = plotted[0]?.cap;
  const sharedDate = first && plotted.every(({cap}) => cap.as_of === first.as_of && cap.session_status === first.session_status);
  const stockAnalysis = plotted.length > 0 && plotted.every(({cap}) =>
    cap.status === 'provider_reported' && new URL(cap.source_url).hostname === 'stockanalysis.com'
  );
  const groups = [['all','All sizes'], ['small','Small'], ['mid','Mid'], ['large','Large']];
  const buttons = groups.map(([id,label]) =>
    `<button type="button" data-cap-group="${id}" aria-pressed="${state.size === id}">${label}</button>`
  ).join('');
  let plot = '<p class="cap-empty">No eligible market caps in this selection.</p>';
  if (first) {
    const step = 10 ** Math.floor(Math.log10(first.value));
    const maximum = Math.ceil(first.value / step) * step;
    plot = `<div class="cap-plot" data-cap-max="${maximum}">
      <div class="cap-axis" aria-hidden="true"><span>Company / size</span>
        <div class="cap-ticks"><span>$0</span><span>${money(maximum / 2)}</span><span>${money(maximum)}</span></div>
        <span>Market cap (USD)</span></div>
      <ol aria-label="Market caps, largest to smallest">${plotted.map(row => capPlotRow(row, maximum, sharedDate)).join('')}</ol>
    </div>`;
  }
  return `<section id="market-cap-chart" class="cap-chart" aria-labelledby="page-title">
    <div class="cap-heading"><h1 id="page-title">Market capitalization</h1><div id="tradingview-peer-slot"></div></div>
    <p class="cap-source">${stockAnalysis ? 'Provider-reported USD values · Stock Analysis' : 'USD market-cap observations'}${sharedDate ? ' · '+sizeObservationDate(first) : ''}</p>
    <p class="cap-timing">${!sharedDate && plotted.length ? 'Dates appear beside each observation. ' : ''}Source figures are rounded. Exact valuation times are unavailable.</p>
    <div class="cap-toolbar"><div class="cap-groups" role="group" aria-label="Filter by company size">${buttons}</div>
      <span>Linear scale from $0</span></div>
    ${plot}
    ${omitted.length ? `<div class="cap-omissions"><strong>Excluded from chart</strong><ul>${omitted.join('')}</ul></div>` : ''}
  </section>`;
}
