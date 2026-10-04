from pathlib import Path
from pypdf import PdfReader
import json
R=Path(__file__).resolve().parent
hits=[]
for name,terms in [('my-energy-mag9-2016.pdf',['338','water heater']),('my-water-guideline2016.pdf',['coefficient','efficiency','performance'])]:
 for i,p in enumerate(PdfReader(R/'data/raw'/name).pages):
  t=p.extract_text()
  if any(x in t.lower() for x in terms):
   hits.append(dict(file=name,pdf_page=i+1,excerpt=t[:120]))
(R/'evidence/DEVICE_SEARCH_INDEX.json').write_text(json.dumps(hits,indent=2),encoding='utf8')
print(json.dumps(hits,indent=2))
