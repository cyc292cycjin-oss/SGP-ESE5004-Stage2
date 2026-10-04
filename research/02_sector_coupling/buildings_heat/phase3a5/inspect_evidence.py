from pathlib import Path
import json,re
from pypdf import PdfReader
import pypdfium2 as pdfium
R=Path(__file__).resolve().parent
raw=R/'data/raw/buildings';out=R/'data/processed/buildings';out.mkdir(parents=True,exist_ok=True)
selected={};hits={}
specs={'malaysia-neb2016.pdf':[92,93,94,95,98,99,100,101,102,103],
 'eria-pilot2013.pdf':[49,56,57], 'belda-eceee2017.pdf':[2,3,5,6],
 'ember-methodology.pdf':[9,10,49,58,71,78,84,91]}
for name,pages in specs.items():
    doc=PdfReader(raw/name)
    selected[name]={str(i):doc.pages[i-1].extract_text() for i in pages}
for name,terms in {'aeo8.pdf':['3,036','3036','1,658','1658','electricity demand','own use','own-use','electrification'],
                   'malaysia-neb2016.pdf':['41.868','conversion factor','efficiency','weighted','survey'],
                   'heesi2019.pdf':['household','water heating','space heating','cooking'],
                   'cambodia-energy-statistics.pdf':['water heating','space heating','cooking']}.items():
    hits[name]=[]
    for i,p in enumerate(PdfReader(raw/name).pages):
        text=p.extract_text();low=text.lower()
        for term in terms:
            at=low.find(term)
            if at>=0:hits[name].append(dict(page=i+1,term=term,context=text[max(0,at-220):at+680]))
(out/'SELECTED_PAGES.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf8')
(out/'TERM_LOCATIONS.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf8')
pre=R/'evidence/previews';pre.mkdir(parents=True,exist_ok=True)
doc=pdfium.PdfDocument(raw/'malaysia-neb2016.pdf')
for page in [95,103]:doc[page-1].render(scale=1.4).to_pil().save(pre/f'MY_page{page}.png')
print(json.dumps(dict(selected_pages={k:list(v) for k,v in selected.items()},hit_counts={k:len(v) for k,v in hits.items()})))
