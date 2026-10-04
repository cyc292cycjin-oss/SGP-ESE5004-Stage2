import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root=new URL('.',import.meta.url);
const registry=new URL('../../../../data_registry/buildings_phase3a4/',root);
await fs.mkdir(registry,{recursive:true});
const column=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
const outputs=[['COMBINED_MATRIX',root,'BUILDINGS_FIX_COMBINED_TEST_MATRIX'],
 ['E3_REQUIREMENTS',registry,'BUILDINGS_E3_DATA_REQUIREMENTS'],
 ['USEFUL_HEAT_SCHEMA',registry,'BUILDINGS_USEFUL_HEAT_INPUT_SCHEMA']];
const receipt=[];
for(const [input,dest,output] of outputs){
 const records=JSON.parse(await fs.readFile(new URL(`derived/${input}.json`,root),'utf8'));
 const fields=Object.keys(records[0]);
 const wb=Workbook.create();const sheet=wb.worksheets.add('Audit');
 const range=sheet.getRange(`A1:${column(fields.length)}${records.length+1}`);
 const values=[fields,...records.map(r=>fields.map(f=>r[f]??''))];range.values=values;
 if(JSON.stringify(range.values)!==JSON.stringify(values))throw new Error('Typed value roundtrip mismatch');
 await wb.inspect({kind:'table',range:`Audit!A1:${column(Math.min(fields.length,5))}3`,tableMaxRows:3,tableMaxCols:5,maxChars:1000});
 await fs.writeFile(new URL(`${output}.csv`,dest),'\uFEFF'+range.values.map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n','utf8');
 receipt.push({output,rows:records.length,columns:fields.length,authoring:'Artifact Tool',typed_values_roundtrip:true});
}
const fields=JSON.parse(await fs.readFile(new URL('derived/INPUT_TEMPLATE_FIELDS.json',root),'utf8'));
const wb=Workbook.create();const sheet=wb.worksheets.add('Input template');
sheet.getRange(`A1:${column(fields.length)}1`).values=[fields];
await fs.writeFile(new URL('BUILDINGS_USEFUL_HEAT_INPUT_TEMPLATE.csv',registry),'\uFEFF'+fields.map(quote).join(',')+'\r\n','utf8');
receipt.push({output:'BUILDINGS_USEFUL_HEAT_INPUT_TEMPLATE',rows:0,columns:fields.length,authoring:'Artifact Tool',scientific_inputs:false});
await fs.writeFile(new URL('evidence/TABLE_EXPORT_RECEIPT.json',root),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(receipt));
