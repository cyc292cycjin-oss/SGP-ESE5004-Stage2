"""S4D-1 stop diagnostic (decision 93): why some nodes are unclear under the instruction rule (offshore region OR port / LNG record).

The offshore shapes are the author EEZ polygons; internal waters (inside straight baselines, e.g. the Bight of Bangkok, Cambodian coast) and Indonesian /
Philippine archipelagic waters are NOT in them (same gap as S4C-1). For every node with a captured-CO2 buffer this script measures whether the node's onshore
region reaches the outer edge of the ASEAN land shapes (= coastline or a land border with a non-ASEAN country), how far that edge lies from the EEZ shapes
(an edge next to the EEZ is coast facing internal / archipelagic waters; an edge far from any EEZ is a land border with CN / IN / BD), and the great-circle
distance from the node to that edge. Read-only; no model change.

    python scripts_project/s4d_1_coast_diagnostic.py --output research_inputs/co2_v5
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.ops import nearest_points

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
UP = ROOT.parents[1] / "pypsa-asean"
LAND = UP / "resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson"
EEZ = UP / "resources/baseline-aims-3H-tutorial/shapes/offshore_shapes.geojson"
REG_ON = ROOT / "research_inputs/renewable_v5/regions_onshore.geojson"
EQ = "EPSG:6933"


def gc_km(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2); dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(a))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    t = pd.read_csv(a.output / "COASTAL_NODES_S4D1.csv")
    land = gpd.read_file(LAND); eez = gpd.read_file(EEZ); on = gpd.read_file(REG_ON).set_index("node")
    land_u = land.union_all() if hasattr(land, "union_all") else land.unary_union
    eez_eq = eez.to_crs(EQ); eez_u_eq = eez_eq.union_all() if hasattr(eez_eq, "union_all") else eez_eq.unary_union
    edge = land_u.boundary   # outer edge of the ASEAN land (coastline incl. internal-water coasts, and land borders with non-ASEAN countries)
    edge_eq = gpd.GeoSeries([edge], crs="EPSG:4326").to_crs(EQ).iloc[0]
    rows = []
    for _, r in t[t.co2_buffer].iterrows():
        node = r.node
        reg = on.loc[node, "geometry"] if node in on.index else None
        reaches = bool(reg is not None and reg.buffer(0.02).intersects(edge))   # ~2 km in degrees
        seg = reg.buffer(0.02).intersection(edge) if reaches else None
        seg_eq = gpd.GeoSeries([seg], crs="EPSG:4326").to_crs(EQ).iloc[0] if reaches else None
        seg_to_eez = float(seg_eq.distance(eez_u_eq) / 1e3) if reaches else None
        seg_len = float(seg_eq.length / 1e3) if reaches else 0.0
        p = Point(r.x, r.y)
        q = nearest_points(p, edge)[1]
        d_edge = gc_km(r.x, r.y, q.x, q.y)
        kind = ("coast (edge next to the EEZ shapes)" if reaches and seg_to_eez is not None and seg_to_eez <= 60 else
                "land border with a non-ASEAN country or far coast" if reaches else "interior (region does not reach the ASEAN land edge)")
        rows.append(dict(node=node, country=r.country, rule_coastal=bool(r.coastal), rule_basis=r.basis, has_offshore_region=bool(r.has_offshore_region), ports=r.ports if isinstance(r.ports, str) else "",
                         region_reaches_land_edge=reaches, edge_length_km=round(seg_len, 1), edge_distance_to_eez_km=(round(seg_to_eez, 1) if seg_to_eez is not None else None),
                         node_to_land_edge_km=round(d_edge, 1), edge_kind=kind,
                         disagreement=bool(r.coastal) != (kind.startswith("coast"))))
    d = pd.DataFrame(rows).sort_values(["country", "node"])
    d.to_csv(a.output / "COASTAL_NODES_S4D1_DIAGNOSTIC.csv", index=False)
    # projection check: equal-area distance vs great circle for one coastal pair
    chk = dict(node="BN4 0")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(d[d.disagreement | (~d.rule_coastal)].to_string())
    print("disagreements:", int(d.disagreement.sum()), "of", len(d))
    print(d.groupby(["rule_coastal", "edge_kind"]).size().to_string())


if __name__ == "__main__":
    main()
