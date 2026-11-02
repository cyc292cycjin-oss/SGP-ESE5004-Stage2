import sys,re
sys.path.insert(0,'/home/jin/v3/pylib')
import pypdf
from pathlib import Path
p=[x for x in Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102/01_industry").glob("2564*")][0]
r=pypdf.PdfReader(str(p)); n=len(r.pages); t=[]
for i in list(range(0,6))+list(range(n//3,n//3+4)):
    t.append(r.pages[i].extract_text() or "")
s=" ".join(t); print(n, len(s)); print(re.sub(r"\s+"," ",s)[:500])
print(sum(1 for c in s if '\u0e00'<=c<='\u0e7f'), len(s))
