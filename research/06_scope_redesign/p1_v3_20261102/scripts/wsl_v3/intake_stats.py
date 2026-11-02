"""V3 1.2 items 3-5, 8: detailed counts. Read only."""
import json, re, sys, zipfile, warnings
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd
warnings.filterwarnings("ignore")
SRC = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/v3_20261102")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
V3 = MAIN / "results_project/v3"; OUT = V3 / "phase1"; INT = V3 / "intake"
ISO = {"Brunei": "BN", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Lao PDR": "LA", "Malaysia": "MY", "Myanmar": "MM", "Burma": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "East Timor": "TL", "Vietnam": "VN", "Viet Nam": "VN"}
ISO3 = {"BRN": "BN", "KHM": "KH", "IDN": "ID", "LAO": "LA", "MYS": "MY", "MMR": "MM", "PHL": "PH", "SGP": "SG", "THA": "TH", "TLS": "TL", "VNM": "VN"}
pd.set_option("display.width", 240); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
what = sys.argv[1:] or ["gem", "gis", "dose", "gas", "gadm"]
G = INT / "gem"


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", "").str.replace(">", "").str.strip(), errors="coerce")


def coord(s):
    m = s.astype(str).str.extract(r"(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)")
    return pd.to_numeric(m[0], errors="coerce"), pd.to_numeric(m[1], errors="coerce")


if "gem" in what:
    f = [x for x in G.glob("Plant-level data - Global Cement*.xlsx")][0]
    c = pd.read_excel(f, sheet_name="Final data"); c["iso"] = c["Country/area"].map(ISO); c = c[c.iso.notna()].copy()
    c["lat"], c["lon"] = coord(c["Coordinates"]); c["cap"] = num(c["Cement capacity (million metric tonnes per annum)"]); c["clk"] = num(c["Clinker capacity (million metric tonnes per annum)"])
    print("CEMENT status", c["Operating status"].value_counts().to_dict())
    op = c[c["Operating status"].astype(str).str.lower().str.startswith("operating")]
    t = op.groupby("iso").agg(plants=("cap", "size"), cap_mt=("cap", "sum"), cap_known=("cap", "count"), clk_mt=("clk", "sum"), coord_ok=("lat", "count"))
    print(t); print("coord acc", op["Coordinate accuracy"].value_counts().to_dict(), "plant type", op["Plant type"].value_counts().to_dict())
    op.drop(columns=[x for x in op if "Owner" in x or "Parent" in x or "other language" in x]).to_csv(OUT / "GEM_CEMENT_ASEAN_OPERATING.csv", index=False)
    t.to_csv(OUT / "GEM_CEMENT_ASEAN_SUMMARY.csv")
    f = [x for x in G.glob("Plant-level data - Global Iron*.xlsx")][0]
    pl = pd.read_excel(f, sheet_name="Plant data"); ca = pd.read_excel(f, sheet_name="Plant capacities and status"); pr = pd.read_excel(f, sheet_name="Plant production")
    pl["iso"] = pl["Country/area"].map(ISO); pl = pl[pl.iso.notna()].copy(); pl["lat"], pl["lon"] = coord(pl["Coordinates"])
    ca["iso"] = ca["Country/area"].map(ISO); ca = ca[ca.iso.notna()].copy()
    print("STEEL status", ca["Status"].value_counts().to_dict())
    for k in ["Nominal crude steel capacity (ttpa)", "Nominal BOF steel capacity (ttpa)", "Nominal EAF steel capacity (ttpa)", "Nominal IF steel capacity (ttpa)", "Other/unspecified steel capacity (ttpa)", "Nominal iron capacity (ttpa)", "Nominal BF capacity (ttpa)", "Nominal DRI capacity (ttpa)", "Other/unspecified iron capacity (ttpa)"]:
        ca[k] = num(ca[k])
    oc = ca[ca["Status"].astype(str).str.lower().str.startswith("operating")]
    m = oc.merge(pl[["GEM plant ID", "lat", "lon", "Coordinate accuracy", "Subnational unit", "Ferronickel capacity (ttpa)", "Main production equipment"]].rename(columns={"Main production equipment": "equip"}), on="GEM plant ID", how="left")
    m["fe_ni"] = num(m["Ferronickel capacity (ttpa)"])
    pid = m.drop_duplicates("GEM plant ID")
    t = m.groupby("iso").agg(rows=("lat", "size"), crude_ttpa=("Nominal crude steel capacity (ttpa)", "sum"), bof=("Nominal BOF steel capacity (ttpa)", "sum"), eaf=("Nominal EAF steel capacity (ttpa)", "sum"), ind=("Nominal IF steel capacity (ttpa)", "sum"),
                              iron=("Nominal iron capacity (ttpa)", "sum"), bf=("Nominal BF capacity (ttpa)", "sum"), dri=("Nominal DRI capacity (ttpa)", "sum"))
    t["plants"] = pid.groupby("iso").size(); t["coord_ok"] = pid.groupby("iso").lat.count(); t["fe_ni_ttpa"] = pid.groupby("iso").fe_ni.sum()
    print(t); print("coord acc", pid["Coordinate accuracy"].value_counts().to_dict())
    print("ferronickel rows all", pl["Ferronickel capacity (ttpa)"].notna().sum(), pl[num(pl["Ferronickel capacity (ttpa)"]) > 0][["Plant name (English)", "iso", "Ferronickel capacity (ttpa)", "Subnational unit"]].to_string()[:1500])
    prd = pr[pr["GEM plant ID"].isin(pl["GEM plant ID"])]; print("production rows", prd.shape, prd["Type of production"].value_counts().to_dict()); print(prd[[2019, 2023, 2024]].notna().sum().to_dict())
    m.to_csv(OUT / "GEM_STEEL_ASEAN_OPERATING.csv", index=False); t.to_csv(OUT / "GEM_STEEL_ASEAN_SUMMARY.csv")
    u = pd.ExcelFile([x for x in G.glob("Steel unit data*.xlsx")][0])
    for s in ["Electric arc furnaces", "Basic oxygen furnaces", "Induction furnaces"]:
        x = u.parse(s); x["iso"] = x["Country/area"].map(ISO); x = x[x.iso.notna() & x["Unit status"].astype(str).str.lower().str.startswith("operating")]
        print(s, x.groupby("iso").size().to_dict(), "cap kt", round(num(x["Current capacity (ttpa)"]).sum()))
    u = pd.ExcelFile([x for x in G.glob("Iron unit data*.xlsx")][0])
    for s in ["Blast furnaces", "Direct reduced iron furnaces"]:
        x = u.parse(s); x["iso"] = x["Country/area"].map(ISO); x = x[x.iso.notna() & x["Unit status"].astype(str).str.lower().str.startswith("operating")]
        print(s, x.groupby("iso").size().to_dict(), "cap kt", round(num(x["Current capacity (ttpa)"]).sum()))
if "gis" in what:
    gd = INT / "INDOPAC_GIS.gdb"
    with zipfile.ZipFile(SRC / "02_facilities/SI_INDOPAC_GIS_Data-Level_Metadata.zip") as x:
        s = x.read("SI_INDOPAC_GIS_Data-Level_Metadata/INDOPAC_Mineral_Facilities.xml").decode("utf-8", "replace")
    attrs = re.findall(r"<attrlabl[^>]*>(.*?)</attrlabl>.*?<attrdef[^>]*>(.*?)</attrdef>", s, flags=re.S)
    print(len(attrs)); [print("  ", a, "=", re.sub(r"\s+", " ", b)[:150]) for a, b in attrs[:46]]
    f = gpd.read_file(gd, layer="INDOPAC_Mineral_Facilities", engine="pyogrio")
    print(f.Country.value_counts().to_dict())
    print("FeatureTyp", f.FeatureTyp.value_counts().head(25).to_dict())
    for c in ["DsgAttr01", "DsgAttr02", "DsgAttr03", "DsgAttr04", "DsgAttr05", "DsgAttr06", "DsgAttr07", "DsgAttr08", "DsgAttr9", "DsgAttr10", "LocOpStat", "LocConf"]:
        print(c, f[c].notna().sum(), f[c].astype(str).value_counts().head(14).to_dict())
    f.drop(columns="geometry").to_csv(OUT / "USGS_INDOPAC_FACILITIES_ALL.csv", index=False)
if "dose" in what:
    d = pd.read_csv(SRC / "03_subnational/DOSE_V2.11.csv", low_memory=False)
    d["iso"] = d.GID_0.map(ISO3); a = d[d.iso.notna()]
    cols = ["grp_lcu", "pop", "grp_pc_usd", "man_grp_pc_lcu", "man_grp_pc_usd", "man_grp_pc_usd_2015", "ag_grp_pc_usd", "serv_grp_pc_usd"]
    rows = []
    for iso, g in a.groupby("iso"):
        z = g[g.man_grp_pc_usd.notna()]
        rows.append(dict(iso=iso, rows=len(g), adm1=g.GID_1.nunique(), y0=int(g.year.min()), y1=int(g.year.max()), man_rows=len(z), man_y0=int(z.year.min()) if len(z) else None, man_y1=int(z.year.max()) if len(z) else None,
                         adm1_2019=g[g.year == 2019].GID_1.nunique(), man_adm1_2019=z[z.year == 2019].GID_1.nunique(), man_adm1_latest=(z[z.year == z.year.max()].GID_1.nunique() if len(z) else 0)))
    t = pd.DataFrame(rows).set_index("iso"); print(t)
    print(a.version.value_counts().to_dict() if "version" in a else "")
    print(a[a.iso == "LA"][["region", "GID_1", "year", "man_grp_pc_usd", "pop"]].dropna().head(6))
    t.to_csv(OUT / "DOSE_ASEAN_COVERAGE.csv")
    y = a[(a.year == 2019)].assign(man=lambda x: x.man_grp_pc_usd * x["pop"]).groupby("iso").man.sum(); print((y / 1e9).round(1).to_dict())
    for iso in ("ID", "TH", "VN", "PH", "MY"):
        z = a[(a.iso == iso) & a.man_grp_pc_usd.notna()]; yr = 2019 if 2019 in set(z.year) else int(z.year.max())
        z = z[z.year == yr].assign(man=lambda x: x.man_grp_pc_usd * x["pop"]); print(iso, yr, z.sort_values("man", ascending=False).head(5)[["region", "GID_1", "man"]].assign(s=lambda q: (q.man / z.man.sum()).round(3))[["region", "GID_1", "s"]].to_dict("records"))
if "gadm" in what:
    root = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/gadm")
    print(sorted(p.name for p in root.iterdir()))
    import pyogrio
    for k in ISO3:
        p = root / f"gadm41_{k}" / f"gadm41_{k}.gpkg"
        if p.exists():
            ls = pyogrio.list_layers(p); ad1 = [a for a, _ in ls if a.endswith("_1")]
            print(k, p.stat().st_size, [a for a, _ in ls], (pyogrio.read_info(p, layer=ad1[0])["features"] if ad1 else None))
        else:
            print(k, "MISSING")
    r = gpd.read_file(MAIN / "research_inputs/renewable_v5/regions_onshore.geojson"); print(r.groupby("country").size().to_dict())
if "gas" in what:
    t = pd.read_csv(MAIN / "research_inputs/gas_v5/GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv", keep_default_na=False)
    print(t.to_string()[:3500])
    z = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_s4r_downloads_20261020/F2_lng/gem-download (1).zip"
    with zipfile.ZipFile(z) as x:
        print([ (i.filename, i.file_size) for i in x.infolist()])
