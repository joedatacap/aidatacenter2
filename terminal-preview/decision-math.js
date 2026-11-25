/* Pure illustrative decision calculations. No market data or forecasts.
 * Browser: DecisionMath. Node: require('./decision-math.js').
 * All functions return {ok:false,errors:[message]} on invalid inputs, never
 * substitute zero for a missing value, and do not mutate inputs.
 *
 * scenario({revenue,margin,multiple,debt,cash,claims,shares})
 *   Revenue/balance inputs: USD millions. Shares: fully diluted millions.
 *   Margin: percentage, not fraction. Cash: unrestricted only. Claims: other
 *   senior/non-common claims not already included in debt. Keep scopes/dates
 *   consistent. EBITDA and all model inputs are user assumptions; leases and
 *   minority claims require a consistent EV/EBITDA convention.
 *   Returns ebitda,enterpriseValue,netClaims,equity,rawEquity,deficit,price.
 *   A zero floor represents no residual common value in this model, not a
 *   prediction of bankruptcy or the price at which a share will trade.
 * reverse({price,margin,multiple,debt,cash,claims,shares})
 *   Same units. Price: USD/share. Returns impliedEquity,impliedEnterpriseValue,
 *   requiredEbitda,requiredRevenue; does not establish market expectations.
 * position({entry,stop,target,capital,riskBudgetPct,maxPositionPct,
 *           currentShares,currentCost,cashAvailable?})
 *   Dollar/share prices and USD capital. Entry is the proposed entry or current
 *   reference price, capital is total account equity, currentCost average paid.
 *   Current risk is forward loss from entry/reference to stop, not cost basis.
 *   cashAvailable caps additional purchases only. Omit for no cash constraint;
 *   blank/null supplied cash is invalid. Whole-share limits are rounded down.
 *   A stop is a planning assumption and does not guarantee an execution price.
 * weighted([{price,probability},...])
 *   Explicit user probabilities must total 100. Returns weighted price and
 *   minimum/maximum scenario prices; not a calibrated expected return.
 * projectResidual({cashflows,discountRatePct,terminalEquityValue,corporateClaims,shares})
 *   cashflows: 1–30 explicit annual USD-million amounts available to common,
 *   received/paid at each year-end. Negative years represent equity funding.
 *   For APLD, use parent-attributable distributions AFTER project debt service,
 *   minority/preferred waterfalls and corporate costs. For AGPU, use explicit
 *   post-financing common cash flow assumptions. Do not use revenue or EBITDA.
 *   terminalEquityValue: USD-million common residual at the LAST year-end,
 *   already net of project debt and other claims. No growth rate is inferred.
 *   corporateClaims: present-value USD-million claims NOT already reflected in
 *   cashflows or terminal value. Zero must be explicit. Never deduct the same
 *   debt twice. Shares: assumed fully diluted millions, including financing.
 *   Returns presentValues,presentValueCashflows,presentValueTerminal,rawEquity,
 *   equity,price,deficit,years. This is discounted equity, not enterprise value.
 */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.DecisionMath = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const status = 'Illustrative assumptions, not a price forecast';
  const numeric = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i;
  function inputObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }
  function number(value, name, errors, {positive = false, max = Infinity} = {}) {
    const validType = typeof value === 'number' ||
      (typeof value === 'string' && numeric.test(value.trim()));
    const parsed = validType ? Number(value) : NaN;
    if (!Number.isFinite(parsed) || parsed < 0 || (positive && parsed === 0) || parsed > max) {
      errors.push(name + ' must be a finite ' + (positive ? 'positive' : 'nonnegative') +
        ' number' + (Number.isFinite(max) ? ' no greater than ' + max : '') + '.');
    }
    return parsed;
  }
  function fail(errors) { return {ok: false, errors}; }
  function result(values) {
    if (Object.values(values).some(value => typeof value === 'number' && !Number.isFinite(value))) {
      return fail(['Calculation exceeded numeric limits. Use smaller, consistently scaled inputs.']);
    }
    return {ok: true, status, ...values};
  }
  function valuationInputs(input, reverseMode) {
    const errors = [];
    if (!inputObject(input)) return {errors: ['Enter all valuation inputs.']};
    const margin = number(input.margin, 'EBITDA margin (%)', errors, {positive: reverseMode, max: 100});
    const multiple = number(input.multiple, 'EV/EBITDA multiple', errors, {positive: true});
    const debt = number(input.debt, 'Debt', errors);
    const cash = number(input.cash, 'Unrestricted cash', errors);
    const claims = number(input.claims, 'Other claims', errors);
    const shares = number(input.shares, 'Fully diluted shares', errors, {positive: true});
    return {errors, margin, multiple, debt, cash, claims, shares};
  }
  function scenario(input) {
    const p = valuationInputs(input, false);
    if (p.errors.length) return fail(p.errors);
    const revenue = number(input.revenue, 'Annual revenue', p.errors);
    if (p.errors.length) return fail(p.errors);
    const ebitda = revenue * p.margin / 100;
    const enterpriseValue = ebitda * p.multiple;
    const netClaims = p.debt - p.cash + p.claims;
    const rawEquity = enterpriseValue - netClaims;
    const equity = Math.max(0, rawEquity);
    return result({ebitda, enterpriseValue, netClaims, rawEquity, equity,
      deficit: rawEquity < 0, shortfall: Math.max(0, -rawEquity), price: equity / p.shares});
  }
  function reverse(input) {
    const p = valuationInputs(input, true);
    if (p.errors.length) return fail(p.errors);
    const price = number(input.price, 'Reference price', p.errors);
    if (p.errors.length) return fail(p.errors);
    const impliedEquity = price * p.shares;
    const impliedEnterpriseValue = impliedEquity + p.debt - p.cash + p.claims;
    if (impliedEnterpriseValue < 0) {
      return fail(['The implied enterprise value is negative. A positive EV/EBITDA model cannot infer revenue from these inputs.']);
    }
    const requiredEbitda = impliedEnterpriseValue / p.multiple;
    return result({impliedEquity, impliedEnterpriseValue, requiredEbitda,
      requiredRevenue: requiredEbitda / (p.margin / 100)});
  }
  function position(input) {
    if (!inputObject(input)) return fail(['Enter all position inputs.']);
    const errors = [];
    const entry = number(input.entry, 'Entry/reference price', errors, {positive: true});
    const stop = number(input.stop, 'Stop assumption', errors);
    const target = number(input.target, 'Target assumption', errors, {positive: true});
    const capital = number(input.capital, 'Account equity', errors, {positive: true});
    const riskBudgetPct = number(input.riskBudgetPct, 'Risk budget (%)', errors, {positive: true, max: 100});
    const maxPositionPct = number(input.maxPositionPct, 'Maximum position (%)', errors, {positive: true, max: 100});
    const currentShares = number(input.currentShares, 'Current shares', errors);
    const currentCost = number(input.currentCost, 'Average cost', errors, {positive: currentShares > 0});
    const cashAvailable = input.cashAvailable === undefined ? null : number(input.cashAvailable, 'Available cash', errors);
    if (errors.length) return fail(errors);
    if (stop >= entry) errors.push('For a long position, the stop must be below the entry/reference price.');
    if (target <= entry) errors.push('For a long position, the target must be above the entry/reference price.');
    if (errors.length) return fail(errors);
    const riskPerShare = entry - stop;
    const rewardPerShare = target - entry;
    const riskBudget = capital * riskBudgetPct / 100;
    const allocationBudget = capital * maxPositionPct / 100;
    const riskLimitedShares = Math.floor(riskBudget / riskPerShare);
    const allocationLimitedShares = Math.floor(allocationBudget / entry);
    const maxShares = Math.min(riskLimitedShares, allocationLimitedShares);
    const additionalCapacity = Math.max(0, Math.floor(maxShares - currentShares));
    const additionalShares = cashAvailable === null ? additionalCapacity :
      Math.min(additionalCapacity, Math.floor(cashAvailable / entry));
    const currentValue = currentShares * entry;
    const currentRisk = currentShares * riskPerShare;
    return result({riskPerShare, rewardPerShare, riskBudget, allocationBudget,
      riskLimitedShares, allocationLimitedShares, maxShares, additionalShares,
      sharesOverLimit: Math.max(0, currentShares - maxShares),
      cashConstrained: additionalShares < additionalCapacity,
      plannedShares: currentShares + additionalShares,
      plannedValue: (currentShares + additionalShares) * entry,
      plannedRisk: (currentShares + additionalShares) * riskPerShare,
      currentValue, currentRisk, currentRiskPct: currentRisk / capital * 100,
      currentAllocationPct: currentValue / capital * 100,
      currentUnrealizedPnl: currentShares * (entry - currentCost),
      pnlAtStop: currentShares * (stop - currentCost),
      pnlAtTarget: currentShares * (target - currentCost),
      upsidePct: rewardPerShare / entry * 100,
      downsidePct: riskPerShare / entry * 100,
      rewardRisk: rewardPerShare / riskPerShare,
      warning: 'Stops can gap or slip. These limits exclude fees, taxes, liquidity constraints and correlated positions.'});
  }
  function weighted(rows) {
    if (!Array.isArray(rows) || rows.length < 2) return fail(['Enter at least two scenarios with explicit probabilities.']);
    const errors = [];
    const parsed = rows.map((row, i) => {
      if (!inputObject(row)) { errors.push('Scenario ' + (i + 1) + ' is missing.'); return {}; }
      return {price: number(row.price, 'Scenario ' + (i + 1) + ' price', errors),
        probability: number(row.probability, 'Scenario ' + (i + 1) + ' probability (%)', errors, {max: 100})};
    });
    if (errors.length) return fail(errors);
    const totalProbability = parsed.reduce((sum, row) => sum + row.probability, 0);
    if (Math.abs(totalProbability - 100) > 1e-8) return fail(['Scenario probabilities must sum to 100%.']);
    return result({price: parsed.reduce((sum, row) => sum + row.price * (row.probability / 100), 0),
      totalProbability, minimum: Math.min(...parsed.map(row => row.price)), maximum: Math.max(...parsed.map(row => row.price))});
  }
  function projectResidual(input) {
    if (!inputObject(input)) return fail(['Enter all residual equity inputs.']);
    const errors = [];
    if (!Array.isArray(input.cashflows) || input.cashflows.length < 1 || input.cashflows.length > 30) {
      return fail(['Enter 1 to 30 explicit annual cash flows available to common equity.']);
    }
    const cashflows = Array.from(input.cashflows, (value, i) => {
      const validType = typeof value === 'number' ||
        (typeof value === 'string' && numeric.test(value.trim()));
      const parsed = validType ? Number(value) : NaN;
      if (!Number.isFinite(parsed)) errors.push('Year ' + (i + 1) + ' common cash flow must be a finite number; use an explicit negative amount for equity funding.');
      return parsed;
    });
    const discountRatePct = number(input.discountRatePct, 'Equity discount rate (%)', errors, {positive: true, max: 100});
    const terminalEquityValue = number(input.terminalEquityValue, 'Terminal common equity value', errors);
    const corporateClaims = number(input.corporateClaims, 'Additional corporate claims at present value', errors);
    const shares = number(input.shares, 'Fully diluted shares', errors, {positive: true});
    if (errors.length) return fail(errors);
    const rate = discountRatePct / 100;
    const years = cashflows.length;
    const presentValues = cashflows.map((cash, i) => cash / Math.pow(1 + rate, i + 1));
    const presentValueCashflows = presentValues.reduce((sum, cash) => sum + cash, 0);
    const presentValueTerminal = terminalEquityValue / Math.pow(1 + rate, years);
    const rawEquity = presentValueCashflows + presentValueTerminal - corporateClaims;
    const equity = Math.max(0, rawEquity);
    return result({presentValues, presentValueCashflows, presentValueTerminal,
      rawEquity, equity, price: equity / shares, deficit: rawEquity < 0, years});
  }
  return Object.freeze({scenario, reverse, position, weighted, projectResidual});
});
