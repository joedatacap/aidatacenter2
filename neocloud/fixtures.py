"""Curated task-brief fixtures, NOT independently retrieved or current research."""
from .catalog import SOURCES

DATA = {
 "CRWV": [
  {"instrument_id":"usd-2032-notes","ticker":"CRWV","name":"9.625% senior notes due 2032",
   "currency":"USD","coupon_pct":"9.625","rate_type":"fixed",
   "excerpt":"Task brief fixture: CoreWeave issued $1.25B 9.625% 2032 senior notes in June 2026. Current outstanding principal and exact maturity date require primary-source verification."},
  {"instrument_id":"eur-2032-notes","ticker":"CRWV","name":"8.50% EUR senior notes due 2032",
   "currency":"EUR","coupon_pct":"8.50","rate_type":"fixed",
   "excerpt":"Task brief fixture: CoreWeave issued EUR 2.0B 8.50% senior notes due 2032. Current outstanding principal requires primary-source verification."}],
 "NBIS": [
  {"instrument_id":"convert-2030","ticker":"NBIS","name":"0.50% convertibles due 2030",
   "currency":"USD","coupon_pct":"0.50","rate_type":"convertible","convertible":True,
   "excerpt":"Task brief fixture: Nebius announced $3.45B 0.50% convertibles due 2030 on August 24 2026. Issuance is not a later outstanding balance. Conversion dilution is an economic risk."},
  {"instrument_id":"secured-2030","ticker":"NBIS","name":"Secured facility due October 31 2030",
   "currency":"USD","commitment_amount":"775000000","rate_type":"floating",
   "reference_index":"SOFR","spread_bps":"250","maturity":"2030-10-31",
   "excerpt":"Task brief fixture: Nebius July 17 2026 secured facility approximately $775M, SOFR plus 250 basis points, matures October 31 2030. Drawn balance and hedge status are unverified."}],
 "IREN": [
  {"instrument_id":"gpu-ddtl","ticker":"IREN","name":"GPU financing DDTL",
   "currency":"USD","commitment_amount":"1500000000","drawn_amount":"413000000",
   "rate_type":"floating","reference_index":"1-month SOFR","spread_bps":"225",
   "excerpt":"Task brief fixture: IREN GPU DDTL commitment approximately $1.5B at 1-month SOFR plus 225 basis points. $413M drawn June 30 2026; roughly $394M forward swap, effective terms require verification."},
  {"instrument_id":"gpu-notes","ticker":"IREN","name":"GPU private secured notes",
   "currency":"USD","coupon_pct":"5.96","rate_type":"fixed","secured":True,
   "excerpt":"Task brief fixture: IREN GPU financing included approximately $2.1B private secured notes at 5.96% fixed. Outstanding balance and exact maturity require primary-source verification."}],
 "BTDR": []
}

def bundle(ticker):
    items = DATA[ticker]
    return [{"url":SOURCES[ticker][0],"status":"fixture","title":"Curated HACKATHON_TASK.md fixture",
             "retrieved_at":"2026-10-17T00:00:00+00:00",
             "text":" ".join(i["excerpt"] for i in items)}] if items else []


class SimulatedModel:
    async def json(self, instruction, context):
        completed = [t for t in context["tasks"] if t["status"]=="completed"]
        if "Research Manager" in instruction:
            if not any(t["role"]=="debt" for t in completed):
                return {"tasks":[{"role":role,"ticker":ticker,"goal":"Simulated " + role + " investigation"}
                                  for ticker in context["tickers"] for role in ("debt","deals","markets")],
                        "reason":"SIMULATED manager plan; no Crusoe call"}
            auditors = [t for t in completed if t["role"]=="auditor"]
            if not auditors:
                return {"tasks":[{"role":"auditor","ticker":t,"goal":"Challenge missing balances and hedge evidence"} for t in context["tickers"]],
                        "reason":"SIMULATED review"}
            if not any(t["role"]=="followup" for t in completed):
                return {"tasks":[{"role":"followup","ticker":auditors[0]["ticker"],
                                  "parent_task_id":auditors[0]["id"],
                                  "goal":"Verify auditor concern: outstanding balance and effective hedge dates"}],
                        "reason":"SIMULATED recursive follow-up; not evidence of live Crusoe recursion"}
            if not any(t["role"]=="dossier" for t in completed):
                return {"tasks":[{"role":"dossier","ticker":context["tickers"][0],
                                  "goal":"Summarize risk dimensions and unresolved disclosure gaps"}],
                        "reason":"SIMULATED dossier"}
            return {"finish":True,"reason":"SIMULATED workflow complete; fixtures remain unverified"}
        assignment = context["assignment"]
        ticker = assignment["ticker"]
        if assignment["role"] in ("debt","followup"):
            evidence, instruments = [],[]
            for index,item in enumerate(DATA[ticker]):
                evidence.append({"source_index":0,"excerpt":item["excerpt"],"claim":item["name"],"confidence":"low"})
                instruments.append({k:v for k,v in item.items() if k!="excerpt"} | {"evidence_refs":[index]})
            return {"summary":"SIMULATED fixture extraction; live primary-source verification required.",
                    "evidence":evidence,"instruments":instruments,"concerns":["Outstanding balances and hedge effectiveness unverified."]}
        if assignment["role"]=="markets":
            return {"summary":"Market data unavailable. No invented quotes or performance."}
        if assignment["role"]=="deals":
            return {"summary":"No verified customer deal yet. Financing linkage unverified."}
        if assignment["role"]=="auditor":
            return {"summary":"Disclosure incomplete.","concerns":["Issuance sizes cannot establish outstanding principal. Hedge dates require verification."]}
        return {"summary":"SIMULATED dossier: compare recourse, floating exposure, hedge terms, refinancing horizon and dilution only where evidence exists. No definitive risk ranking is supported.",
                "concerns":context["rule_objections"]}
