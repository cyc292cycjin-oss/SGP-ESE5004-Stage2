import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root=new URL('.',import.meta.url);
const column=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
for(const [input,output] of [['ACCOUNTING_RECORDS','BUILDINGS_DEMAND_ACCOUNTING'],['REGISTRY_RECORDS','BUILDINGS_DATA_REGISTRY']]) {
  const records=JSON.parse(await fs.readFile(new URL(`data/derived/buildings/${input}.json`,root),'utf8'));
  const fields=Object.keys(records[0]);
  const wb=Workbook.create();const sheet=wb.worksheets.add('Audit');
  const range=sheet.getRange(`A1:${column(fields.length)}${records.length+1}`);
  range.values=[fields,...records.map(r=>fields.map(f=>r[f]??''))];
  await fs.writeFile(new URL(`${output}.csv`,root),'\uFEFF'+range.values.map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({output,rows:records.length,columns:fields.length,authoring:'Artifact Tool',all_human_pending:true}));
}
