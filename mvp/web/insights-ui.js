(()=>{'use strict';
const $=id=>document.getElementById(id);
const fmt=n=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0}).format(Number(n)||0);
const num=n=>new Intl.NumberFormat('es-CL',{maximumFractionDigits:1}).format(Number(n)||0);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let serial=0;
async function refresh(){
 const run=++serial,status=$('insights-status');if(!status)return;
 status.textContent='Actualizando análisis del motor local…';
 try{
  const ctrl=new AbortController();const timeout=setTimeout(()=>ctrl.abort(),12000);
  let res;
  try{res=await fetch('/api/insights',{signal:ctrl.signal,cache:'no-store'})}finally{clearTimeout(timeout)}
  if(!res.ok)throw Error('El servidor no pudo calcular los indicadores');
  const data=(await res.json()).insights;if(run!==serial)return;
  status.textContent='Análisis descriptivo · '+esc(data.as_of)+' · Revisar cada acción antes de ejecutarla';
  const categories=$('insights-categories'),pareto=$('insights-pareto'),diagnostics=$('insights-diagnostics'),prices=$('insights-prices'),alerts=$('insights-alerts');
  categories.innerHTML=data.exposure_by_category.length?data.exposure_by_category.map(x=>'<tr><td>'+esc(x.category)+'</td><td>'+fmt(x.clp)+'</td></tr>').join(''):'<tr><td colspan="2">Sin exposición estimada.</td></tr>';
  pareto.innerHTML=data.pareto.length?data.pareto.slice(0,12).map(x=>'<tr><td>'+esc(x.sku)+' · '+esc(x.location)+'</td><td>'+fmt(x.exposure_clp)+'</td><td>'+num(x.cumulative_share_pct)+' %</td></tr>').join(''):'<tr><td colspan="3">No hay lotes en riesgo.</td></tr>';
  diagnostics.innerHTML=data.diagnostics.length?data.diagnostics.map(x=>'<tr><td>'+esc(x.sku)+' · '+esc(x.location)+'</td><td>'+fmt(x.observed_waste_clp)+'</td><td>'+esc(x.hypotheses.join(' ')||'Sin observaciones con los datos disponibles')+'</td></tr>').join(''):'<tr><td colspan="3">Importa lotes para comenzar.</td></tr>';
  prices.innerHTML=data.price_scenarios.length?data.price_scenarios.slice(0,20).map(x=>'<tr><td>'+esc(x.lot_code)+'</td><td>'+num(x.days_to_expiry)+' días</td><td>'+x.scenarios.map(s=>esc(s.discount_pct)+'%: '+fmt(s.price_clp)+(s.meets_unit_cost_floor?'':' (bajo costo)')).join(' · ')+'</td></tr>').join(''):'<tr><td colspan="3">Sin descuentos simulables para lotes vigentes con margen positivo.</td></tr>';
  alerts.innerHTML=data.alerts.length?data.alerts.map(x=>'<li><strong>'+esc(x.lot_code)+' · '+esc(x.location)+'</strong> — '+esc(x.message)+'</li>').join(''):'<li>No hay alertas urgentes según el inventario cargado.</li>';
 }catch(error){if(run!==serial)return;status.textContent='No se pudieron actualizar los análisis: '+error.message}
}
document.addEventListener('DOMContentLoaded',refresh);
document.addEventListener('predice:data-updated',refresh);
})();