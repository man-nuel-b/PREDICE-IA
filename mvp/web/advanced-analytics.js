/* Predice-IA: estadística descriptiva para analítica visual.
   No modifica el motor de predicciones ni afirma precisión/ahorros. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.PrediceAdvancedAnalytics=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const iso=/^\d{4}-\d{2}-\d{2}$/;
  const n=value=>{const x=Number(value);return Number.isFinite(x)&&x>=0?x:0};
  const addDays=(date,days)=>{const d=new Date(date+'T00:00:00Z');if(!Number.isFinite(d.valueOf()))throw Error('Fecha inválida');d.setUTCDate(d.getUTCDate()+days);return d.toISOString().slice(0,10)};
  const groupKey=(sku,location)=>String(sku)+'\u0000'+String(location);
  const pct=(part,whole)=>whole>0?Math.round(part/whole*1000)/10:null;
  function analyze(snapshot,{days=28,location='all'}={}){
    if(![7,28,56].includes(Number(days)))throw Error('Periodo inválido');
    const span=Number(days);
    if(!snapshot||!snapshot.datasets||!snapshot.analysis||!iso.test(snapshot.analysis.as_of||''))throw Error('Datos insuficientes para el análisis');
    const {lots=[],sales=[],waste=[]}=snapshot.datasets;
    const {risks=[],recommendations=[]}=snapshot.analysis;
    const asOf=snapshot.analysis.as_of;
    const start=addDays(asOf,1-span);
    const locations=[...new Set([...lots,...sales,...waste].map(r=>r.location).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'es'));
    if(location!=='all'&&!locations.includes(location))location='all';
    const matches=r=>location==='all'||r.location===location;
    const windowDate=(d)=>typeof d==='string'&&iso.test(d)&&d>=start&&d<=asOf;
    const inPeriod=(rows,key)=>rows.filter(r=>matches(r)&&windowDate(r[key]));
    const currentLots=lots.filter(matches),currentRisks=risks.filter(matches),currentRecommendations=recommendations.filter(matches);
    const datedWaste=inPeriod(waste,'occurred_on'),datedSales=inPeriod(sales,'sold_on');
    const byProduct=new Map();
    const categoryByProduct=new Map();
    for(const lot of currentLots){
      const k=groupKey(lot.sku,lot.location);
      categoryByProduct.set(k,lot.category||'Sin categoría');
      if(!byProduct.has(k))byProduct.set(k,lot.name||lot.sku);
    }
    const buckets=Array.from({length:span/7},(_,i)=>({
      index:i,from:addDays(start,7*i),to:addDays(start,7*i+6),
      wasteCost:0,salesValue:0,salesUnits:0,missingSalesPrice:0,wasteEvents:0,salesRows:0
    }));
    const bucketOf=date=>Math.floor((new Date(date+'T00:00:00Z')-new Date(start+'T00:00:00Z'))/86400000/7);
    const categoryMap=new Map();
    const ensureCategory=cat=>{if(!categoryMap.has(cat))categoryMap.set(cat,{name:cat,inventory:0,exposure:0,observedWaste:0,recordedSales:0});return categoryMap.get(cat)};
    for(const lot of currentLots){ensureCategory(lot.category||'Sin categoría').inventory+=n(lot.quantity)*n(lot.unit_cost)}
    for(const risk of currentRisks){const cat=categoryByProduct.get(groupKey(risk.sku,risk.location))||'Sin categoría';ensureCategory(cat).exposure+=n(risk.cost_exposure)}
    let wasteCost=0,positiveSalesValue=0,missingSalesPrice=0,totalSalesRows=datedSales.length;
    for(const w of datedWaste){
      const value=n(w.quantity)*n(w.unit_cost);wasteCost+=value;
      ensureCategory(categoryByProduct.get(groupKey(w.sku,w.location))||'Sin categoría').observedWaste+=value;
      const b=buckets[bucketOf(w.occurred_on)];if(b){b.wasteCost+=value;b.wasteEvents++}
    }
    for(const s of datedSales){
      const price=n(s.unit_price);const value=n(s.quantity)*price;
      if(price<=0)missingSalesPrice++;else positiveSalesValue+=value;
      ensureCategory(categoryByProduct.get(groupKey(s.sku,s.location))||'Sin categoría').recordedSales+=value;
      const b=buckets[bucketOf(s.sold_on)];if(b){b.salesValue+=value;b.salesUnits+=n(s.quantity);b.salesRows++;if(price<=0)b.missingSalesPrice++}
    }
    const riskByProduct=new Map();
    for(const r of currentRisks){
      const k=groupKey(r.sku,r.location);
      if(!riskByProduct.has(k))riskByProduct.set(k,{sku:r.sku,location:r.location,name:r.name||byProduct.get(k)||r.sku,exposure:0,lots:0});
      const item=riskByProduct.get(k);item.exposure+=n(r.cost_exposure);item.lots++;
    }
    const pareto=[...riskByProduct.values()].sort((a,b)=>b.exposure-a.exposure||a.sku.localeCompare(b.sku));
    const totalExposure=pareto.reduce((sum,r)=>sum+r.exposure,0);
    let cumulative=0;for(const r of pareto){cumulative+=r.exposure;r.share=pct(r.exposure,totalExposure);r.cumulative=pct(cumulative,totalExposure)}
    const demand=currentRecommendations.map(r=>({
      sku:r.sku,location:r.location,name:r.name,daily:n(r.daily_demand),
      volatility:n(r.daily_demand)>0?pct(n(r.daily_sigma),n(r.daily_demand)):null,
      coverage:pct(n(r.coverage),1),confidence:r.confidence||'baja',
      recommendedOrder:n(r.recommended_order),decisionStatus:r.decision_status
    })).sort((a,b)=>(b.volatility??-1)-(a.volatility??-1));
    const averageCoverage=demand.length?demand.reduce((s,r)=>s+n(r.coverage),0)/demand.length:null;
    const lowData=demand.filter(r=>r.confidence==='baja').length;
    return {
      location,locations,days:span,from:start,to:asOf,
      metrics:{observedWaste:wasteCost,recordedSales:missingSalesPrice?null:positiveSalesValue,
        partiallyPricedSales:positiveSalesValue,missingSalesPrice,salesRows:totalSalesRows,
        riskExposure:totalExposure,atRiskLots:currentRisks.length,
        riskTopThreeShare:pct(pareto.slice(0,3).reduce((s,r)=>s+r.exposure,0),totalExposure),
        averageCoverage,lowData,recommendationCount:demand.length},
      buckets,pareto,demand,
      categories:[...categoryMap.values()].sort((a,b)=>b.exposure-a.exposure||b.observedWaste-a.observedWaste),
      notes:[
        'Merma observada: eventos registrados al costo en el periodo seleccionado.',
        'Exposición estimada: cálculo actual del motor para lotes en riesgo, independiente del periodo.',
        'Ventas registradas: ingresos brutos de registros con precio válido; los días ausentes no se asumen sin ventas.',
        'Variabilidad: desviación diaria estimada dividida por demanda media, no es precisión del pronóstico.',
        'No se calculan ahorros logrados ni probabilidades calibradas.'
      ]
    };
  }
  return Object.freeze({analyze,addDays,pct});
});
