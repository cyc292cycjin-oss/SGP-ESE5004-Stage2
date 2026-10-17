"""S4E-1 (decision 94, implementing decision 15): complete the adjacent cross-border corridors.

Rules (S4E instruction S4E-1; candidates only - capacity 0, built or not by the model; the 2025 cross-border stock stays the starting point):
  1. Land adjacency: two nodes of different countries are adjacent when their onshore regions (S4A Voronoi regions,
     research_inputs/renewable_v5/regions_onshore.geojson) share a border of >= 1 km (boundary of one region inside the other buffered by 1 km, to
     absorb misaligned country shapes; the 1 km corner-touch rule of the S4D-1 coastal table). Every adjacent pair not already joined by a
     cross-border line / DC link becomes a candidate corridor.
  2. Cross-sea: only the ACE (2024) APG AIMS III priority projects across the sea (#4 Peninsular Malaysia - Sumatera, #7 Philippines - Sabah,
     #15 East Sabah - North Kalimantan, #16 Singapore - Sumatera with #5 Batam merged); end points = the nearest pair of nodes of the two named
     areas (great-circle); a pair already found by rule 1 is not repeated. 'other initiative' projects (SG-VN, SG-KH) are registered as
     optional candidates, not added.
  3. Stock: APG existing_MW against the corridor table's 2025 capacities; differences are listed, verified stock is not changed.
  4. Domestic (decision 35 consistency): APG national projects (#3 Sarawak - Peninsular, #8b Sarawak - Sabah, #18a Kalimantan - Java, #18b
     Sumatera - Java) checked for a domestic line / DC link; missing ones are added as domestic candidates (both scenarios).
  5. Parameters as before: length = great-circle x 1.25 (registry corridor_length_factor_frozen_base); subsea share by the S4C supplement 01 rule
     (same landmass of the two node locations -> 0, else the not-land share of the great-circle route; s4c_1_subsea_shares.classify); type:
     AC line when both node locations lie on the same landmass (overland, like the existing cross-border lines), else DC link (HVDC, like the
     existing inter-island links of the frozen base); cost: decision-50 cost layer (S4C-1: AC length x ((1 - s) HVAC overhead + s HVAC
     submarine); DC length x ((1 - s) HVDC overhead + s HVDC submarine) + inverter pair) at build time; H2 / CO2 / gas pipeline candidates follow
     the electricity topology (decision 59).

    python scripts_project/s4e_1_corridors.py --network <S4D-6 integrated build>
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Geod

from carrier_architecture import COUNTRIES
from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv
from s4c_1_subsea_shares import AUTHOR, classify
from s4d_layers import connected_coalitions

SCRIPT = "scripts_project/s4e_1_corridors.py"
INSTRUCTION_SHA = "e5c184c12a91a89ac52e151661cf593a75139396436b95bb75ef0c1cfbb7e9db"
OUT = ROOT / "research_inputs/corridors"
CORR = OUT / "cross_border_corridors.csv"
SUB = OUT / "SUBSEA_SHARE_S4C1.csv"
APG = SRC_DIR / "APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv"
REG_ON = ROOT / "research_inputs/renewable_v5/regions_onshore.geojson"
TOL_M, MIN_KM, LENGTH_FACTOR = 1000.0, 1.0, 1.25
CROSS_SEA = [("4", "MY_Peninsular", "ID_Sumatra", "Peninsular Malaysia - Sumatera"), ("7", "PH", "MY_Sabah", "Philippines - Sabah"),
             ("15", "MY_Sabah", "ID_Kalimantan", "East Sabah - North Kalimantan"), ("16", "SG", "ID_Sumatra", "Singapore - Sumatera (#5 Batam merged)")]
OPTIONAL = [("other1", "SG", "VN", "Singapore - Vietnam"), ("other2", "SG", "KH", "Singapore - Cambodia")]
DOMESTIC = [("3", "MY_Sarawak", "MY_Peninsular", "Sarawak - Peninsular Malaysia"), ("8b", "MY_Sarawak", "MY_Sabah", "Sarawak - Sabah"),
            ("18a", "ID_Kalimantan", "ID_Java", "Kalimantan - Java"), ("18b", "ID_Sumatra", "ID_Java", "Sumatera - Java")]
# corridor-table components -> APG project (s3_0_corridors.COMPONENT_TO_APG)
from s3_0_corridors import COMPONENT_TO_APG  # noqa: E402


def hav(x0, y0, x1, y1):
    p0, p1 = np.radians(y0), np.radians(y1); dl = np.radians(x1 - x0)
    return float(2 * 6371.0 * np.arcsin(np.sqrt(np.sin((p1 - p0) / 2) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2) ** 2)))


def fill_missing_pairs(network: Path) -> list:
    """Second pass: the new topology changes side structures built from it (the S3-1 gas connectivity upgrade joins every gas node without a
    pipeline candidate to the nearest node of its country that has one), so node pairs absent from SUBSEA_SHARE_S4E1.csv can appear. For a
    network built with --override corridors.subsea_share=zero, every line / DC / B2B / pipeline node pair missing from the table is classified
    with the same method (s4c_1_subsea_shares.classify + same-landmass rule) and appended."""
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network)); b = n.buses
    S = pd.read_csv(OUT / "SUBSEA_SHARE_S4E1.csv"); have = set(zip(S.loc0, S.loc1))
    land = gpd.read_file(AUTHOR / "country_shapes.geojson").union_all(); off = gpd.read_file(AUTHOR / "offshore_shapes.geojson").union_all()
    shapely.prepare(land); shapely.prepare(off); polys = list(land.geoms); tree = shapely.STRtree(polys); geod = Geod(ellps="WGS84")
    suffixes = (" gas", " H2", " co2 stored", " oil")

    def loc(bus):   # as s4c_1_subsea_shares.loc
        l = str(b.at[bus, "location"]) if "location" in b and str(b.at[bus, "location"]) not in ("", "nan") else bus
        if l not in b.index or (float(b.at[l, "x"]) == 0.0 and float(b.at[l, "y"]) == 0.0):
            for s in suffixes:
                if bus.endswith(s) and bus[: -len(s)] in b.index:
                    l = bus[: -len(s)]; break
        return l

    def landmass(node):
        pt = shapely.Point(float(b.at[node, "x"]), float(b.at[node, "y"])); hit = tree.query(pt, predicate="intersects")
        if len(hit):
            return int(hit[0]), 0.0
        j = int(tree.nearest(pt)); return j, float(polys[j].distance(pt))
    comps = [("Line", k, z.bus0, z.bus1, "AC") for k, z in n.lines.iterrows()]
    comps += [("Link", k, z.bus0, z.bus1, z.carrier) for k, z in n.links[n.links.carrier.isin(["DC", "B2B", "H2 pipeline", "CO2 pipeline", "gas pipeline"])].iterrows()]
    new = {}
    for typ, k, b0, b1, car in comps:
        key = tuple(sorted((loc(b0), loc(b1))))
        if key[0] == key[1] or key in have:
            continue
        new.setdefault(key, []).append(f"{typ}:{car}:{k}")
    rows = []
    for (l0, l1), names in sorted(new.items()):
        v = classify(geod, land, off, float(b.at[l0, "x"]), float(b.at[l0, "y"]), float(b.at[l1, "x"]), float(b.at[l1, "y"]))
        (m0, o0), (m1, o1) = landmass(l0), landmass(l1); same = m0 == m1
        c0, c1 = str(b.at[l0, "country"]), str(b.at[l1, "country"])
        rows.append(dict(loc0=l0, loc1=l1, country0=c0, country1=c1, cross_border=c0 != c1, candidate=True, **v, components=";".join(sorted({x.rsplit(":", 1)[0] for x in names})),
                         n_components=len(names), names=";".join(sorted(x.split(":", 2)[2] for x in names))[:400], check_expectation="", check_label="S4E-1 topology side effect (second pass)",
                         landmass0=m0, landmass1=m1, offland_deg0=o0, offland_deg1=o1, same_landmass=same, share_zero=0.0, share_geometric_all=v["subsea_share_not_land"],
                         share_landmass_nonland=(0.0 if same else v["subsea_share_not_land"]),
                         main_rule=("same landmass -> 0 (overland route)" if same else "different landmass -> not-land share")))
    if rows:
        S = pd.concat([S, pd.DataFrame(rows)[S.columns]], ignore_index=True)
        S.to_csv(OUT / "SUBSEA_SHARE_S4E1.csv", index=False)
    return rows


def main():
    import pypsa
    from sector_adapter import dc_to_ac
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--fill-from", type=Path, default=None,
                                                                                                            help="second pass: network built with corridors.subsea_share=zero")
    a = ap.parse_args()
    if a.fill_from is not None:
        rows = fill_missing_pairs(a.fill_from)
        js = json.loads((OUT / "CORRIDORS_S4E1.json").read_text())
        js["second_pass"] = dict(network=str(a.fill_from), added_pairs=[{k: r[k] for k in ("loc0", "loc1", "country0", "country1", "components", "great_circle_km", "same_landmass",
                                                                                              "share_landmass_nonland", "gap_share")} for r in rows])
        (OUT / "CORRIDORS_S4E1.json").write_text(json.dumps(js, indent=1, default=str))
        print(json.dumps(js["second_pass"], indent=1, default=str))
        return
    n = pypsa.Network(str(a.network)); b = n.buses
    geo = b[b.carrier.isin(["AC", "DC"])]
    dcm = dc_to_ac(n)
    cor = pd.read_csv(CORR, float_precision="round_trip"); sub = pd.read_csv(SUB)
    apg = pd.read_csv(APG, dtype=str, keep_default_na=False)
    # existing joins (lines / DC links), by AC node pair
    def pair(x, y):
        return tuple(sorted((dcm.get(x, x), dcm.get(y, y))))
    joins = {}
    for typ in ("Line", "Link"):
        d = n.df(typ); d = d[d.carrier.isin(["AC", "DC"])]
        for k, z in d.iterrows():
            joins.setdefault(pair(z.bus0, z.bus1), []).append(f"{typ}:{k}")
    # 1. land adjacency of the onshore regions
    on = gpd.read_file(REG_ON).to_crs("EPSG:6933").set_index("node")
    idx = list(on.index); sidx = on.sindex; adj = []
    for x in idx:
        gx = on.at[x, "geometry"]
        for j in sidx.query(gx.buffer(3 * TOL_M), predicate="intersects"):
            y = idx[j]
            if y <= x or on.at[y, "country"] == on.at[x, "country"]:
                continue
            gy = on.at[y, "geometry"]
            L1 = gx.boundary.intersection(gy.buffer(TOL_M)).length / 1e3
            L3 = gx.boundary.intersection(gy.buffer(3 * TOL_M)).length / 1e3
            if L3 <= 0:
                continue
            p = tuple(sorted((x, y))); ex = joins.get(p, [])
            adj.append(dict(node_a=p[0], node_b=p[1], country_a=b.at[p[0], "country"], country_b=b.at[p[1], "country"], shared_border_km=round(L1, 2),
                            shared_border_km_3km_tol=round(L3, 2), adjacent=bool(L1 >= MIN_KM), existing_components=";".join(ex),
                            action=("existing corridor" if ex else ("new candidate" if L1 >= MIN_KM else "not adjacent (< 1 km)")),
                            basis=f"onshore regions share {L1:.1f} km of border (1 km tolerance)"))
    adj = pd.DataFrame(adj).sort_values(["country_a", "country_b", "node_a", "node_b"])
    unclear = adj[(adj.shared_border_km > 0) & (adj.shared_border_km < MIN_KM)]
    # 2. cross-sea APG projects: nearest node pair
    xy = geo[["x", "y"]]

    def nearest(ga, gb):
        A = [i for i in geo.index if i.startswith(ga) and dcm.get(i, i) == i]; B = [i for i in geo.index if i.startswith(gb) and dcm.get(i, i) == i]
        best = sorted((hav(xy.at[p, "x"], xy.at[p, "y"], xy.at[q, "x"], xy.at[q, "y"]), p, q) for p in A for q in B)
        return best[0], best[1:3]
    sea = []
    for no, ga, gb, label in CROSS_SEA + OPTIONAL:
        (d, p, q), nxt = nearest(ga, gb); key = tuple(sorted((p, q)))
        in_adj = bool(((adj.node_a == key[0]) & (adj.node_b == key[1]) & adj.adjacent).any())
        sea.append(dict(apg_no=no, project=label, node_a=key[0], node_b=key[1], great_circle_km=round(d, 1), next_pairs="; ".join(f"{x}-{y} {dd:.0f} km" for dd, x, y in nxt),
                        existing_components=";".join(joins.get(key, [])), covered_by_land_adjacency=in_adj, optional=no.startswith("other"),
                        action=("optional (other initiative, not in the main run)" if no.startswith("other") else
                                ("covered by the land-adjacency candidate" if in_adj else ("existing corridor" if joins.get(key) else "new candidate")))))
    sea = pd.DataFrame(sea)
    # 4. domestic APG projects
    dom = []
    for no, ga, gb, label in DOMESTIC:
        hits = [f"{t}:{k}" for (u, v), ks in joins.items() for t_k in ks for t, k in [t_k.split(":", 1)]
                if (u.startswith(ga) and v.startswith(gb)) or (u.startswith(gb) and v.startswith(ga))]
        (d, p, q), nxt = nearest(ga, gb); key = tuple(sorted((p, q)))
        dom.append(dict(apg_no=no, project=label, existing_components=";".join(sorted(set(hits))), node_a=key[0], node_b=key[1], great_circle_km=round(d, 1),
                        action=("existing domestic connection" if hits else "new domestic candidate")))
    dom = pd.DataFrame(dom)
    # 5. geometry: landmass, subsea share, type, length
    land_gdf = gpd.read_file(AUTHOR / "country_shapes.geojson"); off_gdf = gpd.read_file(AUTHOR / "offshore_shapes.geojson")
    land = land_gdf.union_all(); off = off_gdf.union_all(); shapely.prepare(land); shapely.prepare(off)
    polys = list(land.geoms); tree = shapely.STRtree(polys); geod = Geod(ellps="WGS84")

    def landmass(node):
        pt = shapely.Point(float(b.at[node, "x"]), float(b.at[node, "y"])); hit = tree.query(pt, predicate="intersects")
        if len(hit):
            return int(hit[0]), 0.0
        j = int(tree.nearest(pt)); return j, float(polys[j].distance(pt))
    new_pairs = [(r.node_a, r.node_b, "adjacency", "") for r in adj[adj.action == "new candidate"].itertuples()]
    new_pairs += [(r.node_a, r.node_b, "apg", r.apg_no) for r in sea[sea.action == "new candidate"].itertuples()]
    dom_pairs = [(r.node_a, r.node_b, "domestic", r.apg_no) for r in dom[dom.action == "new domestic candidate"].itertuples()]
    old_keys = {(r.loc0, r.loc1): i for i, r in sub.iterrows()}
    geo_rows, corr_rows, dom_rows = [], [], []
    for (p, q, kind, no) in new_pairs + dom_pairs:
        v = classify(geod, land, off, float(b.at[p, "x"]), float(b.at[p, "y"]), float(b.at[q, "x"]), float(b.at[q, "y"]))
        (l0, o0), (l1, o1) = landmass(p), landmass(q); same = l0 == l1
        share = 0.0 if same else v["subsea_share_not_land"]
        typ, car = ("Line", "AC") if same else ("Link", "DC")
        cp, cq = str(b.at[p, "country"]), str(b.at[q, "country"])
        name = (f"S4E1 {p} - {q}" if kind == "adjacency" else f"APG{no} {p} - {q} DC") if typ == "Link" or kind != "adjacency" else f"S4E1 {p} - {q}"
        if typ == "Link" and kind == "adjacency":
            name = f"S4E1 {p} - {q} DC"
        length = v["great_circle_km"] * LENGTH_FACTOR
        status = {"adjacency": "S4E1_ADJACENCY_CANDIDATE (decision 94): onshore regions share a border; capacity 0, extendable",
                  "apg": f"S4E1_APG_CROSS_SEA_CANDIDATE (decision 94): APG AIMS III #{no}; capacity 0, extendable",
                  "domestic": f"S4E1_DOMESTIC_CANDIDATE (decision 94 / 35): APG AIMS III #{no} national project; capacity 0, extendable"}[kind]
        row = {"from": p, "to": q, "carrier": car, "length_km": length, "subsea_share": share,
               "source": "S4E-1 (scripts_project/s4e_1_corridors.py): great-circle x 1.25; subsea share S4C supplement 01 rule", "component_type": typ, "component": name,
               "country_from": cp, "country_to": cq, "capacity_2025_mw": 0.0, "nominal_mw_in_base": 0.0, "nominal_minus_lower_bound_mw": 0.0, "status": status}
        (dom_rows if kind == "domestic" else corr_rows).append(row)
        key = tuple(sorted((p, q)))
        geo_rows.append(dict(loc0=key[0], loc1=key[1], country0=str(b.at[key[0], "country"]), country1=str(b.at[key[1], "country"]), cross_border=cp != cq, candidate=True, **v,
                             components=f"{typ}:{car}", n_components=1, names=name, check_expectation="", check_label=f"S4E-1 {kind} {no}".strip(),
                             landmass0=(l0 if key[0] == p else l1), landmass1=(l1 if key[0] == p else l0), offland_deg0=(o0 if key[0] == p else o1), offland_deg1=(o1 if key[0] == p else o0),
                             same_landmass=same, share_zero=0.0, share_geometric_all=v["subsea_share_not_land"], share_landmass_nonland=share,
                             main_rule=("same landmass -> 0 (overland route)" if same else "different landmass -> not-land share"), _type=typ, _kind=kind, _no=no))
    G = pd.DataFrame(geo_rows)
    gaps = G[(~G.same_landmass) & (G.gap_share > 0.05)]
    # subsea superset table: old rows unchanged; pairs already present (e.g. common-sense check pairs) become candidates
    S = sub.copy()
    for r in G.itertuples():
        k = (r.loc0, r.loc1)
        if k in old_keys:
            i = old_keys[k]; S.at[i, "candidate"] = True
            S.at[i, "components"] = (str(S.at[i, "components"]) + ";" if str(S.at[i, "components"]) not in ("", "nan") else "") + r.components
        else:
            S = pd.concat([S, pd.DataFrame([{c: getattr(r, c) for c in sub.columns}])], ignore_index=True)
    # corridor tables
    C = pd.concat([cor, pd.DataFrame(corr_rows)], ignore_index=True)
    D = pd.DataFrame(dom_rows)
    # 3. APG stock check
    stock = []
    for r in apg.itertuples():
        comps = [c for c, no in COMPONENT_TO_APG.items() if no == r.apg_no]
        model = float(cor[cor.component.astype(str).isin(comps)].capacity_2025_mw.sum()) if comps else 0.0
        ex = r.existing_MW.strip()
        try:
            exv = float(ex)
        except ValueError:
            exv = None
        diff = None if exv is None else model - exv
        if r.country_a == r.country_b:
            verdict = "national project (S4E-1 item 4)"
        elif exv is None and model < 5.0:
            verdict = "no APG stock; model stock negligible" if model > 0 else "no stock on either side"
        elif exv is None:
            verdict = "model stock without APG existing value"
        elif abs(diff) < 1.0:
            verdict = "consistent"
        else:
            verdict = "DIFFERENT - listed, verified stock not changed"
        stock.append(dict(apg_no=r.apg_no, connection=r.connection, country_a=r.country_a, country_b=r.country_b, apg_existing_mw=ex, model_2025_mw=round(model, 3),
                          model_components=";".join(comps), difference_mw=(None if diff is None else round(diff, 3)), verdict=verdict))
    stock = pd.DataFrame(stock)
    # 6. corridor graph and coalitions (cross-border rows of the new table)
    def edges_of(t):
        return {tuple(sorted((str(r.country_from), str(r.country_to)))) for r in t.itertuples() if str(r.country_from) != str(r.country_to)}
    # the gas stock (GEM) also joins ID-SG; the graph of the model = electricity corridors (pipelines follow them) + the existing gas pipelines
    gas_edges = {("ID", "SG")}
    e_old, e_new = edges_of(cor) | gas_edges, edges_of(C) | gas_edges
    linked = sorted({c for e in e_new for c in e}); isolated = sorted(set(COUNTRIES) - set(linked))
    cc_old = connected_coalitions(e_old, sorted(COUNTRIES)); cc_new = connected_coalitions(e_new, sorted(COUNTRIES))
    # one component?
    comp = {c: c for c in COUNTRIES}
    def find(c):
        while comp[c] != c:
            c = comp[c]
        return c
    for u, v in e_new:
        comp[find(u)] = find(v)
    components = sorted({find(c) for c in COUNTRIES})
    # write
    adj.to_csv(OUT / "ADJACENCY_S4E1.csv", index=False); sea.to_csv(OUT / "APG_CROSS_SEA_S4E1.csv", index=False); dom.to_csv(OUT / "APG_DOMESTIC_S4E1.csv", index=False)
    stock.to_csv(OUT / "APG_STOCK_CHECK_S4E1.csv", index=False)
    C.to_csv(OUT / "CORRIDORS_S4E1.csv", index=False); D.to_csv(OUT / "DOMESTIC_CORRIDORS_S4E1.csv", index=False)
    S.to_csv(OUT / "SUBSEA_SHARE_S4E1.csv", index=False); G.to_csv(OUT / "NEW_CORRIDOR_GEOMETRY_S4E1.csv", index=False)
    summ = dict(rule=dict(tolerance_m=TOL_M, min_shared_km=MIN_KM, length_factor=LENGTH_FACTOR, type="AC line if same landmass else DC link"),
                adjacency=dict(pairs=int(adj.adjacent.sum()), existing=int((adj.action == "existing corridor").sum()), new=int((adj.action == "new candidate").sum()),
                               unclear_below_1km=unclear[["node_a", "node_b", "shared_border_km"]].to_dict("records"),
                               min_shared_km=float(adj[adj.adjacent].shared_border_km.min()), by_country_pair_new={f"{k[0]}-{k[1]}": int(v) for k, v in adj[adj.action == "new candidate"].groupby(["country_a", "country_b"]).size().items()}),
                cross_sea=sea.to_dict("records"), domestic=dom.to_dict("records"),
                new_corridors=len(corr_rows), new_domestic=len(dom_rows), new_types=pd.DataFrame(corr_rows + dom_rows).groupby(["component_type"]).size().to_dict() if corr_rows + dom_rows else {},
                gap_pairs=gaps[["loc0", "loc1", "gap_share"]].to_dict("records"), stock_check=stock.to_dict("records"),
                graph=dict(edges_before=sorted("-".join(e) for e in e_old), edges_after=sorted("-".join(e) for e in e_new), isolated_after=isolated, components_after=components,
                           connected_coalitions_before=cc_old, connected_coalitions_after=cc_new),
                sources=dict(regions_onshore=sha256(REG_ON), corridors=sha256(CORR), subsea_s4c1=sha256(SUB), apg=sha256(APG), network=str(a.network)))
    (OUT / "CORRIDORS_S4E1.json").write_text(json.dumps(summ, indent=1, default=str))
    # registry fragment s4e_1
    reg = Registry(SCRIPT); ins = "work/p1_step4e_20261017/S4E_CLAUDE_CODE_INSTRUCTION.md"
    reg.add("s4e1_corridor_rules", "Decision 94 corridor completion rules: land adjacency = onshore regions of nodes of different countries share >= 1 km of border (1 km alignment "
            "tolerance); cross-sea = APG AIMS III priority projects #4, #7, #15, #16 (nearest node pair of the two areas; pairs already adjacent not repeated); other "
            "initiatives SG-VN / SG-KH optional only; candidates capacity 0, extendable; AC line when both node locations lie on one landmass, else DC link; length "
            "great-circle x 1.25; subsea share S4C supplement 01 rule; cost decision-50 cost layer; H2 / CO2 / gas candidates follow the topology (decision 59)",
            "rules", "flag", "B", "S4E instruction S4E-1", ins, INSTRUCTION_SHA, decision_ref="94,15,59,16,50", status="REFERENCE_ONLY")
    for f, desc in [("ADJACENCY_S4E1.csv", f"land adjacency table: {int(adj.adjacent.sum())} adjacent cross-border node pairs ({int((adj.action == 'existing corridor').sum())} existing, "
                                           f"{int((adj.action == 'new candidate').sum())} new), shared border km and basis per pair"),
                    ("CORRIDORS_S4E1.csv", f"corridor table with the S4E-1 candidates: {len(cor)} rows of cross_border_corridors.csv + {len(corr_rows)} new"),
                    ("DOMESTIC_CORRIDORS_S4E1.csv", f"{len(dom_rows)} domestic candidates (APG national projects without a domestic connection)"),
                    ("SUBSEA_SHARE_S4E1.csv", "subsea share table: SUBSEA_SHARE_S4C1.csv rows unchanged + the new node pairs (same method)"),
                    ("APG_STOCK_CHECK_S4E1.csv", "APG existing_MW vs the corridor table 2025 stock per project (differences listed, verified stock unchanged)")]:
        reg.add("s4e1_" + f.split(".")[0].lower(), "Decision 94: " + desc, "table", "flag", "B", "derived (scripts_project/s4e_1_corridors.py)", "research_inputs/corridors/" + f,
                sha256(OUT / f), decision_ref="94", status="REFERENCE_ONLY")
    reg.add("s4e1_corridor_graph", f"Corridor graph after S4E-1: edges {len(e_new)} (before {len(e_old)}), isolated {isolated or 'none'}, components {len(components)}; connected coalitions "
            f"with >= 2 members {cc_new['with_two_or_more']} (before {cc_old['with_two_or_more']})", cc_new["with_two_or_more"], "coalitions", "B", "derived", "research_inputs/corridors/CORRIDORS_S4E1.json",
            sha256(OUT / "CORRIDORS_S4E1.json"), decision_ref="94,91", status="REFERENCE_ONLY")
    reg.add("s4e1_adjacency_switch", "research.corridors.adjacency_completion values: on (main: corridor table CORRIDORS_S4E1.csv + domestic candidates DOMESTIC_CORRIDORS_S4E1.csv) | "
            "off (cross_border_corridors.csv, comparison); the disconnected scenario closes every cross-border network component as before", "on|off", "flag", "B", "S4E instruction S4E-1 item 7",
            "configs/research/baseline.yaml", INSTRUCTION_SHA, decision_ref="94", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4e_1.csv")
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 70)
    print(adj[["node_a", "node_b", "shared_border_km", "action"]].to_string())
    print(sea.to_string()); print(dom.to_string())
    print(pd.DataFrame(corr_rows + dom_rows)[["from", "to", "component_type", "component", "length_km", "subsea_share"]].to_string())
    print(stock.to_string())
    print(json.dumps({k: summ[k] for k in ("adjacency", "new_corridors", "new_domestic", "new_types", "gap_pairs", "graph")}, indent=1, default=str))


if __name__ == "__main__":
    main()
