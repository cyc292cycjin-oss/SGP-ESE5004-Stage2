import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root=new URL('.',import.meta.url);
const names=['ELECTRICITY_ACCOUNTING_GLOSSARY','AEO8_ELECTRIFICATION_SCOPE_MATRIX','MALAYSIA_BUILDINGS_SOURCE_LEDGER','MALAYSIA_ELECTRIC_HEATING_EVIDENCE','MALAYSIA_HISTORICAL_DEVICE_EVIDENCE','MALAYSIA_USEFUL_HEAT_CANDIDATES','MALAYSIA_E3_CLOSURE_TEST'];
const column=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
const receipt=[];
for(const name of names){
 const records=JSON.parse(await fs.readFile(new URL(`data/derived/${name}.json`,root),'utf8'));
 const fields=Object.keys(records[0]);
 const wb=Workbook.create();const sh=wb.worksheets.add('Evidence');
 const range=sh.getRange(`A1:${column(fields.length)}${records.length+1}`);
 const numericFields=new Set(['Year','RawValue','RawElectricity','FinalElectricityGWh','FinalEnergyMWh','EndUseShare','LHS','RHS','Difference']);
 const convert=(f,v)=>numericFields.has(f)&&v!==''&&/^-?\d+(\.\d+)?$/.test(String(v))?Number(v):v;
 const values=[fields,...records.map(r=>fields.map(f=>convert(f,r[f]??'')))];range.values=values;
 if(JSON.stringify(range.values)!==JSON.stringify(values))throw Error(`Typed roundtrip failed: ${name}`);
 wb.recalculate();
 await wb.inspect({kind:'table',range:'Evidence!A1:E4',tableMaxRows:4,tableMaxCols:5,maxChars:1000});
 const shown=sh.getRange('A1:E5');
 shown.format.columnWidth=44;shown.format.rowHeight=78;shown.format.wrapText=true;
 shown.format.font={name:'Arial',size:11};sh.getRange('A1:E1').format.font={bold:true};
 wb.recalculate();
 const preview=await wb.render({sheetName:'Evidence',range:'A1:E5',scale:1,format:'png'});
 await fs.writeFile(new URL(`evidence/previews/${name}.png`,root),new Uint8Array(await preview.arrayBuffer()));
 await fs.writeFile(new URL(`${name}.csv`,root),'\uFEFF'+range.values.map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n','utf8');
 receipt.push({output:name+'.csv',rows:records.length,columns:fields.length,authoring:'@oai/artifact-tool',typed_values_roundtrip:true});
}
await fs.writeFile(new URL('evidence/TABLE_EXPORT_RECEIPT.json',root),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(receipt));
