import sys,re
sys.path.insert(0,'/home/jin/v3/pylib')
import pypdf
from pathlib import Path
R=Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
p=R/"intake/lit/IRENA_Global_Trade_Hydrogen_2022.pdf"
r=pypdf.PdfReader(str(p)); out=[]
for i,pg in enumerate(r.pages,1):
    out.append(f"\n=====PAGE {i}=====\n"+(pg.extract_text() or ""))
t="".join(out); (R/"phase1/IRENA2022.txt").write_text(t); print(len(r.pages),len(t))
for kw in (r"USD/t\b|USD/tonne|per tonne[- ]km|USD/kg",r"knots|km/h|speed",r"boil.?off",r"charter|time.?charter",r"methanol.{0,60}(ship|tanker|vessel)|(ship|tanker|vessel).{0,60}methanol",r"ammonia.{0,60}(ship|tanker|vessel|carrier)"):
    k=0
    for m in re.finditer(kw,t,flags=re.I):
        s=t[max(0,m.start()-110):m.end()+130].replace("\n"," ")
        pg=t.count("=====PAGE",0,m.start())
        print(f"[{kw[:14]} p{pg}]",s[:260]); k+=1
        if k>=7: break
