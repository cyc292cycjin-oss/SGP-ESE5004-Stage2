"""V3 (decision 164; D164-1 a, D164-2 a, D164-3 a, D164-4 b, D164-5 a): node allocation of the industry demand by facility.

    PYTHONHASHSEED=0 python scripts_project/v3_facility_shares.py --main <main checkout> --dose <DOSE_V2.11.csv> --gadm <pypsa-asean/data/gadm>

Facility sub-sectors: steel, cement (GEM operating plants), non-ferrous (USGS country chapters, province level; GIS for MY), petrochem (USGS GIS with
coordinates; USGS country chapters for ID, TH). Dispersed and other: DOSE manufacturing output by ADM1 (ID, MY, PH 2019; TH, VN 2018), split inside the ADM1
by the node electricity share (D164-4 b). Every other country keeps the v2 rule. Writes research_inputs/industry_v3/*.csv; no build, no solve.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from d1_common import ROOT, sha256

SCRIPT = "scripts_project/v3_facility_shares.py"
V3_DIR = ROOT / "research_inputs/industry_v3"
ISO3 = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MY": "MYS", "MM": "MMR", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}
COUNTRY_NAME = {"Malaysia": "MY", "Vietnam": "VN", "Philippines": "PH", "Burma": "MM", "Brunei": "BN", "Singapore": "SG"}
DOSE_YEAR = {"ID": 2019, "MY": 2019, "PH": 2019, "TH": 2018, "VN": 2018}   # D164-3 a: TH 2019 has 20 ADM1 only, VN ends in 2018
ID_DOSE_TO_GADM = {"IDN.15_1": ["IDN.34_1", "IDN.35_1"]}                 # DOSE Kalimantan Timur = GADM Kalimantan Timur + Kalimantan Utara
ID_DOSE_EXTRA = {"Sulawesi Selatan": ["IDN.25_1"]}                       # GADM Sulawesi Barat has no DOSE row: inside DOSE Sulawesi Selatan
CLINKER_PER_CEMENT = 0.656                                               # technology-data cement finishing clinker-input (registry industry_cement_clinker_ratio)


def norm(d: dict) -> dict:
    d = {k: float(v) for k, v in d.items() if v > 0}; s = sum(d.values())
    return {k: v / s for k, v in d.items()} if s > 0 else {}


def v2_shares(main: Path) -> dict:
    """country -> {node: share}: the v2 IndustryFinalEnergy shares (s2_layers.allocation_node_shares), electricity-based."""
    a = main / "results_project/assembly_v1/final_allocation"; am = json.loads((a / "allocation_manifest.json").read_text())
    z = np.load(a / am["arrays_file"], allow_pickle=False); out = {}
    for ar in am["records"]:
        p = ar["InputID"].split(":")
        if p[3] != "IndustryFinalEnergy":
            continue
        x = np.asarray(z[ar["ArrayKey"]], dtype=float); x = x.reshape(-1, 1) if x.ndim == 1 else x
        if x.sum() > 0:
            out[p[0]] = {n: float(x[:, j].sum() / x.sum()) for j, n in enumerate(ar["Nodes"])}
    return out


def overlap(r: gpd.GeoDataFrame, gadm: Path) -> pd.DataFrame:
    """ADM1 x node: area of the intersection / area of the node region (areas with a cos(latitude) correction, so that no projection database is needed)."""
    rows = []
    for c, iso in ISO3.items():
        g = gpd.read_file(gadm / f"gadm41_{iso}" / f"gadm41_{iso}.gpkg", layer="ADM_ADM_1", engine="pyogrio", columns=["GID_1", "NAME_1"])
        g["geometry"] = g.geometry.simplify(0.01).buffer(0)
        q = r[r.country == c].copy(); q["geometry"] = q.geometry.buffer(0)
        q["area0"] = q.geometry.area * np.cos(np.radians(q.geometry.centroid.y))
        x = gpd.overlay(g, q[["node", "area0", "geometry"]], how="intersection", keep_geom_type=True)
        for _, z in x.iterrows():
            a = z.geometry.area * np.cos(np.radians(z.geometry.centroid.y))
            if a > 0:
                rows.append(dict(country=c, gid=z.GID_1, name=z.NAME_1, node=z.node, frac_of_node=a / z.area0))
        for _, z in g[~g.GID_1.isin(x.GID_1)].iterrows():   # ADM1 outside every node region (small islands): nearest node of the country
            d = q.geometry.distance(z.geometry.centroid); rows.append(dict(country=c, gid=z.GID_1, name=z.NAME_1, node=q.node.iloc[int(np.argmin(d.values))], frac_of_node=0.0))
    return pd.DataFrame(rows)


def adm1_split(ov: pd.DataFrame, e: dict, gid: str) -> dict:
    """D164-4 b: inside an ADM1 by the node electricity share (weight of a node = its share x the part of its region inside the ADM1)."""
    x = ov[ov.gid == gid]
    w = norm({n: e.get(n, 0.0) * f for n, f in zip(x.node, x.frac_of_node)})
    return w or norm({n: max(f, 1e-9) for n, f in zip(x.node, x.frac_of_node)})


def point_shares(df: pd.DataFrame, r: gpd.GeoDataFrame, weight: str, lat="lat", lon="lon") -> tuple[dict, dict]:
    """country -> {node: share} of point facilities: point in the region, else the nearest node of the same country (D164-1 a)."""
    g = gpd.GeoDataFrame(df.copy(), geometry=gpd.points_from_xy(df[lon], df[lat]), crs=4326)
    j = gpd.sjoin(g, r[["node", "country", "geometry"]].rename(columns={"country": "rc"}), how="left", predicate="within"); j = j[~j.index.duplicated()]
    n_out = 0
    for i, z in j[j.node.isna() | (j.rc != j.iso)].iterrows():
        q = r[r.country == z.iso]; j.at[i, "node"] = q.node.iloc[int(np.argmin(q.geometry.distance(z.geometry).values))]; n_out += 1
    out = {c: norm(g2.groupby("node")[weight].sum().to_dict()) for c, g2 in j.groupby("iso")}
    return out, dict(points=int(len(j)), outside_region=n_out)


def gem_inputs(main: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    p1 = main / "results_project/v3/phase1"
    c = pd.read_csv(p1 / "GEM_CEMENT_ASEAN_OPERATING.csv")
    c = c[["GEM plant ID", "Plant name (English)", "iso", "lat", "lon", "cap", "clk", "Plant type", "Coordinate accuracy"]].rename(columns={"GEM plant ID": "gem_id", "Plant name (English)": "plant", "Plant type": "plant_type", "Coordinate accuracy": "accuracy"})
    c["weight"] = c.clk.where(c.clk > 0, c.cap.where(c.plant_type != "grinding", 0.0) * CLINKER_PER_CEMENT).fillna(0.0)
    for iso, g in c.groupby("iso"):
        if g.weight.sum() <= 0:   # grinding-only countries (BN)
            c.loc[g.index, "weight"] = g.cap.fillna(0.0)
    s = pd.read_csv(p1 / "GEM_STEEL_ASEAN_OPERATING.csv")
    w = "Nominal crude steel capacity (ttpa)"
    s = s.groupby(["GEM plant ID", "Plant name (English)", "iso", "lat", "lon", "Coordinate accuracy"], as_index=False)[w].sum().rename(columns={"GEM plant ID": "gem_id", "Plant name (English)": "plant", "Coordinate accuracy": "accuracy", w: "weight"})
    c.to_csv(V3_DIR / "GEM_CEMENT_ASEAN_OPERATING_V3.csv", index=False); s.to_csv(V3_DIR / "GEM_STEEL_ASEAN_OPERATING_V3.csv", index=False)
    return c, s


def gis_inputs(main: Path) -> pd.DataFrame:
    f = pd.read_csv(main / "results_project/v3/phase1/USGS_INDOPAC_FACILITIES_ALL.csv", low_memory=False)
    f["iso"] = f.Country.map(COUNTRY_NAME); f = f[f.iso.notna()]
    f["cap"] = pd.to_numeric(f.DsgAttr06, errors="coerce").replace(-999.0, np.nan)
    act = f.LocOpStat.astype(str).str.strip() == "Assumed Active"
    unit = f.DsgAttr07.map({"MMbbl": 1000.0, "kbbl": 1.0})
    p = f[act & (f.DsgAttr01 == "Petroleum") & (f.DsgAttr02 == "Refined Petroleum Products") & f.cap.notna() & unit.notna()].assign(subsector="petrochem", weight=lambda d: d.cap * unit.reindex(d.index), weight_unit="kbbl_per_a")
    a = f[act & (f.DsgAttr01 == "Aluminum") & (f.DsgAttr02 == "Metal") & f.cap.notna()].assign(subsector="nonferrous_aluminium_primary", weight=lambda d: d.cap, weight_unit="kt")
    x = pd.concat([p, a])[["iso", "subsector", "FeatureNam", "Latitude", "Longitude", "weight", "weight_unit", "ADM1"]].rename(columns={"FeatureNam": "facility", "Latitude": "lat", "Longitude": "lon"})
    x.to_csv(V3_DIR / "USGS_GIS_ASEAN_SELECTED_V3.csv", index=False)
    return x


def dose_adm1(path: Path, gadm_names: pd.DataFrame) -> dict:
    """country -> {GADM GID_1: share of manufacturing output}."""
    d = pd.read_csv(path, low_memory=False); out = {}
    ph = pd.read_csv(V3_DIR / "PH_PROVINCE_REGION_CROSSWALK.csv")
    for c, yr in DOSE_YEAR.items():
        x = d[(d.GID_0 == ISO3[c]) & (d.year == yr) & d.man_grp_pc_usd.notna()].assign(m=lambda q: q.man_grp_pc_usd * q["pop"])
        s = {}
        for _, z in x.iterrows():
            if c == "PH":
                prov = ph[ph.dose_region == z.region].provinces_gadm.iloc[0].split(";")
                g = gadm_names[(gadm_names.country == "PH") & gadm_names.name.isin(prov)].gid.drop_duplicates().tolist()
                if len(g) < len(prov) - 1:
                    raise ValueError(f"PH crosswalk: {z.region} matches {len(g)} of {len(prov)} provinces")
            else:
                g = ID_DOSE_TO_GADM.get(z.GID_1, [z.GID_1]) + (ID_DOSE_EXTRA.get(z.region, []) if c == "ID" else [])
            for k in g:   # a DOSE unit with several GADM units is shared out by the ADM1 split below (equal parts, then node electricity)
                s[k] = s.get(k, 0.0) + float(z.m) / len(g)
        out[c] = norm(s)
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument("--main", type=Path, required=True); p.add_argument("--dose", type=Path, required=True); p.add_argument("--gadm", type=Path, required=True); a = p.parse_args()
    r = gpd.read_file(a.main / "research_inputs/renewable_v5/regions_onshore.geojson")
    v2 = v2_shares(a.main); ledger = {}
    ov = overlap(r, a.gadm); ov.to_csv(V3_DIR / "ADM1_NODE_OVERLAP_V3.csv", index=False)
    cem, stl = gem_inputs(a.main); gis = gis_inputs(a.main); man = pd.read_csv(V3_DIR / "FACILITIES_MANUAL_V3.csv")
    S = {}   # (country, subsector) -> {node: share}
    for key, df in (("cement", cem), ("steel", stl)):
        res, led = point_shares(df, r, "weight"); ledger[key] = led
        for c, v in res.items():
            S[(c, key)] = v
    for key, g in gis.groupby("subsector"):
        res, led = point_shares(g, r, "weight"); ledger["gis_" + key] = led
        for c, v in res.items():
            S[(c, key)] = v
    names = ov[["country", "gid", "name"]].drop_duplicates()
    for (c, key), g in man.groupby(["country", "subsector"]):
        w = {}
        for _, z in g.iterrows():
            gid = names[(names.country == c) & (names.name == z.province_gadm)].gid
            if not len(gid):
                raise ValueError(f"province {z.province_gadm} ({c}) not in GADM")
            for n, s in adm1_split(ov, v2[c], gid.iloc[0]).items():
                w[n] = w.get(n, 0.0) + float(z.weight) * s
        S[(c, key)] = norm(w)
    dose = dose_adm1(a.dose, names); ledger["dose_year"] = DOSE_YEAR
    for c, m in dose.items():
        w = {}
        for gid, s in m.items():
            if gid in set(ov.gid):
                for n, x in adm1_split(ov, v2[c], gid).items():
                    w[n] = w.get(n, 0.0) + s * x
        S[(c, "dispersed")] = norm(w); S[(c, "other")] = S[(c, "dispersed")]
    sub = pd.read_csv(V3_DIR / "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv")
    rows_c, rows_p, rows_s, comp = [], [], [], []
    subs = sorted(set(sub.subsector) | {"petrochem"})
    for (c, s_), v in sorted(S.items()):
        rows_s += [dict(country=c, subsector=s_, node=n, share=x) for n, x in sorted(v.items())]
    for case, t0 in sub.groupby("case"):
        for c, t in t0.groupby("country"):
            base = v2.get(c)
            get = lambda s: S.get((c, s)) or base
            for car, g in t.groupby("carrier"):
                w = {}
                for _, z in g.iterrows():
                    src = base if car == "ammonia" else get(z.subsector)   # ammonia load sits on the national bus: the node key only names the load
                    for n, x in src.items():
                        w[n] = w.get(n, 0.0) + float(z.mwh_2050) * x
                rows_c += [dict(case=case, country=c, carrier=car, node=n, share=x) for n, x in sorted(norm(w).items())]
            if case == "main":
                tot = {}
                for _, z in t.iterrows():
                    src = base if z.carrier == "ammonia" else get(z.subsector)
                    for n, x in src.items():
                        tot[n] = tot.get(n, 0.0) + float(z.mwh_2050) * x
                T = sum(tot.values())
                for n in sorted(set(tot) | set(base)):
                    comp.append(dict(country=c, node=n, v2_twh=T * base.get(n, 0.0) / 1e6, v3_twh=tot.get(n, 0.0) / 1e6))
                en = t[t.subsector.isin(["steel"]) | t.subsector.str.startswith("nonferrous")].groupby("subsector").mwh_2050.sum()
                mt = {}
                for s_, e in en.items():
                    for n, x in get(s_).items():
                        mt[n] = mt.get(n, 0.0) + float(e) * x
                rows_p += [dict(country=c, key="process_metals", node=n, share=x) for n, x in sorted(norm(mt).items())]
                rows_p += [dict(country=c, key="process_minerals", node=n, share=x) for n, x in sorted(get("cement").items())]
                rows_p += [dict(country=c, key="petrochem", node=n, share=x) for n, x in sorted(get("petrochem").items())]
    pd.DataFrame(rows_s).to_csv(V3_DIR / "INDUSTRY_NODE_SHARES_V3.csv", index=False)
    pd.DataFrame(rows_c).to_csv(V3_DIR / "INDUSTRY_CARRIER_NODE_SHARES_V3.csv", index=False)
    pd.DataFrame(rows_p).to_csv(V3_DIR / "PROCESS_NEU_NODE_SHARES_V3.csv", index=False)
    cmp_ = pd.DataFrame(comp); cmp_.to_csv(V3_DIR / "INDUSTRY_NODE_ALLOCATION_V2_V3.csv", index=False)
    for t, keys in ((pd.DataFrame(rows_c), ["case", "country", "carrier"]), (pd.DataFrame(rows_p), ["country", "key"]), (pd.DataFrame(rows_s), ["country", "subsector"])):
        bad = t.groupby(keys).share.sum().sub(1.0).abs().max()
        if bad > 1e-9:
            raise ValueError(f"shares do not sum to 1: {bad}")
    ledger.update(script=SCRIPT, inputs={k: sha256(Path(v)) for k, v in dict(dose=a.dose, regions=a.main / "research_inputs/renewable_v5/regions_onshore.geojson").items()}, subsectors_with_facility_shares=sorted({k[1] for k in S}), countries_v2_rule={s: sorted(set(v2) - {c for c, k in S if k == s}) for s in ("dispersed", "steel", "cement", "petrochem")})
    (V3_DIR / "FACILITY_SHARES_V3_EVIDENCE.json").write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in ledger.items() if k not in ("inputs",)}, indent=0)[:900])
    x = cmp_[cmp_.country == "ID"].assign(i=lambda d: d.node.str.extract(r"ID_([A-Za-z\-]+)")[0]).groupby("i")[["v2_twh", "v3_twh"]].sum().round(1); print(x.assign(v2_pct=(x.v2_twh / x.v2_twh.sum() * 100).round(1), v3_pct=(x.v3_twh / x.v3_twh.sum() * 100).round(1)).to_string())
    print("largest node change TWh", cmp_.assign(d=cmp_.v3_twh - cmp_.v2_twh).sort_values("d").iloc[[0, 1, 2, -3, -2, -1]][["node", "v2_twh", "v3_twh", "d"]].round(1).to_string())


if __name__ == "__main__":
    main()
