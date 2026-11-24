/* Standalone evidence terminal. Historical availability follows disclosure dates. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[character]));
  const list = value => Array.isArray(value) ? value : [];
  const text = value => value === null || value === undefined || value === '' ? 'Unavailable' : String(value);
  const human = value => text(value).replaceAll('_', ' ');
  const kinds = [
    ['revenue', 'Revenue'], ['cash', 'Cash & restrictions'], ['debt', 'Debt structure'],
    ['financing', 'Financing terms'], ['commitments', 'Commitments'], ['capacity', 'Capacity & delivery'],
    ['concentration', 'Customer concentration'], ['guidance', 'Guidance'], ['earnings', 'Earnings & cash generation']
  ];
  const viewNames = {
    compare: 'Compare companies', companies: 'Company briefs',
    history: 'Commitment history', changes: 'Material changes'
  };
  let companies = [], state, latestReview = '', dataError = '';

  function safeURL(value) {
    try {
      const parsed = new URL(value);
      return ['https:', 'http:'].includes(parsed.protocol) ? parsed.href : null;
    } catch { return null; }
  }

  function date(value) {
    return value ? escape(String(value).slice(0, 10)) : 'Date unavailable';
  }

  function readState() {
    const raw = location.hash.slice(1) || '/compare';
    const [path, query = ''] = raw.split('?');
    const parts = path.split('/').filter(Boolean), params = new URLSearchParams(query);
    return {
      view: viewNames[parts[0]] ? parts[0] : 'compare',
      company: parts[1] || '',
      peers: params.has('peers') ? params.get('peers').split(',').filter(id => companies.some(company => company.id === id)) : companies.map(company => company.id),
      q: params.get('q') || '', asof: params.get('asof') || '',
      type: params.get('type') || 'all', from: params.get('from') || '', to: params.get('to') || ''
    };
  }

  function href(view, changes = {}) {
    const next = {...state, ...changes}, params = new URLSearchParams();
    if (next.peers.length !== companies.length || companies.some(company => !next.peers.includes(company.id))) {
      params.set('peers', next.peers.length ? next.peers.join(',') : 'none');
    }
    for (const key of ['q', 'asof', 'from', 'to']) if (next[key]) params.set(key, next[key]);
    if (next.type && next.type !== 'all') params.set('type', next.type);
    const path = view === 'companies' && next.company ? '/companies/' + encodeURIComponent(next.company) : '/' + view;
    return '#' + path + (params.size ? '?' + params.toString() : '');
  }

  function navigate(view, changes = {}, replace = false) {
    history[replace ? 'replaceState' : 'pushState']({}, '', href(view, changes));
    render();
  }

  function profile(company) { return href('companies', {company: company.id}); }
  function matches(value) { return !state.q || String(value).toLowerCase().includes(state.q.toLowerCase().trim()); }
  function selectedCompanies() { return companies.filter(company => state.peers.includes(company.id)); }
  function companyMatches(company) {
    return matches([company.name, company.ticker, company.role, company.overview,
      ...list(company.facts).flatMap(fact => [fact.label, fact.value, fact.definition, fact.scope])
    ].join(' '));
  }

  function sourceKey(reference) {
    return typeof reference === 'string' ? reference : reference?.id || reference?.source_id || reference?.url || '';
  }

  function sourceRecord(company, reference) {
    const key = sourceKey(reference);
    return list(company.sources).find(source => source.id === key || source.url === key)
      || (reference && typeof reference === 'object' ? reference : null)
      || (safeURL(key) ? {url: key, title: 'Linked source'} : null);
  }

  function evidence(company, reference, factId = '', label = 'Source & definition') {
    const key = sourceKey(reference);
    if (!key) return '<span class="unavailable">Source unavailable</span>';
    return '<button type="button" class="evidence-button" data-source-company="' + escape(company.id)
      + '" data-source="' + escape(key) + '" data-fact="' + escape(factId) + '">' + escape(label) + '</button>';
  }

  function unavailable(reason = 'No reviewed disclosure loaded.') {
    return '<div class="unavailable"><strong>Unavailable</strong><p>' + escape(reason) + '</p></div>';
  }

  function heading(title, description, historical = false) {
    return '<header class="page-heading"><div><h1 id="page-title">' + escape(title) + '</h1><p>' + escape(description) + '</p></div>'
      + (historical ? '<span class="scope-tag">' + (state.asof ? state.asof > latestReview
        ? 'Knowledge capped at review dates' : 'Knowledge as of ' + date(state.asof) : 'All reviewed disclosures') + '</span>' : '') + '</header>';
  }

  function latestNote() {
    return '<div class="reading-note"><div><strong>Latest-only comparison.</strong> Figures retain their own dates, units and scopes. '
      + 'Use Commitment history or Material changes to reconstruct disclosure availability.</div></div>';
  }

  function empty(message) {
    return '<section class="empty"><h2>No matching research</h2><p>' + escape(message)
      + '</p><button type="button" data-reset>Reset selection & filters</button></section>';
  }

  function factMarkup(company, fact, expanded = false) {
    const certainty = human(fact.basis), verification = human(fact.verification);
    return '<article class="fact-item" data-fact-id="' + escape(fact.id) + '">'
      + '<div class="fact-label">' + escape(text(fact.label)) + '</div>'
      + '<p class="fact-value">' + escape(text(fact.value)) + '</p>'
      + '<div class="fact-meta"><span>As of ' + date(fact.as_of) + '</span><span>' + escape(text(fact.unit)) + '</span></div>'
      + (expanded ? '<p class="fact-definition">' + escape(text(fact.definition)) + '</p>' : '')
      + '<div class="fact-meta"><span class="badge">' + escape(certainty) + '</span>'
      + (expanded && verification.length < 70 ? '<span class="badge'
        + (/unverified|incomplete|pending|partial|not /i.test(verification) ? ' caution' : '') + '">' + escape(verification) + '</span>' : '') + '</div>'
      + (expanded && verification.length >= 70 ? '<p class="small muted"><strong>Review</strong> ' + escape(verification) + '</p>' : '')
      + (expanded ? '<dl class="detail-grid"><div><dt>Period / observation</dt><dd>' + date(fact.as_of)
        + '</dd></div><div><dt>Scope</dt><dd>' + escape(text(fact.scope)) + '</dd></div>'
        + '<div><dt>Unit</dt><dd>' + escape(text(fact.unit)) + '</dd></div><div><dt>Definition</dt><dd>'
        + escape(text(fact.definition)) + '</dd></div></dl>'
        + (fact.formula ? '<p class="small"><strong>Formula</strong> ' + escape(fact.formula) + '</p>' : '')
        + (fact.inputs ? inputEvidence(company, fact) : '')
        : '<details class="fact-context"><summary>Definition, scope & review</summary><p>' + escape(text(fact.definition))
          + '</p><p><strong>Scope</strong> ' + escape(text(fact.scope)) + '</p><p><strong>Verification / review</strong> '
          + escape(verification) + '</p></details>')
      + evidence(company, fact.source, fact.id) + '</article>';
  }

  function inputEvidence(company, fact) {
    if (!list(fact.inputs).length) return '';
    return '<section class="input-evidence"><h4>Calculation inputs</h4><ul>' + fact.inputs.map(id => {
      const input = list(company.facts).find(item => item.id === id);
      return '<li>' + (input ? '<strong>' + escape(input.label) + '</strong> · ' + escape(text(input.value)) + ' ' + escape(text(input.unit))
        + '<br>' + evidence(company, input.source, input.id, 'Open input evidence') : 'Input evidence unavailable: ' + escape(id)) + '</li>';
    }).join('') + '</ul></section>';
  }

  function factGroups() {
    const extras = [...new Set(companies.flatMap(company => list(company.facts).map(fact => fact.kind)))].filter(kind => !kinds.some(([key]) => key === kind));
    return [...kinds, ...extras.map(kind => [kind, human(kind)])];
  }

  function factsFor(company, kind) {
    return list(company.facts).filter(fact => fact.kind === kind).slice().sort((a, b) =>
      Number(Boolean(b.primary)) - Number(Boolean(a.primary)) || String(b.as_of).localeCompare(String(a.as_of)));
  }

  function currentMilestone(company) {
    const milestones = list(company.milestones);
    return milestones.find(milestone => !milestone.outcome && /delivery|service|acceptance|capacity|provision/i.test(milestone.type))
      || milestones.find(milestone => !milestone.outcome) || milestones[0];
  }

  function latestChange(company) {
    return list(company.changes).slice().sort((a, b) => String(b.published).localeCompare(String(a.published)))[0];
  }

  function milestoneSummary(company) {
    const milestone = currentMilestone(company);
    if (!milestone) return unavailable('No next delivery milestone has been established.');
    const revision = list(milestone.revisions).slice().sort((a, b) => String(b.published).localeCompare(String(a.published)))[0] || milestone.original;
    const pastTarget = !milestone.outcome && revision?.target_end && revision.target_end < company.reviewed_at.slice(0, 10);
    return '<h4>' + escape(text(milestone.project)) + '</h4><p class="summary-value">' + escape(text(revision?.target)) + '</p>'
      + '<span class="badge caution">' + escape(pastTarget ? 'Past target; completion unverified' : human(milestone.status)) + '</span><p class="small muted">Target disclosed ' + date(revision?.published) + '</p>'
      + evidence(company, revision?.source, '', 'Target disclosure') + '<br><a data-app class="small" href="'
      + escape(href('history', {peers: [company.id]})) + '">Original, revisions & outcome</a>';
  }

  function changeSummary(company) {
    const change = latestChange(company);
    if (!change) return unavailable('No material change record has been reviewed.');
    return '<div class="fact-meta"><span class="badge">' + escape(human(change.type)) + '</span><span>Disclosed ' + date(change.published)
      + '</span></div><p class="summary-value">' + escape(text(change.after)) + '</p>' + evidence(company, change.source, '', 'Updated disclosure')
      + '<br><a data-app class="small" href="' + escape(href('changes', {peers: [company.id]})) + '">Read before / after</a>';
  }

  function overviewSize(company) {
    const size = company.size;
    if (!size) return unavailable('Size has not been verified.');
    return '<p class="summary-value">' + escape(text(size.label)) + '</p><p class="small muted">As of ' + date(size.as_of) + '</p>'
      + '<details class="fact-context"><summary>Size basis & share qualification</summary><p>' + escape(text(size.basis)) + '</p></details>'
      + evidence(company, size.source, '', 'Size evidence & qualification');
  }

  function comparePage() {
    const selected = selectedCompanies().filter(companyMatches);
    let content = heading('Company comparison',
      'Compare the funding, revenue and delivery disclosures behind each company. A reported figure is useful only with its definition and scope.')
      + latestNote();
    if (!selected.length) return content + empty('Select a company or broaden your search to restore the comparison.');
    const widths = Math.max(730, 168 + selected.length * 260);
    const columns = selected.map(company => '<th scope="col" data-company="' + escape(company.id) + '">'
      + '<span class="company-ticker">' + escape(company.ticker) + '</span><a data-app class="column-name" href="'
      + escape(profile(company)) + '">' + escape(company.name) + '</a><span class="company-role">' + escape(text(company.role)) + '</span></th>').join('');
    function contextRow(label, kind, renderer) {
      return '<tr><th scope="row">' + label + '</th>' + selected.map(company => '<td data-company="' + escape(company.id)
        + '" data-kind="' + kind + '">' + renderer(company) + '</td>').join('') + '</tr>';
    }
    const sizeRow = contextRow('Size & basis', 'size', overviewSize);
    const contextRows = contextRow('Next delivery milestone', 'next-milestone', milestoneSummary)
      + contextRow('Latest material change', 'latest-change', changeSummary)
      + contextRow('Diligence question', 'diligence', company => list(company.questions).length ? '<p class="diligence-question">' + escape(company.questions[0]) + '</p>' : unavailable('No specific diligence question loaded.'));
    const groupedRows = factGroups().map(([kind, label]) => ({kind, html: '<tr><th scope="row">' + escape(label) + '</th>' + selected.map(company => {
      const facts = factsFor(company, kind);
      return '<td data-company="' + escape(company.id) + '" data-kind="' + kind + '">'
        + (facts.length ? factMarkup(company, facts[0]) + (facts.length > 1
          ? '<details class="additional-facts"><summary>' + (facts.length - 1) + ' additional disclosure' + (facts.length > 2 ? 's' : '')
            + '</summary>' + facts.slice(1).map(fact => factMarkup(company, fact)).join('') + '</details>' : '') : unavailable()) + '</td>';
    }).join('') + '</tr>'}));
    const coreKinds = ['revenue', 'cash', 'debt'];
    const coreRows = groupedRows.filter(row => coreKinds.includes(row.kind)).map(row => row.html).join('');
    const remainingRows = groupedRows.filter(row => !coreKinds.includes(row.kind)).map(row => row.html).join('');
    content += '<div class="comparison-wrap" tabindex="0" role="region" aria-label="Scrollable company comparison">'
      + '<table class="comparison" style="min-width:' + widths + 'px"><caption>Selected company disclosures · scroll across to compare</caption>'
      + '<thead><tr><th scope="col">Metric & scope</th>' + columns + '</tr></thead><tbody>' + sizeRow + coreRows + contextRows + remainingRows + '</tbody></table></div>';
    return content;
  }

  function sizeContext(company) {
    const size = company.size;
    if (!size) return '<aside class="size-context"><span class="eyebrow">SIZE CONTEXT</span>' + unavailable('Size basis has not been established.') + '</aside>';
    const hasValue = size.value_usd !== null && size.value_usd !== undefined && Number.isFinite(Number(size.value_usd));
    return '<aside class="size-context"><span class="eyebrow">DATED SIZE CONTEXT</span><strong>' + escape(text(size.label)) + '</strong>'
      + (hasValue ? '<p>$' + Number(size.value_usd).toLocaleString('en-US', {maximumFractionDigits: 2}) + ' USD</p>' : '')
      + '<p>Observation ' + date(size.as_of) + '</p><p>' + escape(text(size.basis)) + '</p>'
      + evidence(company, size.source, '', 'Size source & qualification') + '</aside>';
  }

  function profilePage() {
    const selected = selectedCompanies();
    const company = companies.find(item => item.id === state.company) || (!state.company ? selected[0] : null);
    const switcher = '<nav class="company-switcher" aria-label="Company briefs">' + selected.map(item => '<a data-app href="' + escape(profile(item))
      + '"' + (item.id === company?.id ? ' aria-current="page"' : '') + '>' + escape(item.ticker) + '</a>').join('') + '</nav>';
    if (!company) return heading('Company briefs', 'Read the underlying definitions, disclosure evidence and open questions for each business.')
      + switcher + empty(state.company ? 'That company is not in the reviewed dataset.' : 'Select a company to open its brief.');
    const groups = factGroups().map(([kind, label]) => {
      const facts = factsFor(company, kind).filter(fact => matches([company.name, company.ticker, fact.label, fact.value, fact.definition, fact.scope].join(' ')));
      if (!facts.length && state.q) return '';
      return '<section class="profile-facts" data-kind="' + kind + '"><div class="section-title"><h2>' + label + '</h2><span>'
        + facts.length + ' reviewed record' + (facts.length === 1 ? '' : 's') + '</span></div>'
        + (facts.length ? '<div class="fact-grid">' + facts.map(fact => '<div class="fact-card">' + factMarkup(company, fact, true) + '</div>').join('') + '</div>'
          : '<div class="fact-card">' + unavailable() + '</div>') + '</section>';
    }).join('');
    return switcher + '<section class="profile-intro"><div><span class="eyebrow">' + escape(company.ticker) + ' / COMPANY BRIEF</span>'
      + '<h1 id="page-title">' + escape(company.name) + '</h1><p>' + escape(text(company.overview)) + '</p>'
      + '<div class="fact-meta"><span class="badge">' + escape(text(company.role)) + '</span><span>Reviewed ' + date(company.reviewed_at) + '</span></div>'
      + evidence(company, company.identity_source, '', 'Company identity & business source') + '</div>' + sizeContext(company) + '</section>'
      + latestNote() + '<div class="profile-highlights"><section class="fact-card"><h2>Latest material change</h2>' + changeSummary(company)
      + '</section><section class="fact-card"><h2>Delivery milestone</h2>' + milestoneSummary(company) + '</section></div>'
      + '<div class="profile-layout"><div>' + groups + '</div><aside class="profile-aside"><section class="questions"><h3>Questions to carry forward</h3>'
      + (list(company.questions).length ? '<ul>' + company.questions.map(question => '<li>' + escape(question) + '</li>').join('') + '</ul>'
        : '<p>No explicit research questions loaded. This does not establish complete coverage.</p>') + '</section>'
      + '<nav class="profile-crosslinks" aria-label="Continue company research"><a data-app href="' + escape(href('history', {peers: [company.id]}))
      + '">Trace commitments & revisions</a><a data-app href="' + escape(href('changes', {peers: [company.id]}))
      + '">Review before / after disclosures</a><a data-watch-link href="https://neocloud-watch.gpuchips.chatgpt.site/companies/'
      + encodeURIComponent(company.id) + '/" target="_blank" rel="noopener noreferrer">More markets & debt research ↗</a></nav></aside></div>';
  }

  function known(record) {
    return !!record?.published && (!state.asof || String(record.published).slice(0, 10) <= state.asof);
  }

  function milestoneMarkup(company, milestone) {
    const original = milestone.original;
    if (!known(original)) return '';
    const revisions = list(milestone.revisions).filter(known).sort((a, b) => String(a.published).localeCompare(String(b.published)));
    const outcome = known(milestone.outcome) ? milestone.outcome : null;
    const reviewDate = company.reviewed_at.slice(0, 10);
    const effectiveKnowledgeDate = state.asof && state.asof < reviewDate ? state.asof : reviewDate;
    const latestTarget = revisions.at(-1) || original;
    const pastTarget = !outcome && latestTarget.target_end && latestTarget.target_end < effectiveKnowledgeDate;
    const status = pastTarget ? 'Past target; completion unverified' : !state.asof && milestone.status ? human(milestone.status)
      : outcome ? 'Outcome disclosed' : revisions.length ? 'Target revised' : 'Original target disclosed';
    function stage(record, label, actual = false) {
      return '<li' + (actual ? ' class="actual"' : '') + '><span class="stage-label">' + label + ' · disclosed <time datetime="'
        + escape(record.published) + '">' + date(record.published) + '</time></span><strong>' + escape(text(actual ? record.description : record.target))
        + '</strong>' + evidence(company, record.source, '', 'View supporting disclosure') + '</li>';
    }
    return '<article class="milestone" data-milestone="' + escape(milestone.id) + '" data-company="' + escape(company.id) + '">'
      + '<div class="milestone-top"><span>' + escape(human(milestone.type)) + '</span><span class="badge">' + escape(status) + '</span></div>'
      + '<h3>' + escape(text(milestone.project)) + '</h3><ol class="timeline">'
      + stage(original, 'Original target') + revisions.map((revision, index) => stage(revision, 'Revision ' + (index + 1))).join('')
      + (outcome ? stage(outcome, 'Disclosed outcome', true) : '') + '</ol>'
      + (!outcome ? '<p class="outcome-gap">Outcome unavailable' + (state.asof ? ' at this knowledge date' : ' in the reviewed sources') + '. An elapsed target alone does not establish delivery or failure.</p>' : '')
      + (!state.asof && milestone.explanation ? '<p class="history-explanation">' + escape(milestone.explanation) + '</p>' : '') + '</article>';
  }

  function historicalNote() {
    return '<div class="reading-note"><div><strong>' + (state.asof ? 'Only disclosures published by ' + date(state.asof) + '.' : 'Disclosure dates establish availability.')
      + '</strong> Targets are commitments, not delivered capacity. Later revisions and outcomes are hidden when an earlier knowledge date is selected. '
      + 'Undated records are excluded; financial statement dates alone do not establish public availability. Knowledge dates are capped at each company’s review date.</div></div>';
  }

  function historyPage() {
    let count = 0;
    const groups = selectedCompanies().map(company => {
      const entries = list(company.milestones).filter(milestone => matches([company.name, company.ticker, milestone.project, milestone.type,
        milestone.original?.target, ...list(milestone.revisions).filter(known).map(revision => revision.target),
        known(milestone.outcome) ? milestone.outcome?.description : ''
      ].join(' '))).map(milestone => milestoneMarkup(company, milestone)).filter(Boolean);
      count += entries.length;
      return entries.length ? '<section class="history-company"><div class="section-title"><h2><a data-app href="' + escape(profile(company))
        + '">' + escape(company.name) + '</a></h2><span>' + escape(company.ticker) + ' · ' + entries.length + ' tracked commitment'
        + (entries.length === 1 ? '' : 's') + '</span></div><div class="milestones">' + entries.join('') + '</div></section>' : '';
    }).join('');
    return heading('Commitment history', 'Follow what management originally committed to, what changed, and which outcome is actually supported by a disclosure.', true)
      + historicalNote() + (count ? groups : empty('No publication-dated commitments match this company selection, search and knowledge date.'));
  }

  function changesPage() {
    const changes = selectedCompanies().flatMap(company => list(company.changes).map(change => ({company, change})))
      .filter(({company, change}) => known(change) && (state.type === 'all' || change.type === state.type)
        && (!state.from || String(change.published).slice(0, 10) >= state.from)
        && (!state.to || String(change.published).slice(0, 10) <= state.to)
        && matches([company.name, company.ticker, change.type, change.before, change.after, change.why].join(' ')))
      .sort((a, b) => String(b.change.published).localeCompare(String(a.change.published)));
    const cards = changes.map(({company, change}) => '<article class="change-card" data-change="' + escape(change.id) + '" data-company="' + escape(company.id) + '">'
      + '<header class="change-top"><div><a class="change-company" data-app href="' + escape(profile(company)) + '">' + escape(company.name)
      + ' <span class="company-ticker">' + escape(company.ticker) + '</span></a> <span class="badge">' + escape(human(change.type)) + '</span></div>'
      + '<time class="change-date" datetime="' + escape(change.published) + '">Disclosed ' + date(change.published) + '</time></header>'
      + '<div class="change-pair"><section><h3>Before</h3><p>' + escape(text(change.before)) + '</p>'
      + (change.before_source ? evidence(company, change.before_source, '', 'Earlier disclosure') : '<span class="small muted">Prior context stated in the linked disclosure.</span>')
      + '</section><section><h3>After</h3><p>' + escape(text(change.after)) + '</p>' + evidence(company, change.source, '', 'Updated disclosure') + '</section></div>'
      + '<p class="change-why"><strong>Analyst interpretation</strong> · ' + escape(text(change.why).replace(/^Analyst interpretation:\s*/i, '')) + '</p></article>').join('');
    return heading('Material changes', 'Source-backed before / after records across delivery, capacity, financing, customers and guidance.', true)
      + historicalNote() + '<div class="section-title"><h2>Disclosure changes</h2><span>' + changes.length + ' matching record'
      + (changes.length === 1 ? '' : 's') + '</span></div>' + (cards ? '<div class="change-list">' + cards + '</div>'
        : empty('No disclosure changes match these dates, companies, change types and search terms.'));
  }

  function render() {
    state = readState();
    const historical = state.view === 'history' || state.view === 'changes';
    $('historical-controls').hidden = !historical;
    for (const id of ['type-control', 'from-control', 'to-control']) $(id).hidden = state.view !== 'changes';
    for (const [id, key] of [['q', 'q'], ['asof', 'asof'], ['change-type', 'type'], ['date-from', 'from'], ['date-to', 'to']]) {
      if ($(id).value !== state[key]) $(id).value = state[key];
    }
    for (const checkbox of document.querySelectorAll('[data-peer]')) checkbox.checked = state.peers.includes(checkbox.dataset.peer);
    $('peer-count').textContent = state.peers.length + ' selected';
    for (const link of document.querySelectorAll('#primary-nav [data-view]')) {
      link.href = href(link.dataset.view);
      if (link.dataset.view === state.view) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    document.title = 'Neocloud Intelligence Terminal — ' + viewNames[state.view];
    $('page-content').innerHTML = dataError ? empty(dataError) : !companies.length
      ? empty('No reviewed company data has been embedded in this file. Build the terminal with its source ledger.')
      : state.view === 'companies' ? profilePage() : state.view === 'history' ? historyPage() : state.view === 'changes' ? changesPage() : comparePage();
  }

  function openEvidence(button) {
    const company = companies.find(item => item.id === button.dataset.sourceCompany);
    if (!company) return;
    const source = sourceRecord(company, button.dataset.source);
    const fact = list(company.facts).find(item => item.id === button.dataset.fact);
    const url = safeURL(source?.url);
    const fields = fact ? [
      ['Company', company.name], ['Metric', fact.label], ['Source publication', source?.published], ['Observation / period', fact.as_of], ['Review timestamp (UTC)', company.reviewed_at], ['Unit', fact.unit],
      ['Definition', fact.definition], ['Scope', fact.scope], ['Reported / estimated basis', fact.basis],
      ['Verification / review', fact.verification], ['Filing locator / table', fact.locator], ['Formula', fact.formula]
    ].filter(([, value]) => value !== null && value !== undefined && value !== '') : [['Company', company.name], ['Source publication', source?.published], ['Review timestamp (UTC)', company.reviewed_at]];
    $('evidence-body').innerHTML = '<h2 id="evidence-title">' + escape(source?.title || 'Source record unavailable') + '</h2>'
      + '<p class="muted">Source published ' + date(source?.published) + '<br>Research reviewed (UTC) ' + escape(text(company.reviewed_at)) + '</p>'
      + (fact?.excerpt || source?.excerpt ? '<blockquote class="source-excerpt">' + escape(fact?.excerpt || source.excerpt) + '</blockquote>'
        : '<p class="empty">Supporting excerpt unavailable. Open the original source and preserve this evidence gap.</p>')
      + (fact?.excerpt && source?.excerpt && fact.excerpt !== source.excerpt
        ? '<details><summary>Broader source excerpt</summary><blockquote class="source-excerpt">' + escape(source.excerpt) + '</blockquote></details>' : '')
      + (url ? '<a class="source-link" href="' + escape(url) + '" target="_blank" rel="noopener noreferrer">Open original source ↗</a><p class="small muted">' + escape(url) + '</p>'
        : '<p class="unavailable">A safe public source URL is unavailable.</p>')
      + '<dl class="source-metadata">' + fields.map(([label, value]) => '<div><dt>' + escape(label) + '</dt><dd>' + escape(text(value)) + '</dd></div>').join('') + '</dl>'
      + (fact ? inputEvidence(company, fact) : '');
    if (!$('evidence-dialog').open) $('evidence-dialog').showModal();
  }

  function reset() {
    navigate(state.view, {peers: companies.map(company => company.id), q: '', asof: '', type: 'all', from: '', to: ''});
  }

  function init() {
    try {
      const parsed = JSON.parse($('terminal-data')?.textContent || '[]');
      if (!Array.isArray(parsed)) throw new Error('Research must be a company array.');
      companies = parsed.filter(company => company && typeof company.id === 'string');
    } catch { dataError = 'The embedded research could not be read. Rebuild the terminal from its validated source records.'; }
    latestReview = companies.map(company => String(company.reviewed_at || '').slice(0, 10)).filter(Boolean).sort().at(-1) || '';
    $('review-date').textContent = latestReview ? 'Reviewed ' + latestReview : 'Review date unavailable';
    $('peer-options').insertAdjacentHTML('beforeend', companies.map(company => '<label class="peer-option"><input type="checkbox" data-peer="'
      + escape(company.id) + '" aria-label="Select ' + escape(company.ticker) + '"><span><strong>' + escape(company.ticker) + '</strong>' + escape(company.name) + '</span></label>').join(''));
    $('q').addEventListener('input', event => navigate(state.view, {q: event.target.value}, true));
    for (const [id, key] of [['asof', 'asof'], ['change-type', 'type'], ['date-from', 'from'], ['date-to', 'to']]) {
      $(id).addEventListener('change', event => navigate(state.view, {[key]: event.target.value}));
    }
    $('reset').addEventListener('click', reset);
    $('close-evidence').addEventListener('click', () => $('evidence-dialog').close());
    $('evidence-dialog').addEventListener('click', event => { if (event.target === $('evidence-dialog')) $('evidence-dialog').close(); });
    document.addEventListener('change', event => {
      if (!event.target.matches('[data-peer]')) return;
      const peers = [...document.querySelectorAll('[data-peer]:checked')].map(input => input.dataset.peer);
      navigate(state.view, {peers});
    });
    document.addEventListener('click', event => {
      const source = event.target.closest('[data-source]');
      if (source) { openEvidence(source); return; }
      const select = event.target.closest('[data-select]');
      if (select) navigate(state.view, {peers: select.dataset.select === 'all' ? companies.map(company => company.id) : []});
      if (event.target.closest('[data-reset]')) reset();
      const link = event.target.closest('a[data-app]');
      if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) {
        event.preventDefault();
        history.pushState({}, '', link.getAttribute('href'));
        render();
        $('page-content').scrollIntoView({block: 'start'});
      }
    });
    addEventListener('hashchange', render);
    addEventListener('popstate', render);
    render();
  }
  init();
})();
