"""Record exact PDF locations and rendering receipts, not a replacement dataset.
Uses the bundled desktop Python (pypdf and pypdfium2); no environment installation.
"""
from pathlib import Path
import hashlib,json
from pypdf import PdfReader
import pypdfium2 as pdfium
R=Path(__file__).resolve().parent;D=R/'data/raw/buildings'
locations={
 'aeo8.pdf':{68:['54.8%','2023'],70:['2023']},
 'heesi2019.pdf':{40:['7,447','103,016'],93:['excluding consumption by private cars']},
 'cambodia-energy-statistics.pdf':{0:['2000–2019'],1:['September 2022'],15:['estimated'],78:['Table 2019']},
 'aeo8-corrigendum.pdf':{0:['November 2024']},
}
records=[]
for name,checks in locations.items():
    p=D/name;reader=PdfReader(p);pdf=pdfium.PdfDocument(p)
    rec=dict(filename=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=len(reader.pages),checked_locations=[])
    for page,terms in checks.items():
        text=' '.join(reader.pages[page].extract_text().split())
        for term in terms:assert term in text,(name,page,term)
        rec['checked_locations'].append(dict(pdf_page_one_based=page+1,search_terms=terms))
    page=next(iter(checks));png=D/(name+f'.page{page+1}.png')
    pdf[page].render(scale=1.3).to_pil().save(png)
    rec['rendered_page']=png.name;rec['rendered_sha256']=hashlib.sha256(png.read_bytes()).hexdigest()
    records.append(rec)
(R/'evidence/PDF_LOCATION_CHECKS.json').write_text(json.dumps(records,indent=2,ensure_ascii=False))
print(json.dumps({'PDFs':len(records),'verified_locations':sum(len(r['checked_locations']) for r in records)}))
