const {test}=require('node:test');
const assert=require('node:assert/strict');
const {analyze}=require('../web/advanced-analytics.js');
const snapshot={
 datasets:{
  lots:[{sku:'A',name:'Producto A',location:'Local 1',category:'Frescos',quantity:10,unit_cost:100},{sku:'B',name:'Producto B',location:'Local 2',category:'Panadería',quantity:7,unit_cost:300}],
  waste:[{sku:'A',location:'Local 1',quantity:2,unit_cost:100,occurred_on:'2026-11-12'},{sku:'A',location:'Local 1',quantity:1,unit_cost:100,occurred_on:'2026-10-01'},{sku:'B',location:'Local 2',quantity:3,unit_cost:300,occurred_on:'2026-11-12'}],
  sales:[{sku:'A',location:'Local 1',quantity:5,unit_price:200,sold_on:'2026-11-13'},{sku:'B',location:'Local 2',quantity:2,unit_price:0,sold_on:'2026-11-13'},{sku:'B',location:'Local 2',quantity:1,unit_price:300,sold_on:'2026-10-01'}]
 },
 analysis:{as_of:'2026-11-15',risks:[{sku:'A',location:'Local 1',name:'Producto A',cost_exposure:300},{sku:'A',location:'Local 1',name:'Producto A',cost_exposure:200},{sku:'B',location:'Local 2',name:'Producto B',cost_exposure:100}],recommendations:[{sku:'A',name:'Producto A',location:'Local 1',daily_demand:5,daily_sigma:2,coverage:0.75,confidence:'media',recommended_order:12},{sku:'B',name:'Producto B',location:'Local 2',daily_demand:2,daily_sigma:1,coverage:0.25,confidence:'baja',recommended_order:0}]}
};
test('28 días suma merma observada y separa exposición vigente',()=>{
 const a=analyze(snapshot,{days:28});assert.equal(a.metrics.observedWaste,1100);assert.equal(a.metrics.riskExposure,600);assert.equal(a.metrics.salesRows,2);assert.equal(a.metrics.recordedSales,null);assert.equal(a.metrics.missingSalesPrice,1);assert.equal(a.buckets.length,4);
});
test('filtra local sin mezclar otras ubicaciones',()=>{
 const a=analyze(snapshot,{days:7,location:'Local 1'});assert.equal(a.metrics.observedWaste,200);assert.equal(a.metrics.riskExposure,500);assert.equal(a.metrics.recordedSales,1000);assert.equal(a.categories.length,1);assert.equal(a.pareto.length,1);assert.equal(a.buckets.length,1);
});
test('el filtro temporal cambia históricos pero no exposición actual',()=>{
 const a=analyze(snapshot,{days:7}),b=analyze(snapshot,{days:56});assert.equal(a.metrics.riskExposure,b.metrics.riskExposure);assert.equal(a.metrics.observedWaste,1100);assert.equal(b.metrics.observedWaste,1200);
});
test('Pareto acumula exposición por SKU y ubicación una sola vez',()=>{
 const a=analyze(snapshot);assert.equal(a.pareto[0].exposure,500);assert.equal(a.pareto[0].cumulative,83.3);assert.equal(a.pareto.at(-1).cumulative,100);assert.equal(a.metrics.riskTopThreeShare,100);
});
test('sin ventas o lotes no inventa demanda ni porcentajes',()=>{
 const a=analyze({datasets:{lots:[],sales:[],waste:[]},analysis:{as_of:'2026-11-15',risks:[],recommendations:[]}},{days:7});assert.equal(a.metrics.averageCoverage,null);assert.equal(a.metrics.riskTopThreeShare,null);assert.equal(a.metrics.recordedSales,0);assert.equal(a.pareto.length,0);
});
test('rechaza periodo no previsto y no multiplica registros por cero',()=>{
 assert.throws(()=>analyze(snapshot,{days:365}),/Periodo inválido/);
 const a=analyze(snapshot,{days:7});assert.equal(a.demand.find(x=>x.sku==='A').volatility,40);
});
