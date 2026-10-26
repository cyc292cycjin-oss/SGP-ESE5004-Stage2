"""DFX v3 probe (read-only): JRC-IDEES-2021 Industry EU27 workbook ammonia rows, USGS MYB 2022 nitrogen T12 ASEAN rows, NEU gas 2019 rows.

Run: /home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/probe_sources.py
"""
import hashlib
from pathlib import Path

import pandas as pd

MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
WT = Path("/home/jin/wt_b4p_20261026")
SRC = MAIN / "research_inputs/registry_v5/sources"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


idees = SRC / "jrc_idees_2021/EU27/JRC-IDEES-2021_Industry_EU27.xlsx"
usgs = SRC / "pypsa_eur_data/usgs_myb1-2022-nitro-ert.xlsx"
print("IDEES exists", idees.exists(), sha(idees)[:16] if idees.exists() else "")
print("USGS exists", usgs.exists(), sha(usgs)[:16] if usgs.exists() else "")

if idees.exists():
    x = pd.ExcelFile(idees)
    print("IDEES sheets:", x.sheet_names)
    for sh in x.sheet_names:
        t = pd.read_excel(idees, sh, header=None)
        m = t.astype(str).apply(lambda r: r.str.contains("mmonia|NH3|nitrogen", regex=True).any(), axis=1)
        if m.any():
            print("== sheet", sh, "rows with ammonia/NH3/nitrogen:")
            print(t[m].iloc[:, :4].to_string()[:1500])
    # chemical feedstock rows
    for sh in ("CHI", "CHI_fec", "CHI_ued"):
        if sh in x.sheet_names:
            t = pd.read_excel(idees, sh, header=None)
            m = t.astype(str).apply(lambda r: r.str.contains("eedstock|on-energy", regex=True).any(), axis=1)
            print("== sheet", sh, "feedstock rows:")
            print(t[m].iloc[:, :3].to_string()[:1200])

if usgs.exists():
    x = pd.ExcelFile(usgs)
    print("USGS sheets:", x.sheet_names)
    for sh in x.sheet_names:
        t = pd.read_excel(usgs, sh, header=None)
        print("== sheet", sh, t.shape)
        print(t.head(8).iloc[:, :8].to_string()[:1800])
        m = t.astype(str).apply(lambda r: r.str.contains("Indonesia|Malaysia|Vietnam|Viet Nam|Burma|Myanmar|Brunei|Philippines|Thailand|Singapore|Cambodia|Laos|Timor", regex=True).any(), axis=1)
        print(t[m].iloc[:, :8].to_string()[:2500])
        # footnote / unit lines
        u = t.astype(str).apply(lambda r: r.str.contains("Thousand|thousand|contained|nitrogen content|Metric", regex=True).any(), axis=1)
        print("-- unit lines:")
        print(t[u].iloc[:, :3].to_string()[:1200])

dem = pd.read_csv(WT / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", dtype=str, keep_default_na=False)
ne = dem[dem.sector == "NonEnergyUse"].copy()
ne["b"] = pd.to_numeric(ne.base_2019_mwh, errors="coerce").fillna(0.0) / 1e6
ne["v"] = pd.to_numeric(ne.value_2050_mwh, errors="coerce").fillna(0.0) / 1e6
print("== NEU rows (TWh): 2019 base / 2050 value by country x carrier x account")
print(ne.groupby(["country", "carrier", "account"])[["b", "v"]].sum().round(3).to_string())
