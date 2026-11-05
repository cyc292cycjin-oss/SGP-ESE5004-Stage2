"""G2-6: spatial allocation of the Viet Nam sub-sectors (template step 8) against the v3 node shares.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_nodes.py

Points -> v3 onshore regions (point in polygon; outside: nearest node), VN nodes 'VN2 0' ... 'VN2 7'.
  steel: GEM GIST 2026-09 operating capacity lines in 2024; GEM plant production 2024 where reported, otherwise capacity x u (u calibrated to
         worldsteel 2024 21,974 kt, capped at 1) -> compared with v3 (GEM capacity);
  pulp and paper: SFI 2025-07 mills (pulp capacity x u; paper capacity, mills without a value share the rest), as S2;
  glass, alumina, textiles, food: Climate TRACE V5.12.0 asset locations, capacity weights (location only: activity is modelled, S0 4.5);
  cement and other: v3 unchanged (GEM capacity / DOSE 2018).
Also locates the 2019 GIPT captive coal units. Writes VN_NODE_SHARES.csv, tables/VN_STEEL_PLANTS_2024.csv, tables/VN_CAPTIVE_UNIT_NODES.csv,
evidence/_nodes_evidence.json. Memory: Climate TRACE parquet is read with a country filter (the full files exceed the WSL memory budget).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

CT = cm.S2W / "extracted/06_climate_trace"
GEM_STEEL = cm.S2W / "extracted/01_gem_steel/gem-download (2)/Plant-level data - Global Iron and Steel Tracker - September 2026 (V1).xlsx"
SFI = cm.S2W / "downloads/04_sfi_pulp_paper/SFI_ALD_Pulp_Paper_Database_July_2025.xlsx"
OP = ("operating", "operating pre-retirement")


def year_of(x):
    m = re.match(r"^(\d{4})", str(x))
    return int(m.group(1)) if m else np.nan


def coords(s):
    try:
        a, b = [float(x) for x in str(s).split(",")]
        return a, b
    except Exception:   # noqa: BLE001
        return np.nan, np.nan


def node_of(df, regions):
    import geopandas as gpd
    g = gpd.GeoDataFrame(df[["lat", "lon"]].copy(), geometry=gpd.points_from_xy(df.lon, df.lat), crs=4326)
    r = regions[regions.country == cm.CC]
    j = gpd.sjoin(g, r[["node", "geometry"]], how="left", predicate="within"); j = j[~j.index.duplicated()]
    out = j.node.copy(); how = pd.Series("point in region", index=j.index)
    for i in j[j.node.isna()].index:
        out.at[i] = r.node.iloc[int(np.argmin(r.geometry.distance(g.geometry.at[i]).values))]; how.at[i] = "nearest node"
    return out, how


def ct_assets(folder: str) -> pd.DataFrame:
    import pyarrow.parquet as pq
    f = next((CT / folder / "DATA").glob("*emissions_sources_v5_12_0.parquet"))
    t = pq.read_table(f, columns=["source_id", "source_name", "iso3_country", "start_time", "capacity", "lat", "lon"], filters=[("iso3_country", "=", "VNM")]).to_pandas()
    t = t[t.start_time.astype(str).str.startswith("2025")]
    return t.groupby("source_id").agg(name=("source_name", "first"), cap=("capacity", "max"), lat=("lat", "first"), lon=("lon", "first")).reset_index()


def shares(df, w, regions):
    df = df.copy(); df["node"], df["node_method"] = node_of(df, regions)
    s = df.groupby("node")[w].sum(); return (s / s.sum()), df


def main():
    import geopandas as gpd
    ev = cm.Ev("nodes")
    regions = gpd.read_file(cm.MAIN / "research_inputs/renewable_v5/regions_onshore.geojson")
    v3 = pd.read_csv(cm.REPO / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv"); v3 = v3[v3.country == cm.CC]
    v3s = {k: g.set_index("node").share for k, g in v3.groupby("subsector")}
    rows = []

    def add(sub, s_new, v3_key, note):
        ref = v3s.get(v3_key, pd.Series(dtype=float))
        for n in sorted(set(s_new.index) | set(ref.index)):
            a, b = float(s_new.get(n, 0.0)), float(ref.get(n, 0.0))
            rows.append(dict(subsector=sub, node=n, share_v4=a, share_v3=b, diff_pp=(a - b) * 100, note=note + (" | single node difference > 5 pp" if abs(a - b) > 0.05 else "")))

    # ---------------- steel (GEM) ----------------
    xl = pd.read_excel(GEM_STEEL, sheet_name=["Plant data", "Plant capacities and status", "Plant production"])
    pdata, cap, prod = xl["Plant data"], xl["Plant capacities and status"], xl["Plant production"]
    pdi = pdata[pdata["Country/area"].eq("Vietnam")].set_index("GEM plant ID")
    c = cap[cap["Country/area"].eq("Vietnam")].copy()
    c["crude"] = pd.to_numeric(c["Nominal crude steel capacity (ttpa)"], errors="coerce").fillna(0.0)
    c["start_y"] = c["Start date"].map(year_of)
    c = c[c.Status.isin(OP) & (c.crude > 0) & ~(c.start_y > 2024)].copy()
    pr = prod[prod["GEM plant ID"].isin(c["GEM plant ID"]) & prod["Type of production"].eq("Crude steel production (ttpa)")].set_index("GEM plant ID")
    known = {}
    if 2024 in pr.columns:
        for i, v in pd.to_numeric(pr[2024], errors="coerce").dropna().items():
            known[i] = float(v)
    plant = c.groupby("GEM plant ID").crude.sum().rename("crude_cap_kt").to_frame()
    plant["name"] = plant.index.map(lambda i: pdi.at[i, "Plant name (English)"] if i in pdi.index else "")
    plant["lat"], plant["lon"] = zip(*plant.index.map(lambda i: coords(pdi.at[i, "Coordinates"]) if i in pdi.index else (np.nan, np.nan)))
    plant["prod_2024_kt"] = plant.index.map(lambda i: known.get(i, np.nan))
    nat24 = float(pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_OUTPUT_BASE_M08B.csv").set_index("country").at[cm.CC, "steel_base_kt"])
    kn = plant.prod_2024_kt.notna()
    u = (nat24 - plant.loc[kn, "prod_2024_kt"].sum()) / plant.loc[~kn, "crude_cap_kt"].sum()
    plant["activity_2024_kt"] = np.where(kn, plant.prod_2024_kt, plant.crude_cap_kt * min(u, 1.0))
    s_steel, P = shares(plant.reset_index(), "activity_2024_kt", regions)
    P.to_csv(cm.WORK / "tables/VN_STEEL_PLANTS_2024.csv", index=False, float_format="%.4f")
    ev.put("steel.plants_operating_2024", int(len(plant)), "plants", "GEM GIST 2026-09 VN operating crude-steel lines (start <= 2024)", "VERIFIED", "B")
    ev.put("steel.capacity_2024_kt", float(plant.crude_cap_kt.sum()), "kt", "GEM GIST 2026-09", "VERIFIED", "B")
    ev.put("steel.plants_with_production_2024", int(kn.sum()), "plants", "GEM plant production 2024", "VERIFIED", "B")
    ev.put("steel.u_2024", float(u), "-", "worldsteel 2024 (v3 base) minus known production / remaining capacity", "INFERENCE", "C")
    ev.put("steel.facility_total_capped_kt", float(plant.activity_2024_kt.sum()), "kt", "u capped at 1", "EXACT", "C")
    add("steel", s_steel, "steel", "GEM 2024 production or capacity x u (u <= 1)")
    # ---------------- pulp and paper (SFI) ----------------
    S = pd.read_excel(SFI, sheet_name="SFI_Pulp_Paper_Database"); S = S[S.country.eq("Vietnam")].copy()
    S["cap_pulp"] = pd.to_numeric(S["capacity_pulp (tonnes per year) "], errors="coerce"); S["cap_paper"] = pd.to_numeric(S["capacity_paper (tonnes per year)"], errors="coerce")
    S["lat"], S["lon"] = S.latitude.astype(float), S.longitude.astype(float)
    fao = pd.read_csv(cm.WORK / "tables/VN_PULP_PAPER_FAOSTAT.csv").groupby("group").q_2019_t.sum()
    kp, kq = float(S.cap_pulp.sum()), float(S.cap_paper.sum())
    paper_types = ~S.plant_type.astype(str).str.fullmatch("Pulp")
    n_unknown = int((S.cap_paper.isna() & paper_types).sum()); resid = max(0.0, float(fao["paper"]) - kq)
    S["w"] = S.cap_pulp.fillna(0.0) * (float(fao["pulp"]) / kp if kp else 0.0) + np.where(S.cap_paper.notna(), S.cap_paper.fillna(0.0) * min(1.0, float(fao["paper"]) / kq if kq else 0.0),
                                                                                         np.where(paper_types, resid / max(1, n_unknown), 0.0))
    s_pp, S2 = shares(S, "w", regions)
    S2[["uid", "plant_name", "state", "lat", "lon", "plant_type", "cap_pulp", "cap_paper", "w", "node", "node_method"]].to_csv(cm.WORK / "tables/VN_PULP_PAPER_MILLS_SFI.csv", index=False)
    ev.put("pp.sfi_mills", int(len(S)), "mills", "SFI 2025-07 VN", "VERIFIED", "B")
    ev.put("pp.sfi_pulp_capacity_t", kp, "t", "SFI 2025-07 VN", "VERIFIED", "B"); ev.put("pp.sfi_paper_capacity_t", kq, "t", "SFI 2025-07 VN", "VERIFIED", "B")
    add("pulp_paper", s_pp, "dispersed", "SFI mills (S2 weights); v3 = dispersed shares (DOSE 2018)")
    # ---------------- Climate TRACE locations ----------------
    for sub, folder, v3k in (("glass", "manufacturing_glass", "dispersed"), ("alumina", "manufacturing_aluminum", "other"),
                             ("dispersed: textile and leather", "manufacturing_textiles-leather-apparel", "dispersed"), ("dispersed: food and tobacco", "manufacturing_food-beverage-tobacco", "dispersed")):
        a = ct_assets(folder)
        s_, A = shares(a, "cap", regions)
        A.to_csv(cm.WORK / f"tables/VN_CT_{folder.split('_', 1)[1].upper()}.csv", index=False)
        ev.put(f"ct.{folder}.assets", int(len(a)), "assets", f"Climate TRACE V5.12.0 {folder}, VN, 2025", "VERIFIED", "D")
        add(sub, s_, v3k, f"Climate TRACE asset locations, capacity weights ({len(a)} assets; modelled activity, location only); v3 = {v3k} shares")
    for sub, k in (("cement", "cement"), ("other", "other"), ("ammonia (petrochem key in v3)", "petrochem")):
        add(sub, v3s.get(k, pd.Series(dtype=float)), k, "unchanged from v3")
    NS = pd.DataFrame(rows); NS.to_csv(cm.WORK / "VN_NODE_SHARES.csv", index=False, float_format="%.6f")
    # captive units
    cu = pd.read_csv(cm.WORK / "tables/VN_CAPTIVE_UNITS_GIPT.csv")
    cu = cu[cu.op_2019_yearend].rename(columns={"Latitude": "lat", "Longitude": "lon"})
    cu["node"], cu["node_method"] = node_of(cu, regions)
    cu[["Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Captive Industry Type", "lat", "lon", "node", "node_method"]].to_csv(cm.WORK / "tables/VN_CAPTIVE_UNIT_NODES.csv", index=False)
    for r in NS[NS.diff_pp.abs() > 5].itertuples():
        ev.put(f"diff.{r.subsector}.{r.node}", float(r.diff_pp), "pp", "VN_NODE_SHARES.csv", "EXACT", "C")
    ev.write(cm.WORK / "evidence/_nodes_evidence.json")
    pd.set_option("display.width", 220)
    print(NS[NS.subsector.isin(["steel", "pulp_paper", "glass", "alumina", "dispersed: textile and leather"])].round(3).to_string())
    print(P[["name", "crude_cap_kt", "prod_2024_kt", "activity_2024_kt", "node"]].to_string())
    print(cu[["Plant / Project name", "Capacity (MW)", "node"]].to_string())


if __name__ == "__main__":
    main()
