// Independent expectations from the accepted application snapshot, not widget data.
const ELIGIBLE_SIZE_STATUSES=new Set(['provider_reported','verified','dated_provider','reconciled']);
const SIZE_LABELS={large:'Large',mid:'Medium',small:'Small',micro:'Micro',unknown:'Size unverified'};
function expectedSize(company){
 const current=company.size_observation;
 if(current){
  const value=current.value_usd??current.value;
  const eligible=ELIGIBLE_SIZE_STATUSES.has(current.status)&&value!==null&&value!==undefined&&Number.isFinite(Number(value))&&Number(value)>0;
  const band=!eligible?'unknown':Number(value)>=10e9?'large':Number(value)>=2e9?'mid':Number(value)>=300e6?'small':'micro';
  return {band,label:SIZE_LABELS[band],date:current.as_of||current.source_date,value,observation:current};
 }
 const cap=company.market_cap||company.financing?.v2?.market_cap;
 const band=cap&&!cap.ratio_blocker&&cap.value!==null&&Number.isFinite(Number(cap.value))?company.market_cap_band:'unknown';
 return {band:band||'unknown',label:SIZE_LABELS[band]||SIZE_LABELS.unknown,date:cap?.as_of,value:cap?.value,observation:null};
}
module.exports={expectedSize,SIZE_LABELS};
