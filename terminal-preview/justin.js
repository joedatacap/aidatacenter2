/* Dated editions of Justin's public research. The build validates records and sources. */
(() => {
  'use strict';
  function escape(value) {
    return String(value).replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[character]);
  }
  let activeContext;
  const money = value => '$' + value.toFixed(2);
  const change = value => (value > 0 ? '+' : '') + value.toFixed(1) + '%';
  const date = value => new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC'
  }).format(new Date(value + 'T00:00:00Z'));
  function source(url, label) {
    return '<a href="' + escape(url) + '" target="_blank" rel="noopener noreferrer">' + escape(label) + '</a>';
  }
  function median(values) {
    const sorted = values.slice().sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
  }
  function cohortBlock(cohort, selected, report) {
    const rows = [...cohort.rows].sort((a, b) => b.return_pct - a.return_pct);
    const rank = rows.findIndex(row => row.id === selected.id) + 1;
    const others = rows.filter(row => row.id !== selected.id);
    const benchmark = median(others.map(row => row.return_pct));
    const spread = selected.return_pct - benchmark;
    const multiple = row => row.ps === null ? 'Unreconciled' : row.ps.toFixed(2) + '×';
    const content = rows.map(row => {
      const ticker = row.id.toUpperCase();
      return `<tr ${row.id === selected.id ? 'class="justin-selected" aria-current="true"' : ''}>
        <th scope="row">${escape(ticker)}</th><td>${escape(row.group)}</td>
        <td>${source(row.source_url, change(row.return_pct))}</td>
        <td>${source(row.valuation_url, multiple(row))}</td></tr>`;
    }).join('');
    const qualifications = rows.map(row => '<p><strong>' + escape(row.id.toUpperCase()) +
      '</strong> ' + escape(row.ps_basis) + '</p>').join('');
    return `<section class="justin-peers" aria-label="Peer comparison">
      <h2>Against the cohort</h2><p><strong>${escape(selected.id.toUpperCase())} ranks ${rank} of ${rows.length}</strong> over five sessions.
      Its ${change(selected.return_pct)} return was ${Math.abs(spread).toFixed(1)} percentage points ${spread >= 0 ? 'above' : 'below'} the other eight’s median (${change(benchmark)}).</p>
      <p>${escape(report.peer_read)}</p><div class="justin-scroll"><table><caption>${date(cohort.prior_as_of)} to ${date(cohort.as_of)} · USD closing prices</caption>
      <thead><tr><th>Ticker</th><th>Business</th><th>5-session return</th><th>Trailing P/S</th></tr></thead>
      <tbody>${content}</tbody></table></div>
      <p class="small">P/S compares equity value with trailing sales. Debt, preferred claims and margins differ across operators, landlords and miners.</p>
      <details><summary>Peer sources and valuation gaps</summary>${qualifications}</details></section>`;
  }
  function reportPage(ctx, report, company, peer) {
    const objective = report.objective;
    const risk = report.invalidation;
    const rewardRisk = (objective.price - objective.trigger) / (objective.trigger - risk.price);
    const nav = ctx.justin.reports.map(item => {
      const current = item.id === report.id ? ' aria-current="page"' : '';
      return '<a data-app href="#/justin/' + escape(item.id) + '"' + current + '>' + escape(item.id.toUpperCase()) + '</a>';
    }).join('');
    const signalItems = report.signals.map((signal, i) =>
      '<li>' + escape(signal.text) + ' ' + source(signal.url, '[' + (i + 1) + ']') + '</li>').join('');
    const gaps = report.gaps.map(gap =>
      '<li><strong>' + escape(gap.input) + '</strong> ' + escape(gap.source) + '</li>').join('');
    const evidence = report.sources.map(record => '<li>' + source(record.url, record.title) + '</li>').join('');
    const fullSheet = DecisionSheets.render(ctx).replace('<h1 id="page-title">', '<h2>').replace('</h1>', '</h2>');
    return `<article class="justin-report" data-justin-report="${escape(report.id)}">
      <header class="justin-byline"><span><strong>Justin</strong> <span>AI research analyst</span></span>
      <time datetime="${report.as_of}">${date(report.as_of)}</time></header>
      <nav class="decision-tabs justin-tabs" aria-label="Analyst coverage">${nav}</nav>
      <section class="justin-call">
        <div class="justin-callhead"><h1 id="page-title">${escape(company.name)}</h1><span>30–90 day outlook</span></div>
        <p class="justin-verdict"><strong>${escape(report.rating)}</strong> existing shares <span>·</span> <strong>${escape(report.new_money)}</strong> on a new position</p>
        <p class="justin-thesis">${escape(report.thesis)}</p>
        <dl class="justin-prices">
          <div><dt>${date(ctx.justin.cohort.as_of).split(',')[0]} close</dt><dd>${money(peer.close)}</dd></div>
          <div><dt>Conditional objective</dt><dd>${money(objective.price)}</dd></div>
          <div><dt>Reassess ${risk.price < objective.price ? 'below' : 'above'}</dt><dd>${money(risk.price)}</dd></div>
        </dl>
        <p><b>What activates it?</b> ${escape(objective.condition)}</p>
        <p class="justin-odds">At ${money(objective.trigger)}, distance to the objective is ${money(Math.abs(objective.price - objective.trigger))} versus
        ${money(Math.abs(objective.trigger - risk.price))} to the review level (${rewardRisk.toFixed(2)} to 1 before costs).</p>
        <button type="button" data-save-justin="${escape(report.id)}">Save Justin’s call</button><span id="decision-status" role="status"></span>
      </section>
      <div class="justin-columns"><section><h2>Three signals</h2><ul class="justin-signals">${signalItems}</ul></section>
      <section class="justin-next"><h2>Next checkpoint</h2><strong>${date(report.catalyst.date)}</strong><p>${escape(report.catalyst.event)}</p>
      <p><b>Conviction</b> · ${escape(report.confidence)}</p></section></div>
      <details class="justin-details"><summary>How Justin set the price and what would change it</summary>
      <p>${escape(objective.method)} ${escape(risk.reason)}</p>
      <p>These tactical levels are analyst judgments from price history. Their hit rate has yet to be measured.</p>
      <h3>Evidence Justin needs</h3><ul>${gaps}</ul><ul class="justin-sources">${evidence}</ul></details>
      ${cohortBlock(ctx.justin.cohort, peer, report)}
      <details class="justin-model"><summary>Full decision sheet and calculators</summary>${fullSheet}</details>
    </article>`;
  }
  function render(ctx) {
    activeContext = ctx;
    const data = ctx.justin;
    const id = ctx.state.company || 'crwv';
    const report = data?.reports?.find(item => item.id === id);
    const company = ctx.companies.find(item => item.id === id);
    const peer = data?.cohort?.rows?.find(item => item.id === id);
    if (!report || !company || !peer) return '<h1 id="page-title">Justin research</h1><p>No reviewed report is available for this company.</p>';
    return reportPage(ctx, report, company, peer);
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-save-justin]');
    if (button && activeContext) DecisionWorkspace.saveJustinCall(button.dataset.saveJustin, activeContext);
  });
  window.Justin = {render};
})();
