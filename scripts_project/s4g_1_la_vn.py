"""S4G-1 item 6 (record only, no download, no model change): in-repo evidence on the operating Lao PDR - Viet Nam cross-border lines (the author's AIMS
existing total for LA-VN is 1 MW). Sources searched: AIMS transmission-project tables (data/transmission_projects/AIMS/*.csv), the APG AIMS III
extraction (APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv) and the corridor cross-check (CORRIDOR_APG_CROSSCHECK_2024.csv), the OSM prebuilt line
tables (data/osm-*prebuilt/*/all_lines_build_network.csv; end points located with the author country shapes), the pypsa-asean pre-clustering
network (base.nc) and the frozen electric base, and the GEM power-plant table (Lao plants with a Vietnamese operator / owner / partner; GEM has no
line data).

    python scripts_project/s4g_1_la_vn.py --out research_inputs/corridors/LA_VN_STOCK_CHECK_S4G1.json
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely import wkt

from d1_common import ROOT, SRC_DIR, sha256
from s4c_1_subsea_shares import AUTHOR

PA = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean")


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); a = ap.parse_args()
    shp = gpd.read_file(AUTHOR / "country_shapes.geojson")
    key = next(c for c in ("name", "country", "GID_0", "iso") if c in shp.columns)
    polys = list(shp.geometry); names = [str(x) for x in shp[key]]; tree = shapely.STRtree(polys)

    def country(x, y):
        pt = shapely.Point(float(x), float(y)); hit = tree.query(pt, predicate="intersects")
        if len(hit):
            return names[int(hit[0])]
        j = int(tree.nearest(pt)); return names[j] + "?"   # nearest shape (point offshore / outside)
    pair = lambda c0, c1: {c0.rstrip("?"), c1.rstrip("?")} == {"LA", "VN"}
    out = dict(shapes=str(AUTHOR / "country_shapes.geojson"), shape_key=key, sources={}, found={})
    # 1. AIMS tables
    aims = []
    for f in sorted((ROOT / "data/transmission_projects/AIMS").glob("*.csv")):
        t = pd.read_csv(f, index_col=0)
        out["sources"][str(f.relative_to(ROOT))] = dict(sha256=sha256(f), rows=len(t))
        for k, r in t.iterrows():
            c0, c1 = country(r.x0, r.y0), country(r.x1, r.y1)
            if pair(c0, c1):
                aims.append(dict(table=f.name, name=str(k), status=str(r.project_status), build_year=r.build_year, length_km=r.length,
                                 v_nom=r.get("v_nom"), p_nom=r.get("p_nom"), num_parallel=r.get("num_parallel"), type=r.get("type"), ends=[c0, c1]))
    out["found"]["aims"] = aims
    # 2. APG extraction and corridor cross-check
    apg = pd.read_csv(SRC_DIR / "APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv", dtype=str, keep_default_na=False)
    out["sources"]["APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv"] = dict(sha256=sha256(SRC_DIR / "APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv"))
    out["found"]["apg"] = apg[(apg.country_a + apg.country_b).isin(["LAVN", "VNLA"])].to_dict("records")
    cc = ROOT / "research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv"
    if cc.exists():
        t = pd.read_csv(cc, dtype=str, keep_default_na=False); out["sources"][str(cc.relative_to(ROOT))] = dict(sha256=sha256(cc))
        out["found"]["corridor_crosscheck"] = t[t.apply(lambda r: ("LA" in r.values and "VN" in r.values) or r.astype(str).str.contains("LA-VN|VN-LA|Lao PDR - Viet").any(), axis=1)].to_dict("records")
    # 3. OSM prebuilt line tables
    osm = {}
    for f in sorted(ROOT.glob("data/osm*prebuilt/*/all_lines_build_network.csv")):
        t = pd.read_csv(f); hits = []
        for _, r in t.iterrows():
            try:
                g = wkt.loads(r.geometry)
            except Exception:
                continue
            coords = [c for part in (g.geoms if hasattr(g, "geoms") else [g]) for c in part.coords]
            cs = {country(x, y).rstrip("?") for x, y in (coords[0], coords[-1])}
            allc = {country(x, y).rstrip("?") for x, y in coords[:: max(1, len(coords) // 20)]}
            if {"LA", "VN"} <= (cs | allc):
                hits.append(dict(line_id=r.line_id, voltage_kv=float(r.voltage) / 1e3, circuits=r.circuits, dc=bool(r.dc), length_km=float(r.length) / 1e3,
                                 end_countries=sorted(cs), countries_along=sorted(allc)))
        osm[str(f.relative_to(ROOT))] = dict(sha256=sha256(f), rows=len(t), la_vn=hits)
    out["found"]["osm_prebuilt"] = osm
    # 4. pypsa-asean pre-clustering network and the frozen base
    import pypsa
    nets = {}
    for tag, p in (("pypsa_asean_base", PA / "networks/baseline-aims-3H-tutorial/base.nc"), ("frozen_electric_base", ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc")):
        if not p.exists():
            continue
        n = pypsa.Network(str(p)); c = n.buses.country
        L = n.lines[(c.reindex(n.lines.bus0).values + c.reindex(n.lines.bus1).values == "LAVN") | (c.reindex(n.lines.bus0).values + c.reindex(n.lines.bus1).values == "VNLA")]
        K = n.links[(c.reindex(n.links.bus0).values + c.reindex(n.links.bus1).values == "LAVN") | (c.reindex(n.links.bus0).values + c.reindex(n.links.bus1).values == "VNLA")]
        nets[tag] = dict(file=str(p), lines=[dict(name=str(k), v_nom=float(z.get("v_nom", float("nan"))), num_parallel=float(z.num_parallel), s_nom=float(z.s_nom), length=float(z.length),
                                                  type=str(z.type), build_year=float(z.get("build_year", 0))) for k, z in L.iterrows()],
                         links=[dict(name=str(k), p_nom=float(z.p_nom), carrier=str(z.carrier)) for k, z in K.iterrows()])
    out["found"]["networks"] = nets
    # 5. GEM: Lao plants with a Vietnamese operator / owner / parent (ownership is not an export line; GEM has no line data)
    g = pd.read_csv(SRC_DIR / "GEM_GIPT_2026-09_ASEAN11.csv", dtype=str, keep_default_na=False)
    out["sources"]["GEM_GIPT_2026-09_ASEAN11.csv"] = dict(sha256=sha256(SRC_DIR / "GEM_GIPT_2026-09_ASEAN11.csv"))
    la = g[g["Country/area"] == "Laos"]
    viet = la[la[["Operator(s)", "Owner(s)", "Parent(s)", "Plant / Project name (other)", "Country/area 2 (hydropower only)"]].apply(lambda r: r.str.contains("Viet", case=False).any(), axis=1)]
    out["found"]["gem_lao_plants_vietnamese_party"] = viet[["Plant / Project name", "Unit / Phase name", "Capacity (MW)", "Status", "Start year", "Type", "Operator(s)", "Owner(s)",
                                                            "Country/area 2 (hydropower only)", "Latitude", "Longitude"]].to_dict("records")
    a.out.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({k: (v if k != "osm_prebuilt" else {f: x["la_vn"] for f, x in v.items()}) for k, v in out["found"].items()}, indent=1, default=str)[:12000])


if __name__ == "__main__":
    main()
