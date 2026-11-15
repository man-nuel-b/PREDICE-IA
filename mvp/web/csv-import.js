/* Predice-IA · importación CSV compatible con exportaciones Excel de Chile.
 * Pure parser (no DOM, no network, no writes). Server remains authoritative.
 */
(function (root, factory) {
  const parser = factory();
  if (typeof module === 'object' && module.exports) module.exports = parser;
  if (root) root.PrediceCSVImport = parser;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const MAX_ROWS = 20000;
  const REQUIRED = {
    lots: ['code','sku','name','category','location','unit','quantity','unit_cost','unit_price','expires_on'],
    sales: ['sku','location','sold_on','quantity'],
    waste: ['sku','location','occurred_on','quantity','unit_cost']
  };
  const LABELS = {
    code:['code','codigo_lote','lote','codigo'],
    sku:['sku','codigo_producto','cod_producto','id_producto'],
    name:['name','nombre','producto','nombre_producto'],
    category:['category','categoria','familia'],
    location:['location','local','sucursal','ubicacion'],
    unit:['unit','unidad','unidad_medida'],
    quantity:['quantity','cantidad','unidades'],
    unit_cost:['unit_cost','costo_unitario','coste_unitario','costo'],
    unit_price:['unit_price','precio_venta','precio_unitario','precio'],
    expires_on:['expires_on','fecha_vencimiento','vencimiento','fecha_caducidad'],
    sold_on:['sold_on','fecha_venta','fecha_de_venta'],
    occurred_on:['occurred_on','fecha_merma','fecha_perdida','fecha'],
    manual_daily_sales:['manual_daily_sales','venta_diaria_estimada','ventas_diarias_estimadas'],
    shelf_life_days:['shelf_life_days','vida_util_dias','dias_vida_util']
  };
  const numberFields = new Set(['quantity','unit_cost','unit_price','manual_daily_sales','shelf_life_days']);
  const dateFields = new Set(['expires_on','sold_on','occurred_on']);
  const fieldMap = new Map();
  for (const [field, aliases] of Object.entries(LABELS)) for (const alias of aliases) fieldMap.set(alias,field);
  const key = s=>String(s).trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[ .\-]+/g,'_');
  function countFields(line,sep) {
    let count=0,quote=false;
    for(let i=0;i<line.length;i++){
      const c=line[i];if(c==='"'){if(quote&&line[i+1]==='"')i++;else quote=!quote}
      else if(c===sep&&!quote)count++;
    }
    return count;
  }
  function delimiterFor(text) {
    const first=text.split(/\r?\n/).find(s=>s.trim()&&!/^sep=/i.test(s.trim()))||'';
    const candidates=[',',';','\t'];
    return candidates.sort((a,b)=>countFields(first,b)-countFields(first,a))[0];
  }
  function splitRecords(text,delimiter) {
    const out=[];let row=[],cell='',quoted=false,started=false;
    for(let i=0;i<text.length;i++){
      const c=text[i];
      if(c==='"'){
        if(quoted&&text[i+1]==='"'){cell+='"';i++}
        else if(quoted)quoted=false;
        else if(!cell.trim())quoted=true;
        else throw Error('CSV: comillas inesperadas en una columna. Reexporta el archivo como CSV UTF-8.');
      }else if(c===delimiter&&!quoted){row.push(cell);cell='';started=true}
      else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x.trim()))out.push(row);row=[];cell='';started=false}
      else{cell+=c;started=true}
    }
    if(quoted)throw Error('CSV: hay comillas sin cerrar.');
    if(started||cell||row.length){row.push(cell);if(row.some(x=>x.trim()))out.push(row)}
    return out;
  }
  function numeric(value,col,idx) {
    const raw=String(value).replace(/\s|\u00a0/g,'');
    if(!raw)return raw;
    let formatted=raw;
    // Chile: 1.234,56 -> 1234.56, 1,5 -> 1.5. Invariant 1234.56 remains unchanged.
    if(/^[-+]?\d{1,3}(?:\.\d{3})+,(?:\d+)$/.test(raw))formatted=raw.replace(/\./g,'').replace(',','.');
    else if(/^[-+]?\d{1,3}(?:,\d{3})+\.\d+$/.test(raw))formatted=raw.replace(/,/g,'');
    else if(/^[-+]?\d+(?:,\d+)$/.test(raw))formatted=raw.replace(',','.');
    else if(/^[-+]?\d+(?:\.\d+)?$/.test(raw))formatted=raw;
    else throw Error('Fila '+idx+', '+col+': número "'+value+'" no reconocido.');
    if(!Number.isFinite(Number(formatted)))throw Error('Fila '+idx+', '+col+': valor fuera de rango.');
    return formatted;
  }
  function isoDate(value,col,idx) {
    const v=String(value).trim();
    if(/^\d{4}-\d{2}-\d{2}$/.test(v))return v;
    const m=v.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/);
    if(m){const d=Number(m[1]),mo=Number(m[2]);if(d<1||d>31||mo<1||mo>12)throw Error('Fila '+idx+', '+col+': fecha inválida');return m[3]+'-'+String(mo).padStart(2,'0')+'-'+String(d).padStart(2,'0')}
    throw Error('Fila '+idx+', '+col+': fecha "'+v+'" no reconocida. Usa AAAA-MM-DD o DD/MM/AAAA.');
  }
  function parse(text,kind) {
    if(!Object.prototype.hasOwnProperty.call(REQUIRED,kind))throw Error('Selecciona el tipo de archivo correcto.');
    if(typeof text!=='string')throw Error('El contenido del archivo debe ser texto.');
    text=text.replace(/^\ufeff/,'').replace(/\u0000/g,'');
    const sepLine=text.match(/^sep=([;,\t])\s*(?:\r?\n|\r)/i);
    const delimiter=sepLine?sepLine[1]:delimiterFor(text);
    if(sepLine)text=text.slice(sepLine[0].length);
    const matrix=splitRecords(text,delimiter);
    if(matrix.length<2)throw Error('El CSV debe incluir encabezados y al menos una fila.');
    if(matrix.length-1>MAX_ROWS)throw Error('El CSV supera el máximo de 20.000 filas.');
    const head=matrix.shift().map(x=>x.trim());
    const normalized=head.map(x=>fieldMap.get(key(x))||key(x));
    if(normalized.some(x=>!x)||new Set(normalized).size!==normalized.length)throw Error('Hay encabezados vacíos o repetidos. Revisa las columnas del CSV.');
    const missing=REQUIRED[kind].filter(x=>!normalized.includes(x));
    if(missing.length)throw Error('Faltan columnas requeridas: '+missing.join(', ')+'. Descarga la plantilla para '+({lots:'inventario',sales:'ventas',waste:'mermas'}[kind])+'.');
    const rows=matrix.map((fields,i)=>{
      const rowNo=i+2;
      if(fields.length!==head.length)throw Error('Fila '+rowNo+': tiene '+fields.length+' columnas y se esperaban '+head.length+'. Revisa el separador y las comillas.');
      const record={};
      normalized.forEach((col,j)=>{
        let value=fields[j].trim();
        if(numberFields.has(col))value=numeric(value,col,rowNo);
        if(dateFields.has(col))value=isoDate(value,col,rowNo);
        record[col]=value;
      });
      return record;
    });
    return {rows,separator:delimiter,columns:normalized};
  }
  async function readFile(file,kind) {
    if(!file)throw Error('Selecciona primero un archivo.');
    if(/\.xlsx?$|\.ods$/i.test(file.name||''))throw Error('Este MVP no recibe archivos Excel (.xlsx). En Excel elige Archivo → Guardar como → CSV UTF-8 y carga ese CSV.');
    if(!/\.(csv|txt)$/i.test(file.name||''))throw Error('Formato no compatible. Usa un archivo .csv exportado desde Excel.');
    if(file.size>4*1024*1024)throw Error('El archivo supera 4 MB. Divide los registros en archivos más pequeños.');
    if(file.size===0)throw Error('El archivo seleccionado está vacío.');
    const bytes=await file.arrayBuffer();const buf=new Uint8Array(bytes);
    let text='',encoding='UTF-8';
    if(buf[0]===0xff&&buf[1]===0xfe){text=new TextDecoder('utf-16le',{fatal:true}).decode(bytes);encoding='UTF-16 LE';}
    else if(buf[0]===0xfe&&buf[1]===0xff){text=new TextDecoder('utf-16be',{fatal:true}).decode(bytes);encoding='UTF-16 BE';}
    else {
      try{text=new TextDecoder('utf-8',{fatal:true}).decode(bytes)}
      catch(e){text=new TextDecoder('windows-1252').decode(bytes);encoding='Windows-1252';}
    }
    return {...parse(text,kind),encoding};
  }
  function template(kind) {
    const headers={
      lots:'code;sku;name;category;location;unit;quantity;unit_cost;unit_price;expires_on;manual_daily_sales;shelf_life_days',
      sales:'sku;location;sold_on;quantity;unit_price',
      waste:'sku;location;occurred_on;quantity;unit_cost'
    };
    if(!headers[kind])throw Error('Tipo de archivo inválido');
    return '\ufeff'+headers[kind]+'\r\n';
  }
  return Object.freeze({parse,readFile,template,REQUIRED});
});
