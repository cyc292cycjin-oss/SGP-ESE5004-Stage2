"""S4D-1 item 1 (decision 93; user decision 2026-10-17 on stop report S4D_STOP_01: option A with the physical coastline, consistent with the
'not-land' reading of supplement 01): final coastal-node table.

A node is coastal when
  (1) its onshore region touches the physical coast - any sea, internal waters and archipelagic waters included (e.g. the Bight of Bangkok, the Cambodian
      coast), not the EEZ alone; contact length reported per node; or
  (2) a sea port (World Port Index harbour type not River / Lake / Canal; author ports.csv, nearest node of the same country) or an LNG import terminal
      (GEM, research_inputs/lng_terminals_v5) is recorded at the node; river-only port records do not count (draught); or
  (3) it is a converter node without an onshore region lying within 5 km of the sea.
Reason (registered): the IEAGHG (2004) ship-transport cost already contains the port, buffer-tank and loading facilities, so a coast is enough to build a
CO2 loading terminal; river ports are excluded for lack of draught.

Sea mask: the author offshore shapes (EEZ) plus the internal / archipelagic waters, found as the holes of union(author land shapes, EEZ) that touch the EEZ
(water enclosed by coast and baselines); holes that do not touch the EEZ are lakes; foreign land (CN, IN, BD) lies outside the union and never counts.
A morphological opening of 1 km removes the slivers left by misaligned country borders and border rivers. Lengths in EPSG:6933 (equal area, metres).

    python scripts_project/s4d_1_coastline.py --output research_inputs/co2_v5
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import nearest_points, unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
UP = ROOT.parents[1] / "pypsa-asean"
LAND = UP / "resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson"
EEZ = UP / "resources/baseline-aims-3H-tutorial/shapes/offshore_shapes.geojson"
REG_ON = ROOT / "research_inputs/renewable_v5/regions_onshore.geojson"
EQ = "EPSG:6933"
OPEN_M = 1000.0      # morphological opening radius (slivers)
TOUCH_M = 1000.0     # contact tolerance between region boundary and sea
MIN_CONTACT_KM = 1.0 # a contact shorter than this is a corner touch, not a coast
CONVERTER_KM = 5.0
# sea-mask spot checks (lon, lat): internal / archipelagic waters named in the user decision must be sea; Tonle Sap must not
MASK_CHECKS = {"Bight of Bangkok": (100.6, 13.3), "Cambodian coast (Kampot)": (104.1, 10.5), "Gulf of Martaban": (97.0, 16.2), "Java Sea": (110.0, -5.5),
               "Makassar Strait": (118.5, -2.0), "Sibuyan Sea": (122.5, 12.5), "Gulf of Tonkin": (107.5, 20.5), "Tonle Sap (lake)": (104.0, 12.9)}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def polys(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    t = pd.read_csv(a.output / "COASTAL_NODES_S4D1.csv").set_index("node")
    ports = pd.read_csv(a.output / "PORTS_ASEAN_TO_NODES_S4D1.csv")
    land = gpd.read_file(LAND).to_crs(EQ); eez = gpd.read_file(EEZ).to_crs(EQ); on = gpd.read_file(REG_ON).to_crs(EQ).set_index("node")
    land_u = unary_union(land.geometry); eez_u = unary_union(eez.geometry)
    U = unary_union([land_u, eez_u])
    holes = [Polygon(r) for p in polys(U) for r in p.interiors]
    internal = [h for h in holes if h.distance(eez_u) <= 1000.0]
    lakes = [h for h in holes if h.distance(eez_u) > 1000.0]
    sea = unary_union([eez_u] + internal).buffer(-OPEN_M).buffer(OPEN_M)
    sea_touch = sea.buffer(TOUCH_M)
    sea_ports = ports[~ports.harbor_type.astype(str).str.contains("River|Lake|Canal", case=False)]
    river_ports = ports[ports.harbor_type.astype(str).str.contains("River|Lake|Canal", case=False)]
    on_u = unary_union(on.geometry)

    def between(g):
        """Region-to-sea distance and who owns the land on the shortest line to the sea (a gap in the regions would be a shape error)."""
        a, b = nearest_points(g, sea); line = LineString([a, b]); own = []
        for s in (0.25, 0.5, 0.75):
            p = line.interpolate(s, normalized=True)
            o = [i for i, h in on.geometry.items() if h.contains(p)]
            own += o or (["land without region"] if land_u.contains(p) else [])
        return line.length / 1e3, "/".join(dict.fromkeys(own))

    rows = []
    for node, r in t.iterrows():
        contact_km = 0.0; reg_sea_km = None; strip = ""
        if node in on.index:
            b = on.loc[node, "geometry"].boundary
            contact_km = float(b.intersection(sea_touch).length / 1e3)
            if contact_km < MIN_CONTACT_KM:
                reg_sea_km, strip = between(on.loc[node, "geometry"])
        pt = gpd.GeoSeries([Point(r.x, r.y)], crs="EPSG:4326").to_crs(EQ).iloc[0]
        d_sea_km = 0.0 if sea.contains(pt) else float(pt.distance(sea) / 1e3)
        sp = sea_ports[sea_ports.node == node]; rp = river_ports[river_ports.node == node]
        lng = r.lng_terminals if isinstance(r.lng_terminals, str) else ""
        by_coast = contact_km >= MIN_CONTACT_KM
        by_port = len(sp) > 0 or bool(lng)
        by_conv = (node not in on.index) and d_sea_km <= CONVERTER_KM
        coastal = bool(by_coast or by_port or by_conv)
        basis = []
        if by_coast:
            basis.append(f"coast contact {contact_km:.1f} km")
        if len(sp):
            basis.append("sea port " + "/".join(sp.port.astype(str)))
        if lng:
            basis.append("LNG " + lng)
        if by_conv:
            basis.append(f"converter node {d_sea_km:.1f} km from the sea")
        if not coastal:
            reg = f"region {reg_sea_km:.1f} km from the sea, land between in region {strip}" if reg_sea_km is not None else "no onshore region"
            basis.append(("river port only: " + "/".join(rp.port.astype(str)) + "; " if len(rp) else "") + f"no coast contact ({reg}; node {d_sea_km:.0f} km from the sea)")
        rows.append(dict(node=node, country=r.country, coastal=coastal, basis="; ".join(basis), coast_contact_km=round(contact_km, 1),
                         region_distance_to_sea_km=None if reg_sea_km is None else round(reg_sea_km, 1), land_to_sea_in_region=strip, node_distance_to_sea_km=round(d_sea_km, 1),
                         sea_ports="/".join(sp.port.astype(str)), river_ports="/".join(rp.port.astype(str)), lng_terminals=lng, has_onshore_region=node in on.index,
                         has_offshore_region_eez=bool(r.has_offshore_region), coastal_previous_rule=bool(r.coastal), co2_buffer=bool(r.co2_buffer)))
    f = pd.DataFrame(rows).sort_values(["country", "node"])
    f.to_csv(a.output / "COASTAL_NODES_S4D1_FINAL.csv", index=False)
    b = f[f.co2_buffer]
    spots = gpd.GeoSeries([Point(*v) for v in MASK_CHECKS.values()], crs="EPSG:4326").to_crs(EQ)
    land_gap = {c: round(g.difference(on_u).difference(sea).area / 1e6, 1) for c, g in zip(land.name, land.geometry)}
    summ = dict(rule="option A with the physical coastline (user decision 2026-10-17)", open_m=OPEN_M, touch_m=TOUCH_M, min_contact_km=MIN_CONTACT_KM, converter_km=CONVERTER_KM,
                sea_mask=dict(internal_water_polygons=len(internal), internal_water_km2=round(sum(h.area for h in internal) / 1e6, 0), lakes_excluded=len(lakes),
                              spot_checks={k: bool(sea.contains(p)) for k, p in zip(MASK_CHECKS, spots)},
                              land_not_in_any_onshore_region_km2=land_gap),
                nodes=int(len(f)), coastal=int(f.coastal.sum()), buffered=dict(coastal=int(b.coastal.sum()), inland=int((~b.coastal).sum()), inland_nodes=sorted(b.node[~b.coastal])),
                changed_vs_instruction_rule=f.loc[f.coastal != f.coastal_previous_rule, ["node", "country", "coastal", "basis"]].to_dict("records"),
                coast_only_no_eez_region=f.loc[f.coastal & ~f.has_offshore_region_eez, ["node", "basis"]].to_dict("records"),
                sources=dict(land=dict(path=str(LAND), sha256=sha(LAND)), eez=dict(path=str(EEZ), sha256=sha(EEZ)), regions_onshore=dict(path=str(REG_ON.relative_to(ROOT)), sha256=sha(REG_ON))))
    (a.output / "COASTAL_NODES_S4D1_FINAL.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False))
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 110)
    print(f[["node", "country", "coastal", "coast_contact_km", "node_distance_to_sea_km", "basis"]].to_string())
    print(json.dumps({k: v for k, v in summ.items() if k != "sources"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
