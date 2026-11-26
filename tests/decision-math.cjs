'use strict';
// Synthetic inputs only. No test values represent market observations.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const M = require('../terminal-preview/decision-math.js');
let checks = 0;
function test(name, fn) { fn(); checks++; console.log('ok - ' + name); }
const model = {revenue: 1000, margin: 40, multiple: 10, debt: 2000, cash: 100, claims: 100, shares: 100};
const trade = {entry: 50, stop: 45, target: 65, capital: 100000, riskBudgetPct: 1,
  maxPositionPct: 20, currentShares: 0, currentCost: 0};
const close = (a,b) => assert(Math.abs(a-b) < 1e-8, `${a} != ${b}`);

test('enterprise bridge keeps debt, cash, claims and dilution separate', () => {
  const r = M.scenario(model);
  assert.equal(r.ok, true); assert.equal(r.ebitda, 400); assert.equal(r.enterpriseValue, 4000);
  assert.equal(r.equity, 2000); assert.equal(r.price, 20); assert.equal(r.deficit, false);
  assert.equal(M.scenario({...model, shares: 200}).price, 10);
  assert.equal(M.scenario({...model, debt: 2100}).price, 19);
  assert.equal(M.scenario({...model, claims: 200}).price, 19);
  assert.equal(M.scenario({...model, cash: 200}).price, 21);
});
test('negative residual is disclosed rather than rendered as negative share price', () => {
  const r = M.scenario({...model, debt: 5000});
  assert.equal(r.rawEquity, -1000); assert.equal(r.price, 0); assert.equal(r.deficit, true);
  assert.equal(r.shortfall, 1000);
});
test('zero revenue or margin is a valid explicit scenario, not an absent value', () => {
  assert.equal(M.scenario({...model, revenue: 0}).price, 0);
  assert.equal(M.scenario({...model, margin: 0}).price, 0);
  assert.equal(M.scenario({...model, debt: 0, cash: 0, claims: 0}).price, 40);
});
test('blank, null, booleans, collections and nonfinite values never silently become zero', () => {
  for (const value of ['', ' ', null, undefined, false, true, [], {}, NaN, Infinity, -1, '0x10', '12 USD']) {
    assert.equal(M.scenario({...model, debt: value}).ok, false, String(value));
  }
  assert.equal(M.scenario({...model, shares: 0}).ok, false);
  assert.equal(M.scenario({...model, multiple: 0}).ok, false);
  assert.equal(M.scenario({...model, margin: 101}).ok, false);
  assert.equal(M.scenario(null).ok, false);
});
test('decimal form strings work without changing the supplied object', () => {
  const input = {...model, revenue: ' 1000.0 ', margin: '4e1'};
  const before = JSON.stringify(input);
  assert.equal(M.scenario(input).price, 20);
  assert.equal(JSON.stringify(input), before);
});
test('reverse valuation round-trips the unfloored equity model', () => {
  for (const revenue of [500, 1000, 2000, 4000]) {
    const p = {...model, revenue, debt: 100};
    const direct = M.scenario(p);
    const reverse = M.reverse({...p, price: direct.price});
    assert.equal(reverse.ok, true); close(reverse.requiredRevenue, revenue);
  }
  assert.equal(M.reverse({...model, price: 20, margin: 0}).ok, false);
  assert.equal(M.reverse({...model, price: '', margin: 40}).ok, false);
  assert.equal(M.reverse({...model, price: 0, cash: 10000}).ok, false);
});
test('whole-share sizing obeys risk and allocation caps independently', () => {
  const r = M.position(trade);
  assert.equal(r.maxShares, 200); assert.equal(r.additionalShares, 200);
  assert.equal(r.plannedRisk, 1000); assert.equal(r.rewardRisk, 3);
  assert.equal(r.upsidePct, 30); assert.equal(r.downsidePct, 10);
  const capped = M.position({...trade, maxPositionPct: 3.01});
  assert.equal(capped.maxShares, 60); assert(capped.plannedValue <= capped.allocationBudget);
  const odd = M.position({...trade, entry: 51.7, stop: 43.21, maxPositionPct: 7.123});
  assert(odd.plannedRisk <= odd.riskBudget); assert(odd.plannedValue <= odd.allocationBudget);
});
test('available cash caps additions without counting existing shares as a new purchase', () => {
  const r = M.position({...trade, currentShares: 100, currentCost: 40, cashAvailable: 1250});
  assert.equal(r.additionalShares, 25); assert.equal(r.plannedShares, 125);
  assert.equal(r.cashConstrained, true); assert.equal(r.currentUnrealizedPnl, 1000);
  assert.equal(r.currentRisk, 500); assert.equal(r.pnlAtStop, 500);
  assert.equal(r.pnlAtTarget, 2500);
  assert.equal(M.position({...trade, cashAvailable: 0}).additionalShares, 0);
  assert.equal(M.position({...trade, cashAvailable: ''}).ok, false);
  assert.equal(M.position({...trade, cashAvailable: null}).ok, false);
});
test('an oversized existing holding reports excess without pretending it was reduced', () => {
  const r = M.position({...trade, currentShares: 300, currentCost: 60});
  assert.equal(r.additionalShares, 0); assert.equal(r.sharesOverLimit, 100);
  assert.equal(r.plannedShares, 300); assert.equal(r.currentRisk, 1500);
  assert.equal(r.currentUnrealizedPnl, -3000); assert.equal(r.pnlAtStop, -4500);
});
test('invalid long structures and missing portfolio assumptions are blocked', () => {
  for (const patch of [{stop: 50}, {stop: 55}, {target: 50}, {target: 40}, {capital: 0},
    {riskBudgetPct: 0}, {riskBudgetPct: 101}, {maxPositionPct: 101}, {currentShares: -1},
    {currentShares: 1, currentCost: 0}, {currentShares: null}, {entry: ''}]) {
    assert.equal(M.position({...trade, ...patch}).ok, false, JSON.stringify(patch));
  }
  assert.equal(M.position(null).ok, false);
});
test('overflow fails closed across direct, reverse and position models', () => {
  assert.equal(M.scenario({...model, revenue: 1e308, multiple: 1e308}).ok, false);
  assert.equal(M.reverse({...model, price: 1e308, shares: 1e308}).ok, false);
  assert.equal(M.position({...trade, currentShares: 1e308}).ok, false);
});
test('weighted scenarios require explicit probabilities totaling 100', () => {
  const rows = [{price: 0, probability: 25}, {price: 20, probability: 50}, {price: 40, probability: 25}];
  assert.equal(M.weighted(rows).price, 20);
  assert.equal(M.weighted(rows).minimum, 0);
  assert.equal(M.weighted([{price: 1, probability: 50}, {price: 2, probability: 49}]).ok, false);
  assert.equal(M.weighted([{price: 1, probability: ''}, {price: 2, probability: 100}]).ok, false);
  assert.equal(M.weighted([{price: 1, probability: -1}, {price: 2, probability: 101}]).ok, false);
  assert.equal(M.weighted([]).ok, false); assert.equal(M.weighted(null).ok, false);
});
test('residual equity discounts explicit year-end common cash and terminal value', () => {
  const r = M.projectResidual({cashflows: [110, 121], discountRatePct: 10,
    terminalEquityValue: 1210, corporateClaims: 200, shares: 100});
  assert.equal(r.ok, true); assert.equal(r.years, 2);
  close(r.presentValues[0], 100); close(r.presentValues[1], 100);
  close(r.presentValueCashflows, 200); close(r.presentValueTerminal, 1000);
  close(r.rawEquity, 1000); close(r.price, 10);
});
test('negative funding years reduce common residual without pretending revenue is cash', () => {
  const r = M.projectResidual({cashflows: [-110, 121], discountRatePct: 10,
    terminalEquityValue: 0, corporateClaims: 0, shares: 10});
  close(r.presentValues[0], -100); close(r.presentValues[1], 100);
  close(r.equity, 0); close(r.price, 0);
  const deficit = M.projectResidual({cashflows: [-110, 60.5], discountRatePct: 10,
    terminalEquityValue: 0, corporateClaims: 0, shares: 10});
  close(deficit.rawEquity, -50); assert.equal(deficit.deficit, true);
  assert.equal(deficit.equity, 0); assert.equal(deficit.price, 0);
});
test('residual model adds no hidden debt deduction or inferred terminal growth', () => {
  const input = {cashflows: [110], discountRatePct: 10, terminalEquityValue: 1100,
    corporateClaims: 0, shares: 100};
  const r = M.projectResidual(input);
  close(r.equity, 1100); close(r.price, 11);
  close(M.projectResidual({...input, corporateClaims: 100}).equity, 1000);
  close(M.projectResidual({...input, shares: 200}).price, 5.5);
  // Debt is already reflected upstream. The API cannot deduct an unrelated
  // enterprise-debt field a second time or invent a perpetuity from one year.
  close(M.projectResidual({...input, debt: 100000}).equity, 1100);
  close(M.projectResidual({...input, terminalEquityValue: 0}).equity, 100);
});
test('residual model rejects blank years, missing claims and invalid horizons/rates', () => {
  const input = {cashflows: [0], discountRatePct: 10, terminalEquityValue: 0,
    corporateClaims: 0, shares: 100};
  assert.equal(M.projectResidual(input).ok, true);
  for (const value of ['', ' ', null, undefined, false, [], {}, NaN, Infinity]) {
    assert.equal(M.projectResidual({...input, cashflows: [value]}).ok, false);
  }
  for (const patch of [{cashflows: []}, {cashflows: Array(31).fill(0)}, {cashflows: Array(2)},
    {discountRatePct: 0}, {discountRatePct: -1}, {discountRatePct: 101},
    {terminalEquityValue: -1}, {terminalEquityValue: ''}, {corporateClaims: null},
    {shares: 0}, {shares: -1}]) assert.equal(M.projectResidual({...input, ...patch}).ok, false);
  assert.equal(M.projectResidual(null).ok, false);
  assert.equal(M.projectResidual({...input, cashflows: [1e308, 1e308, 1e308], discountRatePct: 1}).ok, false);
});
test('residual form strings do not mutate input and twenty-year discounting remains finite', () => {
  const input = {cashflows: ['-50', '0', ...Array(18).fill('100')], discountRatePct: '12',
    terminalEquityValue: '0', corporateClaims: '0', shares: '100'};
  const before = JSON.stringify(input); const r = M.projectResidual(input);
  assert.equal(r.ok, true); assert.equal(r.years, 20); assert(Number.isFinite(r.price));
  assert.equal(JSON.stringify(input), before);
});
function marketBars(closes = Array.from({length: 21}, (_, i) => 100 + i)) {
  return closes.map((close, i) => ({date: new Date(Date.UTC(2026, 0, i + 1)).toISOString().slice(0, 10),
    open: close, high: close + 2, low: close - 2, close, volume: (i + 1) * 100, completed: true}));
}
test('market context uses twenty closes but twenty-one prices for twenty returns', () => {
  const bars = marketBars(); const saved = JSON.stringify(bars); const r = M.marketContext(bars);
  assert.equal(r.ok, true); assert.equal(r.complete, true); assert.equal(r.volatilityReturnCount, 20);
  close(r.return5SessionPct, (120 / 115 - 1) * 100);
  close(r.averageVolume20, 1150);
  close(r.averageDollarVolume20, bars.slice(1).reduce((a, b) => a + b.close * b.volume, 0) / 20);
  assert.equal(r.closeHigh20, 120); assert.equal(r.closeLow20, 101); close(r.meanTrueRange14, 4);
  const logs = bars.slice(1).map((b, i) => Math.log(b.close / bars[i].close));
  const average = logs.reduce((a, b) => a + b, 0) / 20;
  close(r.realizedVolatility20Pct, Math.sqrt(logs.reduce((a, b) => a + (b - average) ** 2, 0) / 19) * Math.sqrt(252) * 100);
  assert.match(r.dollarVolumeBasis, /proxy/); assert.equal(JSON.stringify(bars), saved);
});
test('market context handles signed returns and gaps with simple mean true range', () => {
  const bars = marketBars(Array.from({length: 21}, (_, i) => 200 - 5 * i));
  const r = M.marketContext(bars); assert.equal(r.ok, true);
  close(r.return5SessionPct, -20); close(r.meanTrueRange14, 7);
  assert(r.realizedVolatility20Pct > 0);
  const flat = marketBars(Array(21).fill(100)).map(bar => ({...bar, open: 100, high: 100, low: 100, volume: 0}));
  const f = M.marketContext(flat); assert.equal(f.ok, true);
  for (const key of ['return5SessionPct', 'meanTrueRange14', 'realizedVolatility20Pct', 'averageVolume20', 'averageDollarVolume20']) close(f[key], 0);
  const alternating = marketBars(Array.from({length: 21}, (_, i) => 100 * Math.exp(i % 2 ? 0.1 : 0)));
  close(M.marketContext(alternating).realizedVolatility20Pct, Math.sqrt(0.2 / 19 * 252) * 100);
});
test('market context requires complete records and never substitutes missing or partial sessions', () => {
  const bars = marketBars(); assert.equal(M.marketContext(bars.slice(1)).ok, false);
  const partial = M.marketContext(bars.slice(1), {allowPartial: true});
  assert.equal(partial.ok, true); assert.equal(partial.complete, false); assert.equal(partial.realizedVolatility20Pct, null);
  assert.equal(M.marketContext(bars.slice(2), {allowPartial: true}).ok, false);
  for (const patch of [{date: '2026-02-30'}, {date: ''}, {date: '2026-01-01'},
    {completed: false}, {completed: undefined}, {close: ''}, {close: null}, {close: NaN},
    {volume: Infinity}, {volume: -1}, {low: 200}, {high: 1}, {open: 0}, {close: 1000}]) {
    const bad = bars.map(b => ({...b})); bad[1] = {...bad[1], ...patch};
    assert.equal(M.marketContext(bad).ok, false, JSON.stringify(patch));
  }
  assert.equal(M.marketContext([...bars].reverse()).ok, false);
  const sparse = [...bars]; delete sparse[1]; assert.equal(M.marketContext(sparse).ok, false);
  assert.equal(M.marketContext(bars, {allowPartial: 'true'}).ok, false);
  const overflow = bars.map(b => ({...b, volume: 1e308})); assert.equal(M.marketContext(overflow).ok, false);
});
test('common equity hurdle is a distribution identity with explicit million-dollar units', () => {
  const r = M.equityHurdle({price: 20, shares: 100, equityYieldPct: 8});
  assert.equal(r.ok, true); close(r.equityValue, 2000); close(r.requiredAnnualCash, 160);
  close(r.requiredAnnualCash / r.equityValue * 100, 8); assert.equal(r.units, 'USD millions');
  close(M.equityHurdle({price: 20, shares: 150, equityYieldPct: 8}).requiredAnnualCash, 240);
  for (const key of ['price', 'shares', 'equityYieldPct']) {
    for (const bad of ['', null, false, NaN, Infinity, -1, 0]) {
      assert.equal(M.equityHurdle({price: 20, shares: 100, equityYieldPct: 8, [key]: bad}).ok, false);
    }
  }
  assert.equal(M.equityHurdle({price: 20, shares: 100, equityYieldPct: 101}).ok, false);
  assert.equal(M.equityHurdle({price: 1e308, shares: 1e308, equityYieldPct: 8}).ok, false);
});
test('browser global exports the identical API without CommonJS', () => {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(require.resolve('../terminal-preview/decision-math.js'), 'utf8'), context);
  assert.equal(context.DecisionMath.scenario(model).price, 20);
  assert.deepEqual(Object.keys(context.DecisionMath).sort(), Object.keys(M).sort());
});
console.log(`${checks} decision math checks passed.`);
