import re
from pathlib import Path
t=Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1/IRENA2022.txt").read_text()
pg=t.split("=====PAGE ")
def P(i,a=0,b=2600): 
    s=pg[i]; print(f"--- p{i}"); print(re.sub(r"\s+"," ",s)[a:b])
P(40,300,1500); P(42,0,1900)
for i in (43,44,45):
    s=re.sub(r"\s+"," ",pg[i])
    for m in re.finditer(r"(USD|%|days?|km|MJ|GJ|kWh|knots|t/day)[^.]{0,120}(ship|vessel|fuel|port|harbour|terminal)",s):
        print(f"p{i}:",s[max(0,m.start()-90):m.end()+60][:240])
        break
print("--- tables")
for i in range(36,50):
    s=pg[i]
    if re.search(r"TABLE|Table",s):
        for m in re.finditer(r"TABLE [0-9.]+[^\n]{0,110}",s): print(i,m.group(0))
