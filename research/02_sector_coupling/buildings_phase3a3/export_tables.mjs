import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root=new URL('.',import.meta.url);
const column=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
const outputs=[['FIX_TEST_MATRIX','BUILDINGS_FIX_TEST_MATRIX'],['DATA_CANDIDATES','ASEAN_BUILDINGS_DATA_CANDIDATES'],['DATA_REGISTRY_UPDATED','BUILDINGS_DATA_REGISTRY_UPDATED']];
const receipt=[];
for(const [input,output] of outputs){
  const records=JSON.parse(await fs.readFile(new URL(`data/derived/buildings/${input}.json`,root),'utf8'));
  const fields=Object.keys(records[0]);
  const wb=Workbook.create(); const sheet=wb.worksheets.add('Audit');
  const range=sheet.getRange(`A1:${column(fields.length)}${records.length+1}`);
  const values=[fields,...records.map(r=>fields.map(f=>r[f]??''))];
  range.values=values;
  if(JSON.stringify(range.values)!==JSON.stringify(values))throw new Error(`${output}: value roundtrip mismatch`);
  const inspected=await wb.inspect({kind:'table',range:`Audit!A1:${column(Math.min(fields.length,5))}3`,tableMaxRows:3,tableMaxCols:5,maxChars:1200});
  const csv='\uFEFF'+range.values.map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n';
  await fs.writeFile(new URL(`${output}.csv`,root),csv,'utf8');
  receipt.push({output,rows:records.length,columns:fields.length,authoring:'Artifact Tool',typed_values_roundtrip:true,csv_plain_table:true});
}
await fs.writeFile(new URL('evidence/TABLE_EXPORT_RECEIPT.json',root),JSON.stringify(receipt,null,2));
console.log(JSON.stringify(receipt));
