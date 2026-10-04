import fs from 'node:fs/promises';
import { Workbook } from '@oai/artifact-tool';
const root = new URL('.', import.meta.url);
const payload = JSON.parse(await fs.readFile(new URL('ledger_records.json',root),'utf8'));
const wb=Workbook.create();
if(process.argv.includes('--help-csv')) { console.log(wb.help('*',{search:'exportCsv|toCSV|toCsv',include:'index,examples,notes',maxChars:2500}).ndjson); process.exit(0); }
const sh=wb.worksheets.add('Data ledger');
const matrix=[payload.fields,...payload.rows.map(r=>payload.fields.map(f=>r[f]??''))];
sh.getRange(`A1:AB${matrix.length}`).values=matrix;
wb.recalculate();
// CSV has no formatting or formulas. Serialize the authored cell values losslessly.
const authored=sh.getRange(`A1:AB${matrix.length}`).values;
const escape=x=>'"'+String(x??'').replaceAll('"','""')+'"';
await fs.writeFile(new URL('DATA_LEDGER.csv',root),'\uFEFF'+authored.map(r=>r.map(escape).join(',')).join('\r\n')+'\r\n','utf8');
console.log(JSON.stringify({records:authored.length-1,columns:payload.fields.length,format:'CSV',allFinalValuesBlank:payload.rows.every(r=>r.Final_Value==='')}));
