"""Targeted reinspection of original PDFs; no model inputs written."""
from pathlib import Path
import json,re,sys
from pypdf import PdfReader
R=Path(__file__).resolve().parent;P=R.parent/'phase3a5'
out=R/'data/processed';out.mkdir(parents=True,exist_ok=True)
specs={'aeo8.pdf':['final energy','electricity share','final electricity','electricity consumption','gross','net generation','own use','own-use','hydrogen','electric vehicles','cooling','water heating'],
       'malaysia-neb2016.pdf':['Conversion','conversion','41.868','11,630','11630','860','household','survey','Residential','Commercial']}
records={};allpages={}
for name,terms in specs.items():
 d=PdfReader(P/'data/raw/buildings'/name);rows=[];pp={}
 for i,page in enumerate(d.pages):
    t=page.extract_text();matches=[x for x in terms if x.lower() in t.lower()]
    if matches:
        pp[str(i+1)]=t
        rows.append(dict(pdf_page=i+1,terms=matches,context=t[:180].replace('\n',' ')))
 records[name]=rows;allpages[name]=pp
(out/'SOURCE_PAGE_INDEX.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf8')
(out/'PDF_PAGES.json').write_text(json.dumps(allpages,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in records.items()},ensure_ascii=True,indent=2))
