"""X1b: the EPPO projects and the two Xekaman plants in GEM GIPT 2026-09 and in the survival records. Read-only."""
import json, re
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 250, "display.max_columns", 60, "display.max_rows", 300, "display.max_colwidth", 46)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); RI = M / "research_inputs"
g = pd.read_csv(RI / "registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False)
print(list(g.columns))
cc = next(c for c in g.columns if c.lower() in ("country/area", "country", "country_iso2", "iso2"))
print(cc, g[cc].value_counts().head(12).to_dict())
la = g[g[cc].astype(str).str.contains("Laos|LA$|Lao", regex=True)].copy()
print("LA rows", len(la))
nm = next(c for c in g.columns if "plant" in c.lower() and "name" in c.lower() or c.lower() in ("plant / project name", "name"))
pat = "Theun|Hinboun|Houay ?ho|Ngum 2|Ngum2|Hongsa|Xayaburi|Xayabouri|Sayaburi|Xe ?Pian|Xepian|Namnoy|Ngiep|Xekaman|Xe ?Kaman|Sekaman"
x = la[la[nm].astype(str).str.contains(pat, case=False, regex=True)]
cols = [c for c in g.columns if any(k in c.lower() for k in ("name", "status", "capacity", "start", "retired", "type", "lat", "lon", "id", "owner", "unit"))]
print(x[cols].sort_values(nm).to_string()[:9000])
print(json.dumps(json.loads((RI / "asset_survival/integration_contract.json").read_text()), default=str)[:800])
f = json.loads((RI / "asset_survival/GEM_FROZEN_IDENTITY_FIELDS.json").read_text()); print(type(f), list(f)[:10] if isinstance(f, dict) else f[:2])
for p in sorted((RI / "asset_survival").iterdir()):
    print(p.name, p.stat().st_size)
print("=====compact")
print([c for c in g.columns if "lat" in c.lower() or "lon" in c.lower() or "id" in c.lower()])
idc = [c for c in g.columns if c.lower().endswith("id")]
la2 = la[["Type", nm, "Unit / Phase name", "Plant / Project name (other)", "Capacity (MW)", "Status", "Start year", "Latitude", "Longitude"] + idc].copy()
la2[nm] = la2[nm].str.replace(" hydroelectric plant", "", regex=False).str.replace(" power station", "", regex=False)
la2 = la2.rename(columns={nm: "plant", "Unit / Phase name": "unit", "Plant / Project name (other)": "other", "Capacity (MW)": "mw", "Start year": "start", "Latitude": "lat", "Longitude": "lon"})
la2["other"] = la2.other.astype(str).str[:30]
print(la2[la2.Status.astype(str).isin(["operating", "construction", "mothballed"])].sort_values("mw", ascending=False).head(70).to_string(index=False))
