"""S4C-1 item 2 (decision 82): offshore-wind connection distances per node x resource class for the cost-layer connection cost.

Neither the frozen electric base (it only stores the total author capital cost) nor the profile files (author tutorial files are a
different 961-bus network; the S4A rebuilt files hold no distance) carry an average distance for the research nodes, so the distance
is computed here with the PyPSA-Eur v2025.07.0 formula on the same layout as the S4A / S4B profiles in use (pypsa_eur offshore spec,
3 resource classes, research_inputs/renewable_v5/S4A_PROFILE_CLASSES_c3.csv):

  PyPSA-Eur v2025.07.0 scripts/build_renewable_profiles.py lines 157-162 (offshore: distance to the shoreline = the node's onshore region)
  and 287-304 (average_distance per bus x bin = layout-weighted distance of the cells); scripts/add_electricity.py lines 541, 555-562,
  566-576: connection_cost = line_length_factor x (average_distance x <car>-connection-submarine + landfall_length x
  <car>-connection-underground); capital_cost = offwind + <car>-station + connection_cost; landfall_length offwind-ac 20 km,
  offwind-dc 30 km, line_length_factor 1.25 (config.default.yaml lines 219, 238, 325). [read-only view of the GitHub v2025.07.0 files,
  2026-10-16; SHA256 add_electricity.py c93974a1..., build_renewable_profiles.py 12fe6776...]

Distances: cell centre (cutout grid) to the node onshore region polygon (S4A regions_onshore.geojson), in a local azimuthal equidistant
projection centred on the node (EPSG:3035 of PyPSA-Eur is a European projection); weights = class cell potential x cell capacity factor.

Validation against the author network (INFERENCE check of the method): the PyPSA-Earth formula of the author chain (scripts/add_electricity.py
lines 549-567: line_length_factor x average_distance_to_bus x (uw x submarine + (1 - uw) x underground), underwater fraction of the
centre-of-mass -> bus line in the author offshore shape, build_renewable_profiles.py lines 791-836) with the author cost file
(pypsa-asean resources/baseline-aims-3H-tutorial/costs_2050.csv, prepared with fill values lifetime 25, FOM 0, discount rate 0.07) and
the fork offshore spec on one class per node must reproduce the electric-base offwind capital costs.

    python scripts_project/s4c_1_offwind_distance.py --output research_inputs/renewable_v5
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import atlite
import geopandas as gpd
import numpy as np
import pandas as pd
import pypsa
from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point
from shapely.ops import transform

from s4a_profiles import AUTHOR, CUTOUT, NODES, VARIANTS, author_potential, convert

ROOT = Path(__file__).resolve().parents[1]
EB = ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
AUTHOR_COSTS = AUTHOR / "costs_2050.csv"
LANDFALL_KM = {"offwind-ac": 20.0, "offwind-dc": 30.0}   # PyPSA-Eur v2025.07.0 config.default.yaml lines 219, 238
LINE_LENGTH_FACTOR = 1.25   # PyPSA-Eur config.default.yaml line 325; pypsa-asean config.default.yaml line 295 (author chain)


def haversine_km(lon0, lat0, lon, lat):
    la0, lo0, la, lo = map(np.radians, [lat0, lon0, lat, lon])
    h = np.sin((la - la0) / 2) ** 2 + np.cos(la0) * np.cos(la) * np.sin((lo - lo0) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(h))


def author_fixed(tech: str) -> float:
    c = pd.read_csv(AUTHOR_COSTS)
    w = c.pivot_table(index="technology", columns="parameter", values="value", aggfunc="first").loc[tech]
    life = float(w.get("lifetime")) if pd.notna(w.get("lifetime")) else 25.0
    fom = float(w.get("FOM")) if pd.notna(w.get("FOM")) else 0.0
    dr = float(w.get("discount rate")) if pd.notna(w.get("discount rate")) else 0.07
    ann = dr / (1.0 - 1.0 / (1.0 + dr) ** life)
    return (ann + fom / 100.0) * float(w["investment"]) * 1e3   # EUR/kW -> EUR/MW (author prepare_costs)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    t0 = time.time(); log = dict(method=__doc__.split("\n\n")[1].strip(), timings={})
    cutout = atlite.Cutout(str(CUTOUT))
    nodes = pd.read_csv(NODES, index_col=0)
    on_reg = gpd.read_file(ROOT / "research_inputs/renewable_v5/regions_onshore.geojson").set_index("node")
    off_reg = gpd.read_file(ROOT / "research_inputs/renewable_v5/regions_offshore.geojson").set_index("node")
    offshore_union = gpd.read_file(AUTHOR / "shapes/offshore_shapes.geojson").union_all()
    cls = pd.read_csv(ROOT / "research_inputs/renewable_v5/S4A_PROFILE_CLASSES_c3.csv")
    xs, ys = np.meshgrid(cutout.data.x.values, cutout.data.y.values)
    I = cutout.indicatormatrix(off_reg.geometry)
    I_arr = I.toarray().reshape(len(off_reg), len(cutout.data.y), len(cutout.data.x))
    cov = I_arr.sum(axis=0)
    rows, val = [], []
    cf_by_var = {}
    for var in ["pypsa_eur", "fork"]:
        spec = dict(VARIANTS[var]["offwind-ac"])   # identical specs for offwind-ac and offwind-dc
        corr, cf_cell = convert(cutout, spec, capacity_factor=True)
        cf_by_var[var] = (corr * cf_cell).fillna(0.0).load().values.astype(np.float64)
        log["timings"][f"cf_{var}"] = round(time.time() - t0, 1)
    for tech in ["offwind-ac", "offwind-dc"]:
        pot = author_potential(tech, cutout)
        pot_eff = np.where(cov > 0, pot.values / np.maximum(cov, 1e-12), 0.0)
        c3 = cls[(cls.tech == tech) & (cls.variant == "pypsa_eur")]
        for b, node in enumerate(off_reg.index):
            w = I_arr[b] * pot_eff
            if w.sum() <= 0:
                continue
            lon0, lat0 = float(nodes.at[node, "x"]), float(nodes.at[node, "y"])
            aeqd = CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m")
            fwd = Transformer.from_crs("EPSG:4326", aeqd, always_xy=True).transform
            shore = transform(fwd, on_reg.loc[node, "geometry"]) if node in on_reg.index else None
            sel = w > 0
            px, py = fwd(xs[sel], ys[sel])
            dist_shore = np.array([shore.distance(Point(x, y)) / 1e3 for x, y in zip(px, py)]) if shore is not None else np.full(sel.sum(), np.nan)
            cf = cf_by_var["pypsa_eur"]
            # classes exactly as S4A (linear bins between the node cf_min and cf_max of the pypsa_eur offshore spec)
            cfv = cf[sel]; cmin, cmax = float(cfv.min()), float(cfv.max()); edges = cmin + (cmax - cmin) * np.linspace(0, 1, 4)
            for k in range(3):
                m = (cfv >= edges[k]) & ((cfv < edges[k + 1]) if k < 2 else (cfv <= cmax))
                if not m.any():
                    continue
                lw = w[sel][m] * cfv[m]
                ref = c3[(c3.node == node) & (c3.cls == k)]
                pot_k = float(w[sel][m].sum())
                rows.append(dict(tech=tech, node=node, country=nodes.at[node, "country"], cls=k, generator_key=f"{node}|{k}", cells=int(m.sum()), potential_mw=pot_k,
                                 potential_mw_s4a=(float(ref.potential_mw.iloc[0]) if len(ref) else np.nan),
                                 average_distance_km=float((dist_shore[m] * lw).sum() / lw.sum()), landfall_km=LANDFALL_KM[tech], line_length_factor=LINE_LENGTH_FACTOR,
                                 onshore_region=node in on_reg.index, distance_basis="PyPSA-Eur v2025.07.0: cell centre -> node onshore region (shoreline), layout-weighted"))
            # validation: author PyPSA-Earth formula, fork spec, one class per node
            cff = cf_by_var["fork"][sel]; lw = w[sel] * cff
            if lw.sum() > 0:
                d_bus = haversine_km(lon0, lat0, xs[sel], ys[sel])
                com = (float((xs[sel] * lw).sum() / lw.sum()), float((ys[sel] * lw).sum() / lw.sum()))
                line = LineString([com, (lon0, lat0)])
                uw = float(line.intersection(offshore_union).length / line.length) if line.length > 0 else 0.0
                val.append(dict(tech=tech, node=node, average_distance_to_bus_km=float((d_bus * lw).sum() / lw.sum()), underwater_fraction=uw))
        log["timings"][tech] = round(time.time() - t0, 1)
    d = pd.DataFrame(rows)
    d["basis"] = "LAYOUT"
    # nodes whose electric-base offshore generator has no S4A layout cell (S4A kept the author profile: research_renewable.untouched) get the
    # potential-weighted mean distance of the same country and technology (grade C proxy; ASEAN mean when the country has no layout row)
    eb = pypsa.Network(str(EB)); g = eb.generators[eb.generators.p_nom_extendable]
    proxy = []
    for tech in ["offwind-ac", "offwind-dc"]:
        have = set(zip(d.loc[d.tech == tech, "node"], d.loc[d.tech == tech, "cls"]))
        for name, z in g[g.carrier == tech].iterrows():   # electric-base generators are class 0
            node = str(z.bus)
            if (node, 0) in have:
                continue
            c = str(nodes.at[node, "country"]) if node in nodes.index else str(eb.buses.at[node, "country"])   # DC converter nodes are not in the S4A AC node table
            pool = d[(d.tech == tech) & (d.node == node)]; scope = "node"
            if pool.empty:
                pool = d[(d.tech == tech) & (d.country == c)]; scope = "country"
            if pool.empty:
                pool = d[d.tech == tech]; scope = "ASEAN"
            avg = float((pool.average_distance_km * pool.potential_mw).sum() / pool.potential_mw.sum())
            proxy.append(dict(tech=tech, node=node, country=c, cls=0, generator_key=f"{node}|0", cells=0, potential_mw=float(z.p_nom_max) if np.isfinite(z.p_nom_max) else np.nan,
                              potential_mw_s4a=np.nan, average_distance_km=avg, landfall_km=LANDFALL_KM[tech], line_length_factor=LINE_LENGTH_FACTOR, onshore_region=node in on_reg.index,
                              distance_basis=f"PROXY (grade C): no S4A layout cell at this node (author profile kept by S4A); potential-weighted mean distance of {scope} {tech} layout rows",
                              basis=f"PROXY_{scope.upper()}_MEAN"))
    if proxy:
        d = pd.concat([d, pd.DataFrame(proxy)], ignore_index=True)
    log["proxy_rows"] = proxy
    # author cost reproduction
    v = pd.DataFrame(val)
    out = []
    for tech in ["offwind-ac", "offwind-dc"]:
        base = author_fixed("offwind") + author_fixed(f"{tech}-station")
        sub, und = author_fixed(f"{tech}-connection-submarine") / 1e3, author_fixed(f"{tech}-connection-underground") / 1e3   # per km: author rows are EUR/MW/km (no x1e3)
        cc = g[g.carrier == tech].groupby("bus").capital_cost.first()
        for r in v[v.tech == tech].itertuples():
            pred = base + LINE_LENGTH_FACTOR * r.average_distance_to_bus_km * (r.underwater_fraction * sub + (1 - r.underwater_fraction) * und)
            out.append(dict(tech=tech, node=r.node, average_distance_to_bus_km=r.average_distance_to_bus_km, underwater_fraction=r.underwater_fraction, author_capital_cost_predicted=pred,
                            electric_base_capital_cost=float(cc.get(r.node, np.nan)), author_fixed_offwind_plus_station=base, author_submarine_per_km=sub, author_underground_per_km=und))
    o = pd.DataFrame(out); o["rel_diff"] = o.author_capital_cost_predicted / o.electric_base_capital_cost - 1.0
    o["connection_author_base"] = o.electric_base_capital_cost - o.author_fixed_offwind_plus_station
    o["connection_predicted"] = o.author_capital_cost_predicted - o.author_fixed_offwind_plus_station
    a.output.mkdir(parents=True, exist_ok=True)
    d.to_csv(a.output / "OFFWIND_CONNECTION_DISTANCE_S4C1.csv", index=False)
    o.to_csv(a.output / "OFFWIND_DISTANCE_VALIDATION_AUTHOR_S4C1.csv", index=False)
    ok = o.dropna(subset=["electric_base_capital_cost"])
    summ = {t: dict(nodes=int(len(x)), median_abs_rel_diff=float(x.rel_diff.abs().median()), p90_abs_rel_diff=float(x.rel_diff.abs().quantile(0.9)), max_abs_rel_diff=float(x.rel_diff.abs().max()),
                    corr_connection=float(np.corrcoef(x.connection_author_base, x.connection_predicted)[0, 1]) if len(x) > 2 else None)
            for t, x in ok.groupby("tech")}
    lay = d[d.basis == "LAYOUT"]
    log.update(validation=summ, rows=len(d), layout_rows=int(len(lay)), proxy_rows_n=int(len(d) - len(lay)), potential_check=dict(max_abs_rel=float((lay.potential_mw / lay.potential_mw_s4a - 1).abs().max())),
               distance_summary={t: x.average_distance_km.describe().round(2).to_dict() for t, x in lay.groupby("tech")}, seconds=round(time.time() - t0, 1))
    (a.output / "OFFWIND_DISTANCE_S4C1_LOG.json").write_text(json.dumps(log, indent=1, default=str) + "\n")
    print(json.dumps(dict(validation=summ, potential_check=log["potential_check"], distance=log["distance_summary"], seconds=log["seconds"]), indent=1))


if __name__ == "__main__":
    main()
