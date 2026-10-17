"""S4D-0 item 2 / S4D-1 item 1 (decision 93): CO2 chain inventory per node and the coastal-node table.

Coastal node (S4D instruction S4D-1 item 1): the node has an offshore region in the offshore shapes (research_inputs/renewable_v5/regions_offshore.geojson:
the research-node Voronoi cells intersected with the author offshore shapes, pypsa-asean resources/.../shapes/offshore_shapes.geojson - the regions the
offshore wind of the model uses), OR a port / LNG terminal record at the node (author ports.csv, World Port Index subset used by the pypsa-asean chain,
each ASEAN port assigned to the nearest node of its country; GEM LNG import terminals, research_inputs/lng_terminals_v5).

Unclear cases are flagged (the instruction stops on them): an offshore region without any coastline contact of the node's onshore region (Voronoi
sliver), a port record whose harbour type is a river port with no offshore region, or a node whose onshore region does not touch the sea while the node
has a port record more than 50 km away.

    python scripts_project/s4d_1_coastal_nodes.py --network <integrated_2920_3h_unsolved.nc> --output research_inputs/co2_v5
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
UP = ROOT.parents[1] / "pypsa-asean"
PORTS = UP / "resources/baseline-aims-3H-tutorial/ports.csv"
LAND = UP / "resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson"
EEZ = UP / "resources/baseline-aims-3H-tutorial/shapes/offshore_shapes.geojson"
REG_OFF = ROOT / "research_inputs/renewable_v5/regions_offshore.geojson"
REG_ON = ROOT / "research_inputs/renewable_v5/regions_onshore.geojson"
LNG = ROOT / "research_inputs/lng_terminals_v5/LNG_IMPORT_TERMINALS_GEM_2025.csv"
ISO = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
EQ = "EPSG:6933"   # equal-area for areas / distances in metres (cylindrical equal area)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gc_km(lon1, lat1, lon2, lat2):
    p1, p2 = math.radians(lat1), math.radians(lat2); dl = math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(a))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(a.network))
    geo = n.buses[n.buses.carrier.isin(["AC", "DC"])].copy()
    off = gpd.read_file(REG_OFF).set_index("node"); on = gpd.read_file(REG_ON).set_index("node")
    eez = gpd.read_file(EEZ); land = gpd.read_file(LAND)
    eez_u = eez.to_crs(EQ).union_all() if hasattr(eez, "union_all") else eez.to_crs(EQ).unary_union
    land_u = land.to_crs(EQ).union_all() if hasattr(land, "union_all") else land.to_crs(EQ).unary_union
    # ports: ASEAN rows, nearest node of the same country
    p = pd.read_csv(PORTS); p = p[p.country.isin(ISO)].copy()
    rows_p = []
    for _, r in p.iterrows():
        cand = geo[geo.country == r.country]
        if cand.empty:
            continue
        d = cand.apply(lambda b: gc_km(r.x, r.y, b.x, b.y), axis=1)
        rows_p.append(dict(port=r["name"], country=r.country, x=r.x, y=r.y, harbor_type=r.get("Harbor Type"), harbor_size=r.get("Harbor Size"), node=d.idxmin(), node_distance_km=float(d.min())))
    ports = pd.DataFrame(rows_p)
    lng = pd.read_csv(LNG)
    lng_nodes = lng.groupby("node").terminal.apply(lambda s: ";".join(sorted(set(s)))).to_dict()
    # CO2 chain inventory
    L = n.links
    def node_of(b):
        return b[:-len(" co2 stored")] if isinstance(b, str) and b.endswith(" co2 stored") else None
    buffers = set(n.stores.bus[n.stores.get("research_role", pd.Series(dtype=str)) == "CO2_BUFFER"])
    seq_links = L[L.carrier == "CO2 sequestration"]; ext_links = L[L.carrier == "CO2 export extra-ASEAN"]; pipes = L[L.carrier == "CO2 pipeline"]
    rows = []
    for node, b in geo.iterrows():
        cs = f"{node} co2 stored"
        pg = pipes[(pipes.bus0 == cs) | (pipes.bus1 == cs)]
        xb = pg[pg.border_class == "cross_border"] if "border_class" in pg else pg.iloc[0:0]
        has_off = node in off.index
        area_off = float(gpd.GeoSeries([off.loc[node, "geometry"]], crs=off.crs).to_crs(EQ).area.iloc[0] / 1e6) if has_off else 0.0
        pt = gpd.GeoSeries(gpd.points_from_xy([b.x], [b.y]), crs="EPSG:4326").to_crs(EQ).iloc[0]
        dist_sea = float(pt.distance(eez_u) / 1e3)
        on_touch = False
        if node in on.index:
            ong = gpd.GeoSeries([on.loc[node, "geometry"]], crs=on.crs).to_crs(EQ).iloc[0]
            on_touch = bool(ong.buffer(2000).intersects(eez_u))   # onshore region within 2 km of the offshore shapes = has a coastline
        pn = ports[ports.node == node]
        river_only = bool(len(pn) and pn.harbor_type.astype(str).str.contains("River|Lake|Canal", case=False).all())
        coastal_rule = bool(has_off or len(pn) or node in lng_nodes)
        basis = ";".join([x for x, ok in [("offshore_region", has_off), ("port", len(pn) > 0), ("lng_terminal", node in lng_nodes)] if ok]) or "none"
        flags = []
        if has_off and not on_touch and node in on.index:
            flags.append("offshore region but the onshore region does not touch the sea (Voronoi sliver)")
        if (not has_off) and len(pn) and river_only and node not in lng_nodes:
            flags.append("only river / lake / canal port records, no offshore region")
        if (not has_off) and (len(pn) or node in lng_nodes) and not on_touch and node in on.index:
            flags.append("port / LNG record but the onshore region does not touch the sea")
        if node not in on.index and not has_off:
            flags.append("no onshore region (converter node)")
        rows.append(dict(node=node, country=str(b.country), x=float(b.x), y=float(b.y), carrier=str(b.carrier), has_onshore_region=node in on.index, onshore_region_touches_sea=on_touch,
                         has_offshore_region=has_off, offshore_region_km2=round(area_off, 1), node_distance_to_offshore_shapes_km=round(dist_sea, 1),
                         ports=";".join(pn.port.astype(str)) if len(pn) else "", port_types=";".join(pn.harbor_type.astype(str)) if len(pn) else "",
                         port_min_distance_km=round(float(pn.node_distance_km.min()), 1) if len(pn) else None, lng_terminals=lng_nodes.get(node, ""),
                         coastal=coastal_rule, basis=basis, unclear="; ".join(flags), co2_buffer=cs in buffers,
                         domestic_sequestration_link=bool((seq_links.bus0 == cs).any()), extra_asean_export_link=bool((ext_links.bus0 == cs).any()),
                         co2_pipeline_candidates=int(len(pg)), co2_pipeline_cross_border=int(len(xb))))
    t = pd.DataFrame(rows).sort_values(["country", "node"])
    a.output.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.output / "COASTAL_NODES_S4D1.csv", index=False)
    ports.to_csv(a.output / "PORTS_ASEAN_TO_NODES_S4D1.csv", index=False)
    summ = dict(nodes=int(len(t)), coastal=int(t.coastal.sum()), inland=int((~t.coastal).sum()), unclear=t.loc[t.unclear != "", ["node", "country", "basis", "unclear"]].to_dict("records"),
                by_country={c: dict(nodes=int(len(x)), coastal=int(x.coastal.sum()), inland=sorted(x.node[~x.coastal])) for c, x in t.groupby("country")},
                inland_with_buffer=sorted(t.node[(~t.coastal) & t.co2_buffer]), buffers=int(t.co2_buffer.sum()),
                sources=dict(regions_offshore=dict(path=str(REG_OFF.relative_to(ROOT)), sha256=sha(REG_OFF)), regions_onshore=dict(path=str(REG_ON.relative_to(ROOT)), sha256=sha(REG_ON)),
                             offshore_shapes=dict(path=str(EEZ), sha256=sha(EEZ)), country_shapes=dict(path=str(LAND), sha256=sha(LAND)), ports=dict(path=str(PORTS), sha256=sha(PORTS)),
                             lng_terminals=dict(path=str(LNG.relative_to(ROOT)), sha256=sha(LNG)), network=dict(path=str(a.network), sha256=sha(a.network))))
    (a.output / "COASTAL_NODES_S4D1.json").write_text(json.dumps(summ, indent=1, default=str))
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(t[["node", "country", "has_offshore_region", "offshore_region_km2", "onshore_region_touches_sea", "node_distance_to_offshore_shapes_km", "ports", "lng_terminals", "coastal", "basis", "unclear", "co2_buffer", "co2_pipeline_candidates", "co2_pipeline_cross_border"]].to_string())
    print(json.dumps({k: v for k, v in summ.items() if k in ("nodes", "coastal", "inland", "unclear", "by_country", "inland_with_buffer")}, default=str)[:4000])


if __name__ == "__main__":
    main()
