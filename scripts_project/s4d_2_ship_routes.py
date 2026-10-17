"""S4D-2 (decision 92): sea-route distances between coastal nodes and the shipping route factor.

The instruction prices intra-ASEAN CO2 shipping by port-to-port distance = great-circle distance between coastal nodes x a route factor
(value and source stated, grade C, +-25 %). No published route factor is at hand and the S4D download category does not cover one, so the
factor is derived here from the model geometry: shortest over-water paths on a 0.05 degree grid of the bounding box minus the ASEAN land of
the author country shapes (16-neighbour moves, haversine step lengths, ocean = the largest connected water component; every candidate pair
lies between ASEAN coasts, so foreign land missing from the shapes - PNG, Hainan, Australia - is never on a sensible route). Candidate pairs
are the ones the model builds: every coastal buffered node i (research_inputs/co2_v5/COASTAL_NODES_S4D1_FINAL.csv) to each other country j with
a national injection cap > 0, landing at the coastal node of j with the shortest sea path from i (the nearest node by great-circle can lie
across a peninsula: e.g. MM2 4 -> TH2 3 on the Gulf of Thailand, 3,441 km by sea round the Malay peninsula; reported for reference). Factor =
median over the candidate pairs of sea path / great-circle distance between the snapped water cells. Grid bias: the same ratio for pairs
whose straight line lies entirely over water.

    python scripts_project/s4d_2_ship_routes.py --network <S4D-1 integrated build>
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
from shapely.geometry import LineString

import s4d_1_coastline as C
from d1_common import ROOT, sha256

OUT = ROOT / "research_inputs" / "co2_v5"
RES = 0.05
MARGIN = 2.0
MOVES = [(0, 1), (1, 0), (1, 1), (1, -1), (1, 2), (2, 1), (2, -1), (1, -2)]   # half of the 16-neighbourhood; edges are undirected


def hav(lon0, lat0, lon1, lat1):
    p0, p1 = np.radians(lat0), np.radians(lat1); dl = np.radians(lon1 - lon0)
    a = np.sin((p1 - p0) / 2) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def candidate_nodes(network: Path, coastal: pd.DataFrame):
    import pypsa
    logging.disable(logging.WARNING)
    n = pypsa.Network(str(network))
    caps = n.meta["research_co2_storage"]["caps_t_per_year"]
    receivers = sorted(c for c, v in caps.items() if float(v) > 0)
    co = coastal[coastal.coastal].copy()
    co["x"] = n.buses.x.reindex(co.node).to_numpy(); co["y"] = n.buses.y.reindex(co.node).to_numpy()
    return co[co.co2_buffer], co[co.country.isin(receivers)], receivers


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    coastal = pd.read_csv(OUT / "COASTAL_NODES_S4D1_FINAL.csv")
    origins_df, landings_df, receivers = candidate_nodes(a.network, coastal)
    land = gpd.read_file(C.LAND).to_crs("EPSG:4326")
    x0, y0, x1, y1 = land.total_bounds
    x0, y0, x1, y1 = np.floor(x0 - MARGIN), np.floor(y0 - MARGIN), np.ceil(x1 + MARGIN), np.ceil(y1 + MARGIN)
    W, H = int(round((x1 - x0) / RES)), int(round((y1 - y0) / RES))
    tr = from_origin(x0, y1, RES, RES)
    is_land = features.rasterize(((g, 1) for g in land.geometry), out_shape=(H, W), transform=tr, fill=0, all_touched=False).astype(bool)
    lab, nlab = ndimage.label(~is_land, structure=np.ones((3, 3)))
    ocean = lab == np.bincount(lab.ravel())[1:].argmax() + 1
    lon = x0 + (np.arange(W) + 0.5) * RES; lat = y1 - (np.arange(H) + 0.5) * RES
    idx = -np.ones((H, W), dtype=np.int64); idx[ocean] = np.arange(int(ocean.sum()))
    src, dst, wgt = [], [], []
    for dr, dc in MOVES:
        r0 = np.arange(max(0, -dr), H - max(0, dr)); c0 = np.arange(max(0, -dc), W - max(0, dc))
        R, Cc = np.meshgrid(r0, c0, indexing="ij"); R2, C2 = R + dr, Cc + dc
        ok = ocean[R, Cc] & ocean[R2, C2]
        if abs(dr) + abs(dc) == 3:   # knight move: both cells it passes beside must be water (no corner cutting through land)
            ok &= ocean[R + np.sign(dr) * (abs(dr) == 2), Cc + np.sign(dc) * (abs(dc) == 2)] & ocean[R + np.sign(dr) * (abs(dr) == 1), Cc + np.sign(dc) * (abs(dc) == 1)]
        R, Cc, R2, C2 = R[ok], Cc[ok], R2[ok], C2[ok]
        src.append(idx[R, Cc]); dst.append(idx[R2, C2]); wgt.append(hav(lon[Cc], lat[R], lon[C2], lat[R2]))
    src, dst, wgt = np.concatenate(src), np.concatenate(dst), np.concatenate(wgt)
    N = int(ocean.sum())
    G = coo_matrix((np.concatenate([wgt, wgt]), (np.concatenate([src, dst]), np.concatenate([dst, src]))), shape=(N, N)).tocsr()
    orr, occ = np.nonzero(ocean)

    def snap(x, y):
        d = hav(x, y, lon[occ], lat[orr]); k = int(np.argmin(d))
        return k, float(d[k])

    snaps = {}
    for nm, x, y in list(zip(origins_df.node, origins_df.x, origins_df.y)) + list(zip(landings_df.node, landings_df.x, landings_df.y)):
        if nm not in snaps:
            snaps[nm] = snap(x, y)
    origins = list(origins_df.node)
    D = dijkstra(G, directed=False, indices=[snaps[o][0] for o in origins])
    land_u = land.union_all()
    rows = []
    for i, o in origins_df.reset_index(drop=True).iterrows():
        k0, s0 = snaps[o.node]
        for j in receivers:
            if j == o.country:
                continue
            cand = landings_df[landings_df.country == j]
            sea_d = np.array([D[i, snaps[x][0]] for x in cand.node]); m = int(np.argmin(sea_d)); L = cand.iloc[m]
            g_d = hav(o.x, o.y, cand.x.to_numpy(), cand.y.to_numpy()); g = int(np.argmin(g_d))
            k1, s1 = snaps[L.node]
            gcs = float(hav(lon[occ[k0]], lat[orr[k0]], lon[occ[k1]], lat[orr[k1]]))
            rows.append(dict(origin=o.node, origin_country=o.country, receiver=j, landing=L.node, gc_km=round(float(g_d[m]), 1), snap_origin_km=round(s0, 1),
                             snap_landing_km=round(s1, 1), sea_km=round(float(sea_d[m]), 1), gc_snapped_km=round(gcs, 1), ratio=round(float(sea_d[m]) / max(gcs, 1e-9), 4),
                             straight_over_water=not LineString([(lon[occ[k0]], lat[orr[k0]]), (lon[occ[k1]], lat[orr[k1]])]).intersects(land_u),
                             landing_nearest_gc=cand.node.iloc[g], sea_km_nearest_gc=round(float(sea_d[g]), 1)))
    pairs = pd.DataFrame(rows)
    valid = pairs[(pairs.gc_snapped_km >= 50.0) & np.isfinite(pairs.sea_km)]
    factor = float(valid.ratio.median())
    bias = float(valid[valid.straight_over_water].ratio.median()) if valid.straight_over_water.any() else float("nan")
    pairs.to_csv(OUT / "CO2_SHIP_ROUTES_S4D2.csv", index=False)
    summ = dict(grid_deg=RES, bbox=[x0, y0, x1, y1], ocean_cells=N, receivers=receivers, pairs=int(len(pairs)), pairs_used=int(len(valid)), min_gc_km_for_factor=50.0,
                route_factor_median=round(factor, 4), quantiles={q: round(float(valid.ratio.quantile(q)), 4) for q in (0.1, 0.25, 0.5, 0.75, 0.9)},
                grid_bias_straight_pairs=dict(n=int(valid.straight_over_water.sum()), median_ratio=round(bias, 4)),
                largest_ratios=valid.sort_values("ratio", ascending=False).head(8)[["origin", "receiver", "landing", "gc_snapped_km", "sea_km", "ratio"]].to_dict("records"),
                sources=dict(land=dict(path=str(C.LAND), sha256=sha256(C.LAND)), coastal_table_sha256=sha256(OUT / "COASTAL_NODES_S4D1_FINAL.csv"), network=str(a.network)))
    (OUT / "CO2_SHIP_ROUTES_S4D2.json").write_text(json.dumps(summ, indent=1, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "sources"}, indent=1, default=str))
    print(pairs.groupby(["origin_country", "receiver"]).agg(n=("ratio", "size"), gc=("gc_km", "median"), sea=("sea_km", "median"), ratio=("ratio", "median")).round(2).to_string())


if __name__ == "__main__":
    main()
