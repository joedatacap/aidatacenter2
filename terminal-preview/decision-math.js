/* Pure illustrative decision calculations. No market data or forecasts.
 * Historical market statistics describe supplied completed sessions only.
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
 * marketContext(bars,{allowPartial:false}?)
 *   Chronological, unique date YYYY-MM-DD OHLCV records with completed:true.
 *   Positive same-basis OHLC prices; nonnegative volume. Caller must verify the
 *   series has no missing exchange sessions and consistent split adjustments.
 *   Default requires 21 bars: 20 returns need 21 closes. Explicit allowPartial
 *   accepts exactly 20 bars with volatility null; never annualizes 19 as 20.
 *   Last 20 closes define price range and mean volume/dollar-volume. Dollar
 *   volume is close*volume proxy, not actual traded dollars or execution depth.
 *   meanTrueRange14 is simple arithmetic mean, NOT Wilder ATR. Volatility uses
 *   sample standard deviation of 20 daily log returns, annualized by sqrt(252).
 * equityHurdle({price,shares,equityYieldPct})
 *   USD/share price, fully diluted shares in millions, positive yield percent.
 *   Returns equityValue and requiredAnnualCash in USD millions. This is the
 *   common cash distribution needed for the specified yield, not a forecast.
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
  function equityHurdle(input) {
    if (!inputObject(input)) return fail(['Enter all common-equity hurdle inputs.']);
    const errors = [];
    const price = number(input.price, 'Market price', errors, {positive: true});
    const shares = number(input.shares, 'Fully diluted shares (millions)', errors, {positive: true});
    const equityYieldPct = number(input.equityYieldPct, 'Required common cash yield (%)', errors, {positive: true, max: 100});
    if (errors.length) return fail(errors);
    const equityValue = price * shares;
    return result({equityValue, requiredAnnualCash: equityValue * equityYieldPct / 100,
      equityYieldPct, units: 'USD millions', status: 'Required common cash distribution hurdle, not a forecast'});
  }
  function marketContext(bars, options = {}) {
    if (!inputObject(options) || (options.allowPartial !== undefined && typeof options.allowPartial !== 'boolean')) {
      return fail(['allowPartial must be an explicit boolean.']);
    }
    const minimum = options.allowPartial === true ? 20 : 21;
    if (!Array.isArray(bars) || bars.length < minimum) {
      return fail(['Supply at least ' + minimum + ' completed chronological sessions; 20 returns require 21 closes.']);
    }
    const errors = [];
    const rows = Array.from(bars, (bar, i) => {
      if (!inputObject(bar)) { errors.push('Session ' + (i + 1) + ' is missing.'); return null; }
      const date = bar.date;
      if (typeof date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
          !Number.isFinite(Date.parse(date + 'T00:00:00Z')) || new Date(date + 'T00:00:00Z').toISOString().slice(0, 10) !== date) {
        errors.push('Session ' + (i + 1) + ' needs a valid YYYY-MM-DD date.');
      }
      if (bar.completed !== true) errors.push('Session ' + (i + 1) + ' must explicitly be completed.');
      const row = {date};
      for (const field of ['open', 'high', 'low', 'close', 'volume']) {
        row[field] = number(bar[field], 'Session ' + (i + 1) + ' ' + field, errors, {positive: field !== 'volume'});
      }
      if (row.low > row.high || row.open < row.low || row.open > row.high || row.close < row.low || row.close > row.high) {
        errors.push('Session ' + (i + 1) + ' has inconsistent OHLC bounds.');
      }
      return row;
    });
    for (let i = 1; i < rows.length; i++) {
      if (rows[i] && rows[i - 1] && rows[i].date <= rows[i - 1].date) errors.push('Session dates must be unique and strictly ascending.');
    }
    if (errors.length) return fail(errors);
    const last = rows[rows.length - 1];
    const trailing = rows.slice(-20);
    const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length;
    const trueRanges = rows.slice(-14).map((bar, i) => {
      const previous = rows[rows.length - 15 + i].close;
      return Math.max(bar.high - bar.low, Math.abs(bar.high - previous), Math.abs(bar.low - previous));
    });
    let realizedVolatility20Pct = null;
    if (rows.length >= 21) {
      const last21 = rows.slice(-21);
      const logs = last21.slice(1).map((bar, i) => Math.log(bar.close) - Math.log(last21[i].close));
      const average = mean(logs);
      const variance = logs.reduce((sum, value) => sum + Math.pow(value - average, 2), 0) / 19;
      realizedVolatility20Pct = Math.sqrt(variance * 252) * 100;
    }
    return result({status: 'Historical completed-session statistics, not a forecast',
      firstDate: trailing[0].date, lastDate: last.date, suppliedSessions: rows.length,
      complete: rows.length >= 21, volatilityReturnCount: rows.length >= 21 ? 20 : 19,
      return5SessionPct: (last.close / rows[rows.length - 6].close - 1) * 100,
      averageVolume20: mean(trailing.map(bar => bar.volume)),
      averageDollarVolume20: mean(trailing.map(bar => bar.close * bar.volume)),
      dollarVolumeBasis: '20-session mean close times volume proxy; not actual traded dollars',
      closeHigh20: Math.max(...trailing.map(bar => bar.close)),
      closeLow20: Math.min(...trailing.map(bar => bar.close)),
      meanTrueRange14: mean(trueRanges), realizedVolatility20Pct});
  }
  return Object.freeze({scenario, reverse, position, weighted, projectResidual, equityHurdle, marketContext});
});
