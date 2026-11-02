import json
from pathlib import Path
import netCDF4 as nc
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds_x1b")
with nc.Dataset(M / "integrated/integrated_365_24h_unsolved.nc") as d:
    m = json.loads(d.getncattr("meta"))
l = m["research_dedicated_lines"]; print({k: v for k, v in l.items() if k != "lines"})
for r in l["lines"]:
    print(r["link"], r["projects"], r["contract_mw"], round(r["length_km"], 1), round(r["efficiency"], 4), round(r["annual_fom_eur"] / 1e6, 3))
print("existing fom", m["existing_cross_border_fom_eur"] / 1e6, len(m["existing_cross_border_fom_ledger"]))
