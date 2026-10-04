import fs from 'node:fs/promises';
import {Workbook} from '@oai/artifact-tool';
const base=new URL('./',import.meta.url);
const tables=JSON.parse(await fs.readFile(new URL('build/tables.json',base),'utf8'));
const receipts=[];
for(const [name,table] of Object.entries(tables)){
  const wb=Workbook.create(),sh=wb.worksheets.add('Audit');sh.showGridLines=false;
  const values=table.export_values;
  const range=sh.getRangeByIndexes(0,0,values.length,values[0].length);range.values=values;
  if(JSON.stringify(range.values)!==JSON.stringify(values))throw Error('Roundtrip mismatch '+name);
  const view=sh.getRange('A1:D5');view.format.font={name:'Arial',size:11};view.format.wrapText=true;
  view.format.columnWidth=48;view.format.rowHeight=96;
  sh.getRange('A1:D1').format.font={name:'Arial',size:11,bold:true};
  wb.recalculate();
  const inspected=await wb.inspect({kind:'table',range:'Audit!A1:D5',include:'values',tableMaxRows:5,tableMaxCols:4,maxChars:1600});
  const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!',options:{useRegex:true,maxResults:10},maxChars:200});
  const preview=await wb.render({sheetName:'Audit',range:'A1:D5',scale:1,format:'png'});
  await fs.mkdir(new URL('evidence/previews/',base),{recursive:true});
  await fs.writeFile(new URL('evidence/previews/'+name+'.png',base),new Uint8Array(await preview.arrayBuffer()));
  const quote=x=>'"'+String(x??'').replaceAll('"','""')+'"';
  await fs.writeFile(new URL('stage/research/04_model_assembly/gate3/'+name,base),'\uFEFF'+range.values.map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n','utf8');
  receipts.push({name,rows:values.length-1,columns:values[0].length,roundtrip:true,inspection:inspected.ndjson,error_scan:errors.ndjson});
  console.log(name+': '+(values.length-1)+' rows');
}
await fs.writeFile(new URL('evidence/CSV_EXPORT_RECEIPT.json',base),JSON.stringify({authoring:'@oai/artifact-tool',receipts},null,2));
