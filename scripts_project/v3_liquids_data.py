"""V3 (decision 161; D161-1 a, D161-3 a, D161-9 a): national liquid hub nodes and port-to-port sea distances.

    PYTHONHASHSEED=0 python scripts_project/v3_liquids_data.py --network <v2 integrated_2920_3h_unsolved.nc>

Hub = port node by the WPI size rule of PORTS_ASEAN_TO_NODES_S4D1.csv (Large 3, Medium 2, Small 1), with the two reviewed corrections: ID ties between
ID_Java-Bali1 0 and ID_Papua18 0 (Sorong crude terminals) -> ID_Java-Bali1 0, MM -> MM2 1 (Yangon). LA is landlocked: hub = its node with the largest load,
rail transit to the Vietnamese coast (decision 93). Sea distance: the 0.05 degree over-water grid of s4d_2_ship_routes.py (same land mask, same moves).
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra

from d1_common import ROOT, sha256
from s4d_2_ship_routes import MARGIN, MOVES, RES, hav

SCRIPT = "scripts_project/v3_liquids_data.py"
OUT = ROOT / "research_inputs/liquids_v3"
WEIGHT = {"Large": 3.0, "Medium": 2.0, "Small": 1.0}
HUB_OVERRIDE = {"ID": ("ID_Java-Bali1 0", "tie with ID_Papua18 0 (Sorong crude terminals) resolved to the larger load; review D161-1"),
                "MM": ("MM2 1", "rule gives MM2 4 (Mergui, Moulmein, small ports); Yangon is the main port; review D161-1")}


def grid(land_path: Path):
    land = gpd.read_file(land_path).to_crs("EPSG:4326")
    x0, y0, x1, y1 = land.total_bounds
    x0, y0, x1, y1 = np.floor(x0 - MARGIN), np.floor(y0 - MARGIN), np.ceil(x1 + MARGIN), np.ceil(y1 + MARGIN)
    W, H = int(round((x1 - x0) / RES)), int(round((y1 - y0) / RES))
    tr = from_origin(x0, y1, RES, RES)
    is_land = features.rasterize(((g, 1) for g in land.geometry), out_shape=(H, W), transform=tr, fill=0, all_touched=False).astype(bool)
    lab, _ = ndimage.label(~is_land, structure=np.ones((3, 3)))
    ocean = lab == np.bincount(lab.ravel())[1:].argmax() + 1
    lon = x0 + (np.arange(W) + 0.5) * RES; lat = y1 - (np.arange(H) + 0.5) * RES
    idx = -np.ones((H, W), dtype=np.int64); idx[ocean] = np.arange(int(ocean.sum()))
    src, dst, wgt = [], [], []
    for dr, dc in MOVES:
        r0 = np.arange(max(0, -dr), H - max(0, dr)); c0 = np.arange(max(0, -dc), W - max(0, dc))
        R, Cc = np.meshgrid(r0, c0, indexing="ij"); R2, C2 = R + dr, Cc + dc
        ok = ocean[R, Cc] & ocean[R2, C2]
        if abs(dr) + abs(dc) == 3:
            ok &= ocean[R + np.sign(dr) * (abs(dr) == 2), Cc + np.sign(dc) * (abs(dc) == 2)] & ocean[R + np.sign(dr) * (abs(dr) == 1), Cc + np.sign(dc) * (abs(dc) == 1)]
        R, Cc, R2, C2 = R[ok], Cc[ok], R2[ok], C2[ok]
        src.append(idx[R, Cc]); dst.append(idx[R2, C2]); wgt.append(hav(lon[Cc], lat[R], lon[C2], lat[R2]))
    src, dst, wgt = np.concatenate(src), np.concatenate(dst), np.concatenate(wgt)
    N = int(ocean.sum())
    G = coo_matrix((np.concatenate([wgt, wgt]), (np.concatenate([src, dst]), np.concatenate([dst, src]))), shape=(N, N)).tocsr()
    orr, occ = np.nonzero(ocean)
    return G, lon, lat, orr, occ


def hubs(network: Path) -> pd.DataFrame:
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network))
    p = pd.read_csv(ROOT / "research_inputs/co2_v5/PORTS_ASEAN_TO_NODES_S4D1.csv")
    p["w"] = p.harbor_size.map(WEIGHT).fillna(0.5)
    load = n.get_switchable_as_dense("Load", "p_set")[list(n.loads.index[n.loads.account == "Astar"])].sum()
    by_bus = load.groupby(n.loads.bus.reindex(load.index)).sum()
    rows = []
    for c, g in p.groupby("country"):
        t = g.groupby("node").agg(w=("w", "sum"), ports=("port", lambda s: ";".join(sorted(s)))).sort_values("w", ascending=False)
        nd, note = t.index[0], "largest WPI size weight"
        if c in HUB_OVERRIDE:
            nd, note = HUB_OVERRIDE[c]
        rows.append(dict(country=c, hub_node=nd, x=float(n.buses.at[nd, "x"]), y=float(n.buses.at[nd, "y"]), wpi_weight=float(t.w.get(nd, 0.0)), ports=str(t.ports.get(nd, "")), rule=note))
    la = n.buses[(n.buses.country == "LA") & (n.buses.carrier == "AC")]
    nd = by_bus.reindex(la.index).fillna(0.0).idxmax()
    rows.append(dict(country="LA", hub_node=nd, x=float(n.buses.at[nd, "x"]), y=float(n.buses.at[nd, "y"]), wpi_weight=0.0, ports="", rule="landlocked: node with the largest base load, rail transit to the Vietnamese coast (decision 93)"))
    return pd.DataFrame(rows).sort_values("country")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--land", type=Path, required=True, help="author country_shapes.geojson (s4d_1_coastline.LAND)"); a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    h = hubs(a.network); h.to_csv(OUT / "LIQUID_HUB_NODES_V3.csv", index=False)
    G, lon, lat, orr, occ = grid(a.land)
    sea = h[h.country != "LA"].reset_index(drop=True)
    idx = []
    for _, z in sea.iterrows():
        d = hav(z.x, z.y, lon[occ], lat[orr]); idx.append(int(np.argmin(d)))
    D = dijkstra(G, directed=False, indices=idx)
    rows = []
    for i, zi in sea.iterrows():
        for j, zj in sea.iterrows():
            if zi.country != zj.country:
                rows.append(dict(origin=zi.country, destination=zj.country, origin_node=zi.hub_node, destination_node=zj.hub_node, sea_km=round(float(D[i, idx[j]]), 1), gc_km=round(float(hav(zi.x, zi.y, zj.x, zj.y)), 1)))
    r = pd.DataFrame(rows); r.to_csv(OUT / "LIQUID_SHIP_ROUTES_V3.csv", index=False)
    if not np.isfinite(r.sea_km).all():
        raise ValueError("unreachable hub pair")
    t = pd.read_csv(ROOT / "research_inputs/co2_v5/LAO_TRANSIT_S4D1.csv").set_index("node"); la = h[h.country == "LA"].hub_node.iloc[0]
    tr = dict(hub=la, route_km=float(t.at[la, "route_km"]), coastal_node=str(t.at[la, "coastal_node_at_point"]))
    (OUT / "LIQUID_ROUTES_V3_EVIDENCE.json").write_text(json.dumps(dict(script=SCRIPT, grid_deg=RES, pairs=int(len(r)), la_transit=tr, land_sha256=sha256(a.land), hubs=h.to_dict("records"), sea_km_quantiles={q: float(r.sea_km.quantile(q)) for q in (0, 0.5, 1)}), indent=1, sort_keys=True) + "\n")
    print(h[["country", "hub_node", "wpi_weight", "rule"]].to_string())
    print(r[(r.origin == "ID")][["destination", "sea_km", "gc_km"]].to_string()); print(tr, r.sea_km.describe().round(0).to_dict())


if __name__ == "__main__":
    main()
