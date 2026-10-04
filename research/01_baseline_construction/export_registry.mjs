import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root=new URL('.',import.meta.url);
const payload=JSON.parse(await fs.readFile(new URL('REGISTRY_RECORDS.json',root),'utf8'));
const wb=Workbook.create();
const column=n=>{let s='';for(;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;};
const escape=x=>'"'+String(x??'').replaceAll('"','""')+'"';
for(const [path,rows] of Object.entries(payload)){
  const fields=Object.keys(rows[0]);
  const matrix=[fields,...rows.map(r=>fields.map(f=>r[f]??''))];
  const sheet=wb.worksheets.add(path.split('/').at(-1).replace('.csv','').slice(0,31));
  const range=sheet.getRange(`A1:${column(fields.length)}${matrix.length}`);
  range.values=matrix;
  const authored=range.values;
  const url=new URL(path,root);await fs.mkdir(new URL('.',url),{recursive:true});
  await fs.writeFile(url,'\uFEFF'+authored.map(r=>r.map(escape).join(',')).join('\r\n')+'\r\n','utf8');
  console.log(JSON.stringify({file:path,rows:rows.length,columns:fields.length}));
}
