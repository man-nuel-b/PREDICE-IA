(()=>{'use strict';
const $=id=>document.getElementById(id);
const money=n=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0}).format(n||0);
const num=n=>new Intl.NumberFormat('es-CL',{maximumFractionDigits:1}).format(n||0);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let state=null,selected=null;
function notice(message,error=false){$('alert').textContent=message;$('alert').classList.toggle('error',error)}
async function api(url,body){
 const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),url==='/api/import'?60000:12000);
 try{const res=await fetch(url,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});
 const data=await res.json();if(!res.ok)throw Error(data.error||'Error del servidor');return data;
 }finally{clearTimeout(timeout)}
}
function render(data){
 $('motor-status').textContent='Motor local disponible';$('motor-status-dot').classList.remove('offline');
 state=data;const a=data.analysis,k=a.kpis;
 $('kpis').innerHTML=[
  ['Inventario valorizado',money(k.inventory_value),'Valor al costo de los lotes registrados'],
  ['Exposición estimada',money(k.exposure),'No equivale a pérdida realizada'],
  ['Merma observada',money(k.observed_waste_cost),'Registros históricos confirmados'],
  ['Lotes con riesgo',num(k.at_risk_lots),'Requieren revisión antes del vencimiento']]
  .map(([title,value,note])=>'<div class="metric"><div class="name">'+esc(title)+'</div><div class="value">'+esc(value)+'</div><div class="note">'+esc(note)+'</div></div>').join('');
 const risks=a.risks.slice(0,5),max=Math.max(...risks.map(x=>x.cost_exposure),1);
 $('risk-bars').innerHTML=risks.length?risks.map(x=>'<div class="bar-item"><div class="bar-label"><span>'+esc(x.name)+'</span><b>'+money(x.cost_exposure)+'</b></div><div class="bar-track"><div class="bar-fill" style="width:'+Math.min(100,Math.round(x.cost_exposure/max*100))+'%"></div></div></div>').join(''):'<p class="muted">No se detectaron excedentes potenciales en los lotes informados.</p>';
 const focus=a.recommendations.find(x=>x.recommended_order>0)||a.recommendations[0];
 $('featured').innerHTML=focus?'<div class="featured"><span class="pill '+(focus.confidence==='baja'?'pending':'suggest')+'">'+(focus.confidence==='baja'?'Revisar manualmente':'Sugerencia explicable')+'</span><h3>'+esc(focus.name)+'</h3><div class="big">'+num(focus.recommended_order)+' <small>'+esc(focus.unit)+'</small></div><p>'+esc(focus.reason)+'</p><div class="facts"><div>Datos diarios<b>'+focus.coverage*100+' %</b></div><div>Cobertura<b>'+esc(focus.confidence)+'</b></div></div><button class="table-action" data-sku="'+esc(focus.sku)+'" data-location="'+esc(focus.location)+'">Comparar escenarios</button></div>':'<p class="muted">Importa lotes para comenzar.</p>';
 $('recommendations-body').innerHTML=a.recommendations.length?a.recommendations.map(x=>'<tr><td><strong>'+esc(x.name)+'</strong><small>'+esc(x.sku)+' · '+esc(x.location)+'</small></td><td>'+num(x.daily_demand)+'</td><td>'+num(x.usable_at_delivery)+'</td><td><strong>'+num(x.recommended_order)+' '+esc(x.unit)+'</strong></td><td><span class="pill '+(x.confidence==='baja'?'pending':'suggest')+'">'+esc(x.confidence)+'</span></td><td><button class="table-action" data-sku="'+esc(x.sku)+'" data-location="'+esc(x.location)+'">Simular</button></td></tr>').join(''):'<tr><td colspan="6">Importa lotes e historial para obtener sugerencias.</td></tr>';
 $('risks-body').innerHTML=a.risks.length?a.risks.map(x=>'<tr><td><strong>'+esc(x.name)+'</strong><small>'+esc(x.code)+' · '+esc(x.location)+'</small></td><td>'+num(x.days_to_expiry)+' días</td><td>'+num(x.potential_excess)+'</td><td><b>'+money(x.cost_exposure)+'</b></td><td><span class="pill '+(x.priority==='alta'?'urgent':'low')+'">'+esc(x.priority)+'</span></td></tr>').join(''):'<tr><td colspan="5">Sin riesgos estimados con los datos actuales.</td></tr>';
 $('quality').innerHTML='<div class="section-header"><div><span class="eyebrow">TRAZABILIDAD</span><h2>Calidad y cobertura de los datos</h2></div></div><div class="quality-grid"><div>Lotes registrados<strong>'+data.datasets.lots.length+'</strong></div><div>Filas de ventas<strong>'+data.datasets.sales.length+'</strong></div><div>Eventos de merma<strong>'+data.datasets.waste.length+'</strong></div></div><p class="quality-note">'+esc(a.disclaimer)+'</p>'+(a.data_gaps.length?'<p class="quality-note">Atención: '+a.data_gaps.length+' combinaciones SKU/local sin historial suficiente; se usarán tasas manuales.</p>':'');
 if(selected){const p=a.recommendations.find(x=>x.sku===selected.sku&&x.location===selected.location);if(p)renderScenario(p)}
 document.dispatchEvent(new CustomEvent('predice:data-updated'));
 try{window.PrediceAdvancedUI?.render(data)}catch(err){console.error('No se pudo mostrar la analítica avanzada:',err)}
 notice('Datos cargados · '+data.datasets.lots.length+' lotes · cálculo realizado '+a.as_of+'. Recuerda que son estimaciones.');
}
function renderScenario(p){selected={sku:p.sku,location:p.location};const sc=p.scenarios;
 $('scenario-panel').innerHTML='<div class="section-header"><div><h3>'+esc(p.name)+' · '+esc(p.location)+'</h3><p class="muted">Pronóstico '+num(p.daily_demand)+' unidades/día. <strong>'+esc(p.decision_status==='revisar_manual'?'Revisión manual obligatoria':'Revisión humana recomendada')+'</strong>.</p></div></div><div class="scenario-cards">'+sc.map(x=>'<div class="scenario '+(x.order===p.highest_contribution_scenario.order?'positive':'')+'"><span class="eyebrow">COMPRA SIMULADA</span><b>'+num(x.order)+' '+esc(p.unit)+'</b><p>Ventas posibles: '+num(x.expected_sales)+'<br>Merma proyectada: '+num(x.estimated_waste_units)+'<br>Demanda no satisfecha: '+num(x.unmet_demand)+'</p><strong>Contribución orientativa: '+money(x.contribution_proxy)+'</strong><small>Sin costos fijos, impuestos ni validación de demanda</small></div>').join('')+'</div><p class="quality-note">'+esc(p.reason)+' El escenario destacado maximiza una aproximación de contribución; no es una orden de compra.</p>';
}
document.addEventListener('click',e=>{const b=e.target.closest('[data-sku]');if(!b||!state)return;const p=state.analysis.recommendations.find(x=>x.sku===b.dataset.sku&&x.location===b.dataset.location);if(!p)return;renderScenario(p);$('escenarios').scrollIntoView({behavior:'smooth',block:'start'})});
$('settings-form').addEventListener('submit',async e=>{e.preventDefault();const form=new FormData(e.currentTarget);const settings=Object.fromEntries(form);notice('Calculando escenarios…');try{render(await api('/api/analyze',{settings}))}catch(err){notice(err.message,true)}});
$('csv-file').addEventListener('change',()=>{
 const file=$('csv-file').files?.[0];
 $('csv-file-status').textContent=file?'Seleccionado: '+file.name+' · '+new Intl.NumberFormat('es-CL').format(file.size)+' bytes':'Ningún archivo seleccionado.';
});
$('template-button').addEventListener('click',()=>{
 try{
  const kind=$('kind').value,blob=new Blob([window.PrediceCSVImport.template(kind)],{type:'text/csv;charset=utf-8'});
  const link=document.createElement('a'),url=URL.createObjectURL(blob);
  link.href=url;link.download='predice_plantilla_'+kind+'.csv';document.body.append(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
  notice('Plantilla preparada para descargar. Completa las filas y guarda como CSV UTF-8.');
 }catch(err){notice(err.message,true)}
});
$('import-button').addEventListener('click',async()=>{
 const input=$('csv-file'),file=input.files?.[0],button=$('import-button'),kind=$('kind').value;
 if(!file)return notice('Selecciona un archivo CSV o descarga una plantilla.',true);
 const originalLabel=button.textContent;
 try{
  button.disabled=true;button.textContent='Validando archivo...';
  const result=await window.PrediceCSVImport.readFile(file,kind),rows=result.rows;
  $('csv-file-status').textContent='Validado: '+rows.length+' filas · separador '+(result.separator==='\t'?'tabulación':result.separator)+' · '+result.encoding+'.';
  const typeLabel={lots:'inventario',sales:'ventas',waste:'mermas'}[kind];
  if(!confirm('Se reemplazarán los registros de '+typeLabel+' con '+rows.length+' filas. ¿Continuar?'))return;
  notice('Guardando '+rows.length+' filas…');button.textContent='Importando...';
  const response=await api('/api/import',{kind,rows});
  render(response);input.value='';
  $('csv-file-status').textContent='Importación completada: '+rows.length+' filas ('+file.name+').';
  notice('Archivo cargado correctamente: '+rows.length+' filas. Los indicadores y gráficos se actualizaron.');
 }catch(err){
  notice('No se pudo cargar el archivo: '+(err.name==='AbortError'?'La importación tardó demasiado. Intenta un CSV más pequeño.':err.message),true);
 }finally{button.disabled=false;button.textContent=originalLabel}
});
$('reset-button').addEventListener('click',async()=>{if(!confirm('¿Reemplazar todos los datos importados con los ejemplos ficticios?'))return;try{selected=null;render(await api('/api/reset',{}))}catch(err){notice(err.message,true)}});
function syncNav(){const current=location.hash||'#panel';for(const link of document.querySelectorAll('.nav a')){const selected=link.getAttribute('href')===current;link.classList.toggle('active',selected);if(selected)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current')}}
window.addEventListener('hashchange',syncNav);syncNav();
api('/api/data').then(render).catch(e=>{$('motor-status').textContent='Servidor local no disponible';$('motor-status-dot').classList.add('offline');notice('No se pudo conectar con el servidor local: '+e.message,true)});
})();
