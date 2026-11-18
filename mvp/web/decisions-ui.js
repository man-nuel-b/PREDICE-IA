/* Predice-IA: soporte de decisiones; solo lectura, sin acciones automáticas. */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=v=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0}).format(Number(v)||0);
const num=v=>new Intl.NumberFormat('es-CL',{maximumFractionDigits:1}).format(Number(v)||0);
let serial=0;
async function refresh(){
 const seq=++serial;
 const status=$('prevention-status');
 if(!status)return;
 status.textContent='Evaluando pronósticos y acciones preventivas…';
 try{
  const abort=new AbortController();
  const timer=setTimeout(()=>abort.abort(),15000);
  let response;
  try{response=await fetch('/api/decisions',{signal:abort.signal,cache:'no-store'});}finally{clearTimeout(timer)}
  if(!response.ok)throw Error('No se pudo consultar el motor preventivo');
  const data=(await response.json()).decisions;
  if(seq!==serial)return;
  const bt=data.backtesting;
  $('prevention-metrics').innerHTML=[
   ['Series evaluadas',num(bt.evaluated_series),'Con historial suficiente'],
   ['Error histórico WAPE',bt.micro_wape_percent===null?'No disponible':num(bt.micro_wape_percent)+' %','Error ponderado sobre fechas registradas'],
   ['Lotes con acciones',num(data.actions.length),'Sujeto a revisión humana'],
   ['Series sin validación',num(data.data_quality.untested_series),'Información insuficiente']
  ].map(v=>'<div class="analytics-kpi"><span>'+esc(v[0])+'</span><strong>'+esc(v[1])+'</strong><small>'+esc(v[2])+'</small></div>').join('');
  $('prevention-actions').innerHTML=data.actions.length?data.actions.slice(0,30).map(a=>
   '<tr><td><strong>'+esc(a.name)+'</strong><small>'+esc(a.lot_code)+' · '+esc(a.location)+'</small></td>'+
   '<td>'+esc(a.days_to_expiry<0?'Vencido':a.days_to_expiry+' días')+'</td><td>'+money(a.exposure_clp)+'</td>'+
   '<td><strong>'+esc(a.action)+'</strong><small>Revisión obligatoria · '+esc(a.priority)+'</small></td></tr>'
  ).join(''):'<tr><td colspan="4">Sin exposición estimada por las reglas actuales.</td></tr>';
  $('prevention-orders').innerHTML=data.purchases.length?data.purchases.map(a=>
   '<tr><td><strong>'+esc(a.name)+'</strong><small>'+esc(a.location)+'</small></td><td>'+
   (a.historic_wape_pct===null?'Sin validar':num(a.historic_wape_pct)+' %')+'</td><td>'+num(a.recommended_order)+' '+esc(a.unit)+'</td>'+
   '<td><span class="pill '+(a.decision_status==='revisar_manual'?'pending':'suggest')+'">'+esc(a.decision_status==='revisar_manual'?'Revisión necesaria':'Evaluación humana')+'</span></td></tr>'
  ).join(''):'<tr><td colspan="4">Sin recomendaciones.</td></tr>';
  status.textContent='Análisis al '+data.as_of+' · Escenarios orientativos, no órdenes de compra. Datos de ejemplo si no has importado CSV.';
 }catch(err){
  if(seq!==serial)return;
  status.textContent='El centro preventivo requiere el motor local actualizado: '+err.message;
 }
}
document.addEventListener('predice:data-updated',refresh);
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',refresh);else refresh();
})();
