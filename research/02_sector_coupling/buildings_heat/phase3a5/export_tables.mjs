import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root=new URL('.',import.meta.url);
const names=['ASEAN_BUILDINGS_HISTORICAL_ELECTRIC_HEATING_MATRIX','ASEAN_BUILDINGS_ENDUSE_EVIDENCE_MATRIX','BUILDINGS_USEFUL_HEAT_INPUT_CANDIDATES'];
const column=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
const receipt=[];
for(const name of names){
 const records=JSON.parse(await fs.readFile(new URL(`data/derived/buildings/${name}.json`,root),'utf8'));
 const fields=Object.keys(records[0]);
 const wb=Workbook.create();const sh=wb.worksheets.add('Evidence');
 const range=sh.getRange(`A1:${column(fields.length)}${records.length+1}`);
 const values=[fields,...records.map(r=>fields.map(f=>r[f]??''))];range.values=values;
 if(JSON.stringify(range.values)!==JSON.stringify(values))throw Error(`Typed roundtrip failed: ${name}`);
 await wb.inspect({kind:'table',range:`Evidence!A1:E4`,tableMaxRows:4,tableMaxCols:5,maxChars:1000});
 await fs.writeFile(new URL(`${name}.csv`,root),'\uFEFF'+range.values.map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n','utf8');
 receipt.push({output:name+'.csv',rows:records.length,columns:fields.length,authoring:'@oai/artifact-tool',typed_values_roundtrip:true});
}
await fs.writeFile(new URL('evidence/TABLE_EXPORT_RECEIPT.json',root),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(receipt));
