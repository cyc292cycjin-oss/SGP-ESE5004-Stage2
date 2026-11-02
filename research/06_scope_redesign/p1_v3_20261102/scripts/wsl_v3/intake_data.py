"""V3 1.2 items 3-7: GEM steel / cement, USGS INDOPAC GIS, DOSE, RAMP EV, OurAirports. Read only on the originals; extraction under results_project/v3/intake/."""
import gzip, json, zipfile, shutil, sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
V3 = MAIN / "results_project/v3"; OUT = V3 / "phase1"; INT = V3 / "intake"; INT.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
A11 = {"Brunei": "BN", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Lao PDR": "LA", "Malaysia": "MY", "Myanmar": "MM", "Burma": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "East Timor": "TL", "Vietnam": "VN", "Viet Nam": "VN"}
what = sys.argv[1:] or ["gem", "gis", "dose", "ramp", "air"]
res = {}
# ---- GEM -----------------------------------------------------------------------------------------------------
if "gem" in what:
    GEMD = INT / "gem"; GEMD.mkdir(exist_ok=True)
    for z, keep in ((SRC / "02_facilities/gem-download.zip", ("Plant-level data - Global Iron", "Steel unit", "Iron unit")), (SRC / "02_facilities/gem-download (1).zip", ("Plant-level data - Global Cement",))):
        with zipfile.ZipFile(z) as x:
            for i in x.infolist():
                if i.filename.startswith(keep) and not (GEMD / i.filename).exists():
                    x.extract(i, GEMD)
    for f in sorted(GEMD.glob("*.xlsx")):
        xl = pd.ExcelFile(f); print("==", f.name, xl.sheet_names)
        for s in xl.sheet_names:
            t = xl.parse(s, nrows=3); print("  ", s, t.shape, list(t.columns)[:50])
# ---- GIS -----------------------------------------------------------------------------------------------------
if "gis" in what:
    gd = INT / "INDOPAC_GIS.gdb"
    if not gd.exists():
        with zipfile.ZipFile(SRC / "02_facilities/INDOPAC_GIS.gdb.zip") as x:
            x.extractall(INT)
    import pyogrio
    layers = pyogrio.list_layers(gd)
    print(layers)
    for name, typ in layers:
        try:
            info = pyogrio.read_info(gd, layer=name); print("--", name, typ, info["features"], list(info["fields"])[:40])
        except Exception as e:
            print("--", name, typ, "ERR", e)
# ---- DOSE ----------------------------------------------------------------------------------------------------
if "dose" in what:
    d = pd.read_csv(SRC / "03_subnational/DOSE_V2.11.csv", low_memory=False)
    print(d.shape, list(d.columns)[:45])
    print(d.head(2).T.head(30))
# ---- RAMP ----------------------------------------------------------------------------------------------------
if "ramp" in what:
    for nm in ("ramp-ev-consumption-profiles", "ramp-ev-plugin-profiles"):
        t = pd.read_csv(SRC / f"04_ev/{nm}.csv.gz")
        print(nm, t.shape, list(t.columns), t.year.min(), t.year.max(), t.country_code.nunique(), sorted(t.country_code.unique()))
        print(t.datetime.iloc[0], t.datetime.iloc[-1]); print(t.groupby("year").size().head(3))
        t["datetime"] = pd.to_datetime(t.datetime, utc=True)
        print(t.groupby("country_code").datetime.diff().value_counts().head(3))
        val = [c for c in t.columns if c not in ("datetime", "year", "country_code")][0]
        y = t[t.year == 2013]; print("rows2013", len(y), "annual sum sample", y.groupby("country_code")[val].sum().head(5).round(1).to_dict())
        p = y.assign(h=y.datetime.dt.hour).groupby(["country_code", "h"])[val].mean().unstack(0)
        print("peak hour utc by country", p.idxmax().to_dict()); print("trough", p.idxmin().to_dict())
        print(p.mean(axis=1).round(4).to_dict())
        p.to_csv(OUT / f"RAMP_{nm}_2013_DIURNAL_UTC.csv")
# ---- airports ------------------------------------------------------------------------------------------------
if "air" in what:
    a = pd.read_csv(SRC / "05_airports/airports.csv", keep_default_na=False, low_memory=False)
    print(a.shape, list(a.columns))
    iso = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
    s = a[a.iso_country.isin(iso) & a.type.isin(["large_airport", "medium_airport"]) & (a.scheduled_service == "yes")].copy()
    print(len(s), s.groupby(["iso_country", "type"]).size().unstack(fill_value=0))
    s["latitude_deg"] = s.latitude_deg.astype(float); s["longitude_deg"] = s.longitude_deg.astype(float)
    r = gpd.read_file(MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    print(r.columns.tolist(), len(r), r.crs)
    g = gpd.GeoDataFrame(s, geometry=gpd.points_from_xy(s.longitude_deg, s.latitude_deg), crs=4326)
    key = "name" if "name" in r.columns else r.columns[0]
    j = gpd.sjoin(g, r[[key, "geometry"]], how="left", predicate="within")
    print("unmatched in regions", int(j[key].isna().sum()), j[j[key].isna()][["iso_country", "name_left" if "name_left" in j else "name", "type"]].head(20).to_string())
    j.drop(columns="geometry").to_csv(OUT / "ASEAN_AIRPORTS_SCHEDULED_V3.csv", index=False)
