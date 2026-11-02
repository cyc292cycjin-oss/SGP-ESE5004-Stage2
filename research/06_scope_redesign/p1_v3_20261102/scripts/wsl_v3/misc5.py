"""V3 phase 2 inputs: DOSE vs GADM names, MY / others GIS petrochem + aluminium rows, shares of the assembly allocation. Read only."""
import warnings, json
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
warnings.filterwarnings("ignore")
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 44)
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); OUT = MAIN / "results_project/v3/phase1"; SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102")
d = pd.read_csv(SRC / "03_subnational/DOSE_V2.11.csv", low_memory=False)
root = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/gadm")
for iso, yr in (("IDN", 2019), ("MYS", 2019), ("PHL", 2019)):
    g = gpd.read_file(root / f"gadm41_{iso}/gadm41_{iso}.gpkg", layer="ADM_ADM_1", engine="pyogrio", columns=["GID_1", "NAME_1"], read_geometry=False)
    x = d[(d.GID_0 == iso) & (d.year == yr)][["GID_1", "region", "man_grp_pc_usd", "pop"]]
    m = x.merge(g, on="GID_1", how="outer")
    if iso == "PHL":
        print(iso, sorted(x.region.tolist())); print(sorted(g.NAME_1.tolist()))
    else:
        print(iso, m[(m.region.isna()) | (m.NAME_1.isna()) | (m.region.astype(str).str[:5] != m.NAME_1.astype(str).str[:5])].to_string())
f = pd.read_csv(OUT / "USGS_INDOPAC_FACILITIES_ALL.csv", low_memory=False)
A = f[f.Country.isin(["Malaysia", "Vietnam", "Philippines", "Burma", "Brunei", "Singapore"])]
c = ["Country", "FeatureNam", "DsgAttr01", "DsgAttr02", "DsgAttr06", "DsgAttr07", "ADM1", "Latitude", "Longitude", "LocOpStat", "DsgAttr9"]
r = A[A.FeatureTyp.str.contains("Refiner") | A.DsgAttr01.isin(["Aluminum", "Alumina"]) | (A.DsgAttr01 == "Nitrogen")]
print(r[c].sort_values(["Country", "DsgAttr01"]).to_string())
