"""Bounded local source excerpts and review images; no model execution."""
from pathlib import Path
import json,hashlib
from pypdf import PdfReader
import pypdfium2 as pdfium
R=Path(__file__).resolve().parent;P=R.parent/'phase3a5'
E=R/'evidence';E.mkdir(exist_ok=True);(E/'previews').mkdir(exist_ok=True)
specs=[(P/'data/raw/buildings/aeo8.pdf',[48,49,53,56,65,68,69,70,71,183,186],[183,186]),
 (P/'data/raw/buildings/aeo8-corrigendum.pdf',list(range(1,12)),[]),
 (P/'data/raw/buildings/malaysia-neb2016.pdf',[59,74,75,91,92,95,97,98,103,104,105,106,108],[95,103,105]),
 (R/'data/raw/malaysia-neb2019.pdf',[55,57,67,68,72,73,78,79,81],[57,73])]
records=[]
for path,pages,visual in specs:
 d=PdfReader(path);pages=[p for p in pages if p<=len(d.pages)]
 for n in pages:
  out=E/f'{path.stem}_p{n}.txt';out.write_text(d.pages[n-1].extract_text(),encoding='utf8')
 if visual:
  v=pdfium.PdfDocument(path)
  for n in visual:
   png=E/'previews'/f'{path.stem}_p{n}.png'
   if not png.exists():v[n-1].render(scale=1.65).to_pil().save(png)
 records.append(dict(path=path.relative_to(R.parent).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),pdf_pages=pages,rendered_pages=visual))
(E/'SOURCE_EXCERPT_INDEX.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print(json.dumps(records,indent=2))
