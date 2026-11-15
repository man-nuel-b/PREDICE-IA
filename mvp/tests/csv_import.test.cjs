const assert=require('node:assert/strict');
const test=require('node:test');
const m=require('./csv-import.js');
const fields='code;sku;name;category;location;unit;quantity;unit_cost;unit_price;expires_on;manual_daily_sales;shelf_life_days';
test('Excel Chile semicolon + quoted product + decimal comma',()=>{
 const src='\ufeff'+fields+'\r\nL01;MAN01;"Manzanas; rojas";Frutas;Temuco;kg;3,5;1.234,50;2.999,90;15/11/2026;0,5;7\r\n';
 const parsed=m.parse(src,'lots');
 assert.equal(parsed.separator,';');assert.equal(parsed.rows[0].name,'Manzanas; rojas');
 assert.equal(parsed.rows[0].unit_cost,'1234.50');assert.equal(parsed.rows[0].expires_on,'2026-11-15');
 assert.equal(parsed.rows[0].quantity,'3.5');
});
test('English comma CSV and newlines inside quotes',()=>{
 const txt='sku,location,sold_on,quantity,unit_price\nABC,"Local\nTemuco",2026-11-15,12.5,999.90';
 const p=m.parse(txt,'sales');assert.equal(p.rows[0].location,'Local\nTemuco');assert.equal(p.rows[0].quantity,'12.5');
});
test('Aliases in Spanish mapped to expected engine keys',()=>{
 const txt='codigo;codigo_producto;nombre;categoria;local;unidad;cantidad;costo_unitario;precio_venta;fecha_vencimiento\nL3;SKU3;Tomate;Frutas;Temuco;kg;10;500;900;01/12/2026';
 const p=m.parse(txt,'lots');assert.equal(p.rows[0].code,'L3');assert.equal(p.rows[0].sku,'SKU3');assert.equal(p.rows[0].expires_on,'2026-12-01');
});
test('explicit Excel sep=; line',()=>{
 const p=m.parse('sep=;\n'+fields+'\nL01;P01;Pan;Alimentos;Temuco;un;10;100;300;2026-11-19;2;7','lots');assert.equal(p.rows.length,1);
});
test('reject incompatible Excel with clear message',async()=>{
 await assert.rejects(()=>m.readFile({name:'productos.xlsx',size:100},'lots'),/CSV UTF-8/);
});
test('reject missing cols with actionable error',()=>assert.throws(()=>m.parse('sku;local;cantidad\nA;T;10','sales'),/Faltan columnas/));
test('reject unclosed quoted CSV',()=>assert.throws(()=>m.parse(fields+'\nL01;"bad','lots'),/comillas sin cerrar/));
test('accept Windows-1252 accents if UTF-8 fails',async()=>{
 const header='sku;local;fecha_merma;cantidad;costo_unitario\n';
 const bytes=Buffer.concat([Buffer.from(header,'utf8'),Buffer.from('PAN;Viña;15/11/2026;1;150\n','latin1')]);
 const p=await m.readFile({name:'mermas.csv',size:bytes.length,arrayBuffer:async()=>bytes},'waste');
 assert.equal(p.encoding,'Windows-1252');assert.equal(p.rows[0].location,'Viña');
});
test('generate semicolon template for each dataset',()=>{
 for(const kind of ['lots','sales','waste'])assert.match(m.template(kind),/\ufeff/);
});
