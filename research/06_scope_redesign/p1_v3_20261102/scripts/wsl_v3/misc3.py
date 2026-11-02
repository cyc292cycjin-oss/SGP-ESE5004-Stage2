"""V3 phase 1: GEM pipelines (ASEAN cross-border), stock table, Assembly bunker weights, ship unit-cost candidates, node time zones. Read only."""
import io, json, re, zipfile, warnings
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
warnings.filterwarnings("ignore")
pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 150); pd.set_option("display.max_colwidth", 56)
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); OUT = MAIN / "results_project/v3/phase1"
W = Path("/home/jin/wt_v3_20261102")
z = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/F2_lng/gem-download (1).zip"
with zipfile.ZipFile(z) as x:
    xl = pd.ExcelFile(io.BytesIO(x.read("GEM-GGIT-Gas-Pipelines-2025-11.xlsx")))
print(xl.sheet_names)
g = xl.parse([s for s in xl.sheet_names if "ipeline" in s][0])
print(list(g.columns)[:44])
A = ["Brunei", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar", "Philippines", "Singapore", "Thailand", "Timor-Leste", "Vietnam"]
cc = [c for c in g.columns if "ountr" in c and "End" not in c and "Start" not in c][:2]; print(cc)
col = cc[0]
def cnt(s): return sum(1 for a in A if a in str(s))
x = g[g[col].map(cnt) >= 2]
keep = [c for c in ["ProjectID", "PipelineName", "Status", col, "StartCountry", "EndCountry", "StartYear1", "CapacityBcm/y", "Capacity", "CapacityUnits", "Diameter", "DiameterUnits", "LengthKnownKm", "LengthMergedKm", "LengthEstimateKm"] if c in x.columns]
print(x[keep].to_string()[:4200])
st = pd.read_csv(OUT / "V2_CROSS_BORDER_STOCK.csv"); print(st[["type", "name", "carrier", "c0", "c1", "nom", "ext", "length", "kind"]].to_string()[:2600])
print(st.groupby(["carrier"]).nom.agg(["size", "sum"]))
# ship unit costs (EUR2020/MWh per 1000 km) - candidates only
def ann(r, n): return r / (1 - (1 + r) ** -n)
rows = []
for name, inv, cap_t, life, fom, mwh_t in [("MeOH", 35e6, 75e3, 15, .05, 5.528), ("FT/oil products", 35e6, 75e3, 15, .05, 11.9), ("NH3", 81.1642e6, 53e3, 20, .04, 5.166)]:
    a = (ann(.07, life) + fom) * inv; cap = cap_t * mwh_t
    for v, h in [(27.8, 8000.)]:
        ckm = a / (cap * v * h / 2)
        rows.append(dict(cargo=name, annual_eur=a, cap_mwh=cap, capital_eur_per_mwh_1000km=ckm * 1000, ieaghg_per_t_km_as_eur_per_mwh_1000km=0.00295150322083 / mwh_t * 1000, fixed_ports_ieaghg_eur_per_mwh=(13.0 + 11.4 + 2.9) / 6.205 * 1.16898366927 / mwh_t))
print(pd.DataFrame(rows).round(4).to_string())
# node time zone by province (GADM ADM1 point in polygon) for ID
n = pd.read_csv(OUT / "V2_NODES.csv", index_col=0); idn = n[(n.country == "ID") & (n.carrier == "AC")]
adm = gpd.read_file("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/gadm/gadm41_IDN/gadm41_IDN.gpkg", layer="ADM_ADM_1", engine="pyogrio")[["NAME_1", "geometry"]]
p = gpd.GeoDataFrame(idn, geometry=gpd.points_from_xy(idn.x, idn.y), crs=4326)
j = gpd.sjoin_nearest(p, adm.to_crs(4326), how="left")
wib = {"Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Kepulauan Riau", "Jambi", "Sumatera Selatan", "Bangka Belitung", "Bengkulu", "Lampung", "Jakarta Raya", "Banten", "Jawa Barat", "Jawa Tengah", "Yogyakarta", "Jawa Timur", "Kalimantan Barat", "Kalimantan Tengah"}
wit = {"Maluku", "Maluku Utara", "Irian Jaya Barat", "Papua"}
j["tz"] = j.NAME_1.map(lambda s: 7.0 if s in wib else (9.0 if s in wit else 8.0))
print(j.groupby("tz").size().to_dict(), j[["NAME_1", "tz"]].drop_duplicates().sort_values("tz").to_string()[:1400])
j[["NAME_1", "tz", "x", "y"]].to_csv(OUT / "ID_NODE_TIMEZONE_PROPOSAL.csv")
