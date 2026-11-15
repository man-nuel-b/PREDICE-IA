/* Predice-IA: vista y filtros de analítica avanzada, con datos de /api/data. */
(function(){
 'use strict';
 const analytics=window.PrediceAdvancedAnalytics;
 const $=id=>document.getElementById(id);
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&quot;'}[c]));
 const clp=value=>new Intl.NumberFormat('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0}).format(value||0);
 const num=value=>new Intl.NumberFormat('es-CL',{maximumFractionDigits:1}).format(value||0);
 const fmtPct=value=>value===null?'Sin datos':num(value)+' %';
 let snapshot=null,current=null;
 function setText(id,text){$(id).textContent=text}
 function labelDate(date){const [y,m,d]=date.split('-');return d+'/'+m+'/'+y.slice(-2)}
 function trendSvg(buckets,key,label,stroke){
  if(!buckets.length)return '<p class="analytics-empty">No hay periodos para graficar.</p>';
  const values=buckets.map(x=>x[key]),max=Math.max(1,...values),width=600,height=170,top=22,bottom=131,left=26,right=574;
  const points=values.map((v,i)=>({x:values.length===1?300:left+(right-left)*i/(values.length-1),y:bottom-(v/max)*(bottom-top),v}));
  const poly=points.map(p=>p.x+','+p.y).join(' '),baseline=bottom;
  const fillPath=points.length>1?'<polygon fill="'+stroke+'" opacity=".10" points="'+left+','+baseline+' '+poly+' '+right+','+baseline+'"/>':'';
  return '<svg class="analytics-chart" viewBox="0 0 600 170" role="img" aria-label="'+esc(label)+': '+esc(values.map((v,i)=>labelDate(buckets[i].from)+' '+clp(v)).join('; '))+'">'+
    '<line x1="'+left+'" y1="'+baseline+'" x2="'+right+'" y2="'+baseline+'" stroke="#7283a4" stroke-width="1"/>'+fillPath+
    (points.length>1?'<polyline points="'+poly+'" fill="none" stroke="'+stroke+'" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>':'')+
    points.map(p=>'<circle cx="'+p.x+'" cy="'+p.y+'" r="5" stroke="#1b263a" stroke-width="2" fill="'+stroke+'"><title>'+esc(clp(p.v))+'</title></circle>').join('')+
    points.map((p,i)=>'<text x="'+p.x+'" y="156" fill="#b5c5df" text-anchor="middle" font-size="10">'+esc(buckets[i].from.slice(5))+'</text>').join('')+
    '<text x="'+left+'" y="16" fill="#dce5f5" font-size="11">Máx. '+esc(clp(max))+'</text></svg>';
 }
 function renderAdvanced(){
   if(!snapshot)return;
   try{current=analytics.analyze(snapshot,{days:Number($('advanced-period').value),location:$('advanced-location').value})}
   catch(err){setText('advanced-error','No se pudo preparar el análisis: '+err.message);return}
   setText('advanced-error','');
   const a=current,m=a.metrics;
   setText('advanced-scope','Periodo: '+labelDate(a.from)+' a '+labelDate(a.to)+' · '+(a.location==='all'?'Todos los locales':a.location));
   $('advanced-kpis').innerHTML=[
     ['Merma observada',clp(m.observedWaste),'Costo registrado en '+a.days+' días'],
     ['Exposición potencial',clp(m.riskExposure),'Estimación actual; no es merma realizada'],
     ['Ventas valorizadas',m.recordedSales===null?'Parcial':clp(m.recordedSales),m.missingSalesPrice?'Faltan precios en '+m.missingSalesPrice+' fila(s); monto parcial '+clp(m.partiallyPricedSales):'Ingresos brutos de ventas registradas'],
     ['Cobertura del historial',fmtPct(m.averageCoverage),'Promedio simple de SKU/local; no es precisión de IA']
   ].map(([title,value,desc])=>'<div class="analytics-kpi"><span>'+esc(title)+'</span><strong>'+esc(value)+'</strong><small>'+esc(desc)+'</small></div>').join('');
   $('advanced-waste-trend').innerHTML=trendSvg(a.buckets,'wasteCost','Merma observada al costo', '#fda4af');
   $('advanced-sales-trend').innerHTML=trendSvg(a.buckets,'salesValue','Ventas registradas con precios válidos', '#a5b4fc');
   const maxCat=Math.max(1,...a.categories.map(r=>r.exposure));
   $('advanced-categories').innerHTML=a.categories.length?a.categories.map(r=>'<div class="analytics-category"><div class="analytics-category-header"><strong>'+esc(r.name)+'</strong><span>'+clp(r.exposure)+'</span></div><div class="analytics-track"><div style="width:'+Math.min(100,r.exposure/maxCat*100).toFixed(1)+'%"></div></div><small>Merma observada '+clp(r.observedWaste)+' · Inventario '+clp(r.inventory)+'</small></div>').join(''):'<p class="analytics-empty">No hay categorías para esta ubicación.</p>';
   const top=a.pareto.slice(0,8),maxRisk=Math.max(1,...top.map(r=>r.exposure));
   $('advanced-pareto').innerHTML=top.length?top.map(r=>'<div class="analytics-pareto-row"><div><strong>'+esc(r.name)+'</strong><small>'+esc(r.location)+' · '+esc(r.sku)+'</small></div><div class="analytics-pareto-bar"><i style="width:'+(r.exposure/maxRisk*100).toFixed(1)+'%"></i></div><div class="analytics-pareto-values">'+clp(r.exposure)+'<small>Acumulado '+fmtPct(r.cumulative)+'</small></div></div>').join(''):'<p class="analytics-empty">Sin exposición estimada para este filtro.</p>';
   const unstable=a.demand.filter(r=>r.confidence==='baja').length;
   setText('advanced-quality-note',a.demand.length?'SKU/local con datos insuficientes: '+unstable+' de '+a.demand.length+'. La variabilidad no equivale a la precisión del modelo.':'No hay productos con recomendación para este filtro.');
   $('advanced-demand').innerHTML=a.demand.length?a.demand.map(r=>'<tr><td><strong>'+esc(r.name)+'</strong><small>'+esc(r.location)+'</small></td><td>'+num(r.daily)+'</td><td>'+fmtPct(r.volatility)+'</td><td>'+fmtPct(r.coverage)+'</td><td><span class="pill '+(r.confidence==='baja'?'pending':'suggest')+'">'+esc(r.confidence)+'</span></td></tr>').join(''):'<tr><td colspan="5">No existen datos de demanda para este local.</td></tr>';
   const warnings=[];
   if(m.missingSalesPrice)warnings.push('Hay '+m.missingSalesPrice+' registros de venta sin precio positivo: el ingreso total no se considera completo.');
   if(!m.salesRows)warnings.push('No hay ventas registradas en el periodo; la falta de registros no equivale a ventas cero.');
   if(!m.riskExposure)warnings.push('No se observa exposición potencial según las reglas y datos actuales.');
   if(m.lowData)warnings.push(m.lowData+' combinaciones SKU/local requieren revisión humana por cobertura insuficiente.');
   warnings.push('La exposición potencial es un resultado vigente y no cambia al filtrar fechas históricas.');
   warnings.push('Esta sección es análisis descriptivo, no un modelo predictivo nuevo ni ahorro comprobado.');
   $('advanced-insights').innerHTML=warnings.map(t=>'<li>'+esc(t)+'</li>').join('');
 }
 function csvCell(value){let s=String(value??'');if(/^[\s]*[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"'}
 function csvLine(fields){return fields.map(csvCell).join(',')}
 function exportCsv(){
   if(!current)return;
   const a=current;
   const rows=[['Predice-IA · analítica descriptiva'],['Ubicación',a.location],['Desde',a.from],['Hasta',a.to],
     ['Advertencia','Exposición estimada: foto actual del inventario, independiente del filtro temporal'],[],
     ['Categoría','Inventario CLP','Exposición estimada CLP','Merma observada CLP']];
   for(const c of a.categories)rows.push([c.name,Math.round(c.inventory),Math.round(c.exposure),Math.round(c.observedWaste)]);
   rows.push([],['SKU','Ubicación','Producto','Exposición estimada CLP','Porcentaje acumulado']);
   for(const r of a.pareto)rows.push([r.sku,r.location,r.name,Math.round(r.exposure),r.cumulative??'']);
   rows.push([],['Semana desde','Semana hasta','Merma observada CLP','Ventas con precio CLP','Registros sin precio']);
   for(const b of a.buckets)rows.push([b.from,b.to,Math.round(b.wasteCost),Math.round(b.salesValue),b.missingSalesPrice]);
   const blob=new Blob(['\ufeff'+rows.map(csvLine).join('\r\n')],{type:'text/csv;charset=utf-8'});
   const url=URL.createObjectURL(blob),link=document.createElement('a');
   link.href=url;link.download='predice-analitica-'+a.from+'-'+a.to+'.csv';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 function init(){
   if(!$('advanced'))return;
   $('advanced-period').addEventListener('change',renderAdvanced);
   $('advanced-location').addEventListener('change',renderAdvanced);
   $('advanced-export').addEventListener('click',exportCsv);
 }
 window.PrediceAdvancedUI={render(data){
   snapshot=data;
   if(!$('advanced'))return;
   const selector=$('advanced-location'),previous=selector.value;
   const locations=[...new Set([...(data.datasets.lots||[]),...(data.datasets.sales||[]),...(data.datasets.waste||[])].map(r=>r.location).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es'));
   selector.replaceChildren(new Option('Todos los locales','all'),...locations.map(s=>new Option(s,s)));
   selector.value=locations.includes(previous)?previous:'all';
   renderAdvanced();
 }};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
