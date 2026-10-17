"""S4D-1 stop diagnostic (decision 93): which node's onshore region contains each ASEAN port (author ports.csv) and LNG import terminal (point in polygon),
compared with the nearest-node assignment of the instruction rule; and the coastal classification under the options of S4D_STOP_01 section 5. Read-only.

    python scripts_project/s4d_1_port_regions.py --output research_inputs/co2_v5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REG_ON = ROOT / "research_inputs/renewable_v5/regions_onshore.geojson"
LNG = ROOT / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    on = gpd.read_file(REG_ON)
    t = pd.read_csv(a.output / "COASTAL_NODES_S4D1.csv").set_index("node")
    p = pd.read_csv(a.output / "PORTS_ASEAN_TO_NODES_S4D1.csv")
    lng = pd.read_csv(LNG)
    pts = pd.concat([p.assign(kind="port", name=p.port, nearest_node=p.node)[["kind", "name", "country", "x", "y", "harbor_type", "nearest_node"]],
                     lng.assign(kind="lng_terminal", name=lng.terminal, x=lng.longitude, y=lng.latitude, harbor_type="", nearest_node=lng.node)[["kind", "name", "country", "x", "y", "harbor_type", "nearest_node"]]])
    g = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts.x, pts.y), crs="EPSG:4326")
    j = gpd.sjoin(g, on[["node", "geometry"]], how="left", predicate="within").rename(columns={"node": "region_node"})
    j["agrees"] = j.region_node == j.nearest_node
    j["river"] = j.harbor_type.astype(str).str.contains("River|Lake|Canal", case=False)
    j.drop(columns=["geometry", "index_right"], errors="ignore").to_csv(a.output / "PORT_LNG_REGION_S4D1.csv", index=False)
    # option A: offshore region, or a sea port / LNG terminal inside the node's onshore region; converter nodes (no onshore region): node within 5 km of the
    # offshore shapes or an LNG terminal assigned to it
    sea_in = set(j.region_node[(~j.river) & j.region_node.notna()])
    conv = t.index[~t.has_onshore_region]
    optA = {nd: bool(r.has_offshore_region or nd in sea_in or (nd in conv and (r.node_distance_to_offshore_shapes_km <= 5 or isinstance(r.lng_terminals, str))))
            for nd, r in t.iterrows()}
    optB = {nd: bool(r.coastal) for nd, r in t.iterrows()}   # instruction rule as written (nearest-node port / LNG)
    optC = {nd: bool(r.has_offshore_region) for nd, r in t.iterrows()}   # offshore region only
    rows = [dict(node=nd, country=t.at[nd, "country"], co2_buffer=bool(t.at[nd, "co2_buffer"]), A=optA[nd], B=optB[nd], C=optC[nd]) for nd in t.index]
    o = pd.DataFrame(rows); o.to_csv(a.output / "COASTAL_OPTIONS_S4D1.csv", index=False)
    b = o[o.co2_buffer]
    summ = {k: dict(coastal=int(b[k].sum()), inland=int((~b[k]).sum()), inland_nodes=sorted(b.node[~b[k]])) for k in ["A", "B", "C"]}
    summ["A_vs_B_differ"] = sorted(b.node[b.A != b.B]); summ["A_vs_C_differ"] = sorted(b.node[b.A != b.C])
    (a.output / "COASTAL_OPTIONS_S4D1.json").write_text(json.dumps(summ, indent=1))
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(j[(~j.agrees) | j.river][["kind", "name", "country", "harbor_type", "nearest_node", "region_node"]].to_string())
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
