"""M08b probe: structure of the three R1 download files (read-only)."""
import pandas as pd

R1 = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/R1_demand/"
x = pd.ExcelFile(R1 + "myb1-2023-cemen-ERT.xlsx")
print("cement sheets:", x.sheet_names)
t = pd.read_excel(x, "T22", header=None)
print(t.shape)
for i in range(min(8, len(t))):
    print(i, list(t.iloc[i, :8]))
asean = ["Brunei", "Burma", "Cambodia", "Indonesia", "Laos", "Malaysia", "Philippines", "Singapore", "Thailand", "Timor", "Vietnam", "Myanmar"]
for i in range(len(t)):
    v = str(t.iat[i, 0])
    if any(a in v for a in asean):
        print(i, list(t.iloc[i, :12]))
s = pd.ExcelFile(R1 + "exp-2026-10-20_15_02_22.xlsx")
print("steel sheets:", s.sheet_names)
for sh in s.sheet_names:
    d = pd.read_excel(s, sh, header=None)
    print(sh, d.shape)
    print(d.head(6).to_string())
    for i in range(len(d)):
        v = " ".join(str(z) for z in d.iloc[i, :3])
        if any(a in v for a in asean + ["Viet"]):
            print(i, list(d.iloc[i, :9]))
u = pd.read_csv(R1 + "unpopulation_dataportal_20261020224306.csv")
print(u.columns.tolist())
print(u[u.columns[:12]].tail(4).to_string())
