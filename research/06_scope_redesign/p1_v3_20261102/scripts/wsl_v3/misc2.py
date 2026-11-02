"""V3 phase 1: technology-data ship rows, facility -> region matching, DOSE TH years, GIS ASEAN subset, gas stock, LP dims. Read only."""
import json, re, warnings
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
warnings.filterwarnings("ignore")
pd.set_option("display.width", 230); pd.set_option("display.max_columns", 30); pd.set_option("display.max_rows", 150); pd.set_option("display.max_colwidth", 70)
W = Path("/home/jin/wt_v3_20261102"); MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); OUT = MAIN / "results_project/v3/phase1"; SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102")
td = pd.read_csv(W / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv")
x = td[td.technology.str.contains("ship|tanker|Ship", regex=True)]
print(x[["technology", "parameter", "value", "unit", "source"]].to_string()[:3800])
print(sorted(td[td.technology.str.contains("liquid|MeOH|methanol|FT fuel|NH3|ammonia", case=False, regex=True)].technology.unique())[:40])
# regions
r = gpd.read_file(MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
r_m = r.to_crs(3857)
n = pd.read_csv(OUT / "V2_NODES.csv", index_col=0)


def join(df, lat, lon, label, ctry="iso"):
    g = gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df[lon], df[lat]), crs=4326)
    g = g[g[lat].notna()]
    j = gpd.sjoin(g, r[["node", "country", "geometry"]].rename(columns={"country": "region_country"}), how="left", predicate="within")
    j = j[~j.index.duplicated()]
    un = j[j.node.isna()]; bad = j[j.node.notna() & (j.region_country != j[ctry])]
    print(label, "points", len(j), "unmatched", len(un), "other-country region", len(bad), un[ctry].value_counts().to_dict(), bad[ctry].value_counts().to_dict())
    return j


c = pd.read_csv(OUT / "GEM_CEMENT_ASEAN_OPERATING.csv"); jc = join(c, "lat", "lon", "GEM cement")
s = pd.read_csv(OUT / "GEM_STEEL_ASEAN_OPERATING.csv").drop_duplicates("GEM plant ID"); js = join(s, "lat", "lon", "GEM steel")
print(s[s.iso == "ID"][["Plant name (English)", "Nominal crude steel capacity (ttpa)", "equip", "Subnational unit"]].to_string()[:1300])
a = pd.read_csv(OUT / "GEM_STEEL_ASEAN_OPERATING.csv")
# cement shares per node for ID vs current v2 shares
cc = jc.groupby(["iso", "node"]).clk.sum().rename("clk").reset_index(); cc["sh"] = cc.clk / cc.groupby("iso").clk.transform("sum")
print(cc[cc.iso == "ID"].sort_values("sh", ascending=False).head(6).round(3).to_string())
# DOSE TH / VN year coverage
d = pd.read_csv(SRC / "03_subnational/DOSE_V2.11.csv", low_memory=False)
for iso in ("THA", "VNM", "IDN", "MYS", "PHL", "LAO"):
    z = d[(d.GID_0 == iso) & d.man_grp_pc_usd.notna()]; t = z.groupby("year").GID_1.nunique(); print(iso, "adm1 by year (last 8)", t.tail(8).to_dict())
    print("   version", z[z.year == z.year.max()].version.value_counts().to_dict(), "pop na", int(z[z.year == z.year.max()]["pop"].isna().sum()))
th = d[(d.GID_0 == "THA") & (d.year == 2015)].assign(m=lambda q: q.man_grp_pc_usd * q["pop"]); print("TH 2015 top", th.sort_values("m", ascending=False).head(6)[["region", "GID_1", "m"]].assign(m=lambda q: (q.m / th.m.sum()).round(3)).to_dict("records"), "tot bn", round(th.m.sum() / 1e9, 1))
import pyogrio
root = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/gadm")
for iso in ("IDN", "MYS", "PHL", "THA", "VNM"):
    p = root / f"gadm41_{iso}" / f"gadm41_{iso}.gpkg"; g = gpd.read_file(p, layer="ADM_ADM_1", engine="pyogrio", columns=["GID_1", "NAME_1"], read_geometry=False)
    dd = set(d[(d.GID_0 == iso)].GID_1.dropna()); gg = set(g.GID_1); print(iso, "dose", len(dd), "gadm", len(gg), "common", len(dd & gg), "dose-only sample", sorted(dd - gg)[:6], "gadm-only sample", sorted(gg - dd)[:4])
# GIS ASEAN subset
f = pd.read_csv(OUT / "USGS_INDOPAC_FACILITIES_ALL.csv", low_memory=False)
A = f[f.Country.isin(["Malaysia", "Vietnam", "Philippines", "Burma", "Timor-Leste", "Brunei", "Singapore"])].copy()
A["cap"] = pd.to_numeric(A.DsgAttr06, errors="coerce").replace(-999.0, np.nan)
def cls(t):
    c1, ty = str(t.DsgAttr01), str(t.FeatureTyp)
    if c1 == "Cement": return "cement"
    if c1 == "Nickel": return "nickel"
    if c1 in ("Nitrogen",): return "nitrogen"
    if "Refiner" in ty: return "refinery_petrochem"
    if c1 in ("Iron and Steel", "Ferroalloys"): return "steel_ferroalloy"
    if c1 in ("Aluminum", "Alumina", "Bauxite"): return "aluminium"
    return None
A["k"] = A.apply(cls, axis=1); B = A[A.k.notna()]
t = B.groupby(["k", "Country"]).agg(n=("cap", "size"), cap_ok=("cap", "count"), coord=("Latitude", "count")).reset_index(); print(t.to_string())
print("nickel products", A[A.DsgAttr01 == "Nickel"].groupby(["Country", "DsgAttr02", "FeatureTyp"]).size().to_dict())
print("commodities with N", sorted(set(f.DsgAttr01[f.DsgAttr01.astype(str).str.contains("itrog|mmonia|ertil", regex=True)])))
print("processing plants w/o petroleum", A[A.FeatureTyp.str.contains("Refiner")][["Country", "FeatureNam", "DsgAttr01", "DsgAttr02", "cap", "DsgAttr07"]].head(14).to_string())
g = pd.read_csv(W / "research_inputs/gas_v5/GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv", keep_default_na=False)
print(g[["pipeline", "gem_status", "start_year", "capacity_bcm_per_year", "capacity_mw_ncv", "length_km", "from_node", "to_node", "direction", "status"]].to_string())
for fn in ("ammonia_plants.csv", "industrial_database.csv"):
    p = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources") / fn
    t = pd.read_csv(p); print(fn, t.shape, t.columns.tolist()[:14]); cc2 = [x for x in t.columns if "ountry" in x]; print(t[cc2[0]].astype(str).value_counts().head(8).to_dict() if cc2 else "")
