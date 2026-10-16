"""S4A-1 (L14, decisions 70-73): rebuild the wind / solar availability profiles of the research nodes from the ASEAN ERA5 2013
cutout (PyPSA-Earth Weather Databundle of ASEAN v1, Zenodo 10.5281/zenodo.20325289; identical grid and values to the author
tutorial cutout) with atlite 0.4.1, for two configuration variants and an optional resource-class split.

Method (follows PyPSA-Earth scripts/build_renewable_profiles.py lines 763-782 and PyPSA-Eur v2025.07.0 build_renewable_profiles.py):
  * node regions: per country, Voronoi cells of the research AC nodes clipped to the author country shape (onshore) or offshore
    shape (offshore) - the research network only stores node coordinates, the author 100-cluster regions are not in the cache;
  * exclusions / potential: the author layout `potential` (MW per cutout cell after natura / Copernicus / depth / shore rules)
    from resources/baseline-aims-3H-tutorial/renewable_profiles/profile_{tech}.nc is reused unchanged (time-invariant);
  * cell weights: I[b,c] x potential_c / sum_b I[b,c] (coverage-normalised; equals the author availability matrix when availability is uniform inside a cell);
  * per-cell capacity factor cf_c = correction_factor x atlite conversion (wind: log-law extrapolation to hub height + power
    curve; pv: Huld model, CSi, latitude-optimal tilt); layout = potential x cf_c (PyPSA-Earth: capacity placed proportional
    to the cell capacity factor); profile_b(t) = sum_c I[b,c] layout_c cf_c(t) / sum_c I[b,c] layout_c;
  * resource classes (PyPSA-Eur `resource_classes`): per node, cells binned linearly between the node cf_min and cf_max;
    class potential = sum of potential over the class cells; the node p_nom_max of the electric base is split by these shares.
Variants: fork (= pypsa-asean config.default.yaml renewable block as recorded in the author network meta) and pypsa_eur
(PyPSA-Eur v2025.07.0 config.default.yaml renewable defaults; solar tilt kept latitude-optimal, see report).

    python scripts_project/s4a_profiles.py --variant fork pypsa_eur --classes 1 --months 1 --output results_project/s4a/profiles_test
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
import xarray as xr
from shapely.geometry import MultiPoint, box
from shapely.ops import voronoi_diagram

ROOT = Path(__file__).resolve().parents[1]
CUTOUT = ROOT / "cutouts/asean_zenodo_20325289/cutout-2013-era5.nc"
AUTHOR = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial")
NODES = ROOT / "results_project/s4a/analysis/AC_NODES_XY.csv"
TECHS = {"onwind": "onshore", "offwind-ac": "offshore", "offwind-dc": "offshore", "solar": "onshore"}
# fork = author network meta['renewable'] (pypsa-asean config.default.yaml lines 339-425); pypsa_eur = PyPSA-Eur v2025.07.0 config.default.yaml lines 179-275
VARIANTS = {
    "fork": {
        "onwind": dict(method="wind", turbine="Vestas_V112_3MW", correction_factor=1.0, add_cutout_windspeed=False),
        "offwind-ac": dict(method="wind", turbine="NREL_ReferenceTurbine_5MW_offshore", correction_factor=1.0, add_cutout_windspeed=False),
        "offwind-dc": dict(method="wind", turbine="NREL_ReferenceTurbine_5MW_offshore", correction_factor=1.0, add_cutout_windspeed=False),
        "solar": dict(method="pv", panel="CSi", orientation="latitude_optimal", correction_factor=0.854337),
    },
    "pypsa_eur": {
        "onwind": dict(method="wind", turbine="Vestas_V112_3MW", correction_factor=1.0, add_cutout_windspeed=True),
        "offwind-ac": dict(method="wind", turbine="NREL_ReferenceTurbine_2020ATB_5.5MW", correction_factor=0.8855, add_cutout_windspeed=True),
        "offwind-dc": dict(method="wind", turbine="NREL_ReferenceTurbine_2020ATB_5.5MW", correction_factor=0.8855, add_cutout_windspeed=True),
        "solar": dict(method="pv", panel="CSi", orientation="latitude_optimal", correction_factor=1.0),
    },
    # S4B-3 (decisions 74, 75): onshore wind = ERA5 100 m wind speed scaled by the country calibration factor alpha (WIND_CALIBRATION_ALPHA.csv,
    # scripts_project/s4b_3_wind_calibration.py) + the DEA 2050 turbine (technology-data v0.15.0 onwind: 6 MW, 165 m, hub 110 m); offshore wind and solar
    # are the pypsa_eur specs (the export takes them from the pypsa_eur run, identical inputs)
    "calibrated_modern": {
        "onwind": dict(method="wind", turbine="DEA2050", correction_factor=1.0, add_cutout_windspeed=True, alpha="alpha_main"),
    },
    # S4B-3 cross-check only (no network variant): alpha = GWA 3.3 country mean 100 m speed / ERA5 2013 land mean; annual CF per class only
    "gwa_check": {
        "onwind": dict(method="wind", turbine="DEA2050", correction_factor=1.0, add_cutout_windspeed=True, alpha="alpha_gwa_check", cf_only=True),
    },
}


def node_regions(nodes: pd.DataFrame, shapes: gpd.GeoDataFrame, kind: str) -> gpd.GeoDataFrame:
    """Per-country Voronoi partition of the node coordinates, clipped to the country onshore / offshore shape."""
    out = []
    for c, g in nodes.groupby("country"):
        if c not in shapes.index:
            continue
        shape = shapes.loc[c, "geometry"]
        pts = MultiPoint([(float(r.x), float(r.y)) for r in g.itertuples()])
        env = box(*np.array(shape.bounds) + np.array([-3, -3, 3, 3]))
        if len(g) == 1:
            out.append(dict(node=g.index[0], country=c, geometry=shape)); continue
        cells = list(voronoi_diagram(pts, envelope=env).geoms)
        for node, r in g.iterrows():
            p = pts.geoms[list(g.index).index(node)]
            cell = next((k for k in cells if k.contains(p)), None)
            if cell is None:
                cell = min(cells, key=lambda k: k.distance(p))
            geom = cell.intersection(shape)
            if not geom.is_empty:
                out.append(dict(node=node, country=c, geometry=geom))
    return gpd.GeoDataFrame(out, crs="EPSG:4326").set_index("node")


def author_potential(tech: str, cutout: atlite.Cutout) -> xr.DataArray:
    d = xr.open_dataset(AUTHOR / "renewable_profiles" / f"profile_{tech}.nc")
    pot = d.potential.load()
    pot = pot.assign_coords(x=np.round(pot.x.values, 3), y=np.round(pot.y.values, 3))
    grid = xr.DataArray(np.zeros((len(cutout.data.y), len(cutout.data.x))), coords=dict(y=np.round(cutout.data.y.values, 3), x=np.round(cutout.data.x.values, 3)), dims=["y", "x"])
    return pot.reindex_like(grid, fill_value=0.0).fillna(0.0)


def convert(cutout: atlite.Cutout, spec: dict, **kw):
    spec = dict(spec); method = spec.pop("method"); cf = spec.pop("correction_factor")
    if method == "wind":
        turb = spec["turbine"]
        if turb == "DEA2050":   # S4B-3 synthetic DEA 2050 power curve (atlite custom turbine dict)
            from s4b_3_wind_calibration import dea2050_turbine
            t = dea2050_turbine(); turb = dict(V=np.asarray(t["V"], float), POW=np.asarray(t["POW"], float), hub_height=float(t["hub_height"]), P=float(t["P"]))
        return cf, cutout.wind(turbine=turb, add_cutout_windspeed=spec["add_cutout_windspeed"], **kw)
    return cf, cutout.pv(panel=spec["panel"], orientation=spec["orientation"], **kw)


def alpha_cutout(cutout: atlite.Cutout, shapes: gpd.GeoDataFrame, table: Path, column: str) -> tuple[atlite.Cutout, dict]:
    """S4B-3: copy of the cutout whose wnd100m is multiplied by the country alpha (cell -> country with the largest area share; no country -> 1)."""
    al = pd.read_csv(table).set_index("country")[column]
    I = cutout.indicatormatrix(shapes.geometry).toarray().reshape(len(shapes), len(cutout.data.y), len(cutout.data.x))
    grid = np.ones((len(cutout.data.y), len(cutout.data.x)))
    best = I.argmax(axis=0); has = I.max(axis=0) > 0
    for i, c in enumerate(shapes.index):
        if c in al.index and np.isfinite(al[c]):
            grid[(best == i) & has] = float(al[c])
    da = xr.DataArray(grid, coords=dict(y=cutout.data.y, x=cutout.data.x), dims=["y", "x"])
    out = atlite.Cutout(str(CUTOUT)); out.data = cutout.data.assign(wnd100m=cutout.data["wnd100m"] * da)
    return out, {str(c): float(al[c]) for c in shapes.index if c in al.index}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", nargs="+", default=["fork"]); ap.add_argument("--classes", type=int, default=1); ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--techs", nargs="+", default=list(TECHS)); ap.add_argument("--output", type=Path, required=True); ap.add_argument("--nprocesses", type=int, default=1)
    ap.add_argument("--alpha-table", type=Path, default=ROOT / "research_inputs/renewable_v5/WIND_CALIBRATION_ALPHA.csv")   # S4B-3 variants with an alpha column
    a = ap.parse_args(); a.output.mkdir(parents=True, exist_ok=True)
    t0 = time.time(); log = dict(cutout=str(CUTOUT), months=a.months, classes=a.classes, variants=a.variant, atlite=atlite.__version__, timings={})
    cutout = atlite.Cutout(str(CUTOUT))
    if a.months < 12:
        cutout = cutout.sel(time=slice("2013-01-01", f"2013-{a.months:02d}-{pd.Timestamp(2013, a.months, 1).days_in_month:02d} 23:00"))
    log["cutout_shape"] = dict(cutout.data.sizes)
    nodes = pd.read_csv(NODES, index_col=0)
    onshore = gpd.read_file(AUTHOR / "shapes/country_shapes.geojson").set_index("name"); offshore = gpd.read_file(AUTHOR / "shapes/offshore_shapes.geojson").set_index("name")
    regions = {"onshore": node_regions(nodes, onshore, "onshore"), "offshore": node_regions(nodes, offshore, "offshore")}
    for k, r in regions.items():
        r.to_file(a.output / f"regions_{k}.geojson", driver="GeoJSON"); log[f"regions_{k}"] = int(len(r))
    log["timings"]["regions"] = round(time.time() - t0, 1)
    scaled = {}

    def cut_for(spec):   # S4B-3: alpha-scaled cutout copies, one per alpha column
        k = spec.get("alpha")
        if not k:
            return cutout
        if k not in scaled:
            scaled[k], log.setdefault("alpha", {})[k] = alpha_cutout(cutout, onshore, a.alpha_table, k)
            log.setdefault("alpha_table", str(a.alpha_table))
        return scaled[k]

    def plain(spec):
        return {kk: vv for kk, vv in spec.items() if kk not in ("alpha", "cf_only")}
    results = []
    for tech in a.techs:
        kind = TECHS[tech]; reg = regions[kind]
        t1 = time.time()
        pot = author_potential(tech, cutout)
        I = cutout.indicatormatrix(reg.geometry)   # bus x cell (fraction of cell inside region)
        I_arr = I.toarray().reshape(len(reg), len(cutout.data.y), len(cutout.data.x))
        # coverage-normalised layout: potential_c = cap x area x sum_b avail[b,c]; with uniform availability inside a cell
        # avail[b,c] = I[b,c] x a_c and sum_b avail = a_c x sum_b I, so weight[b,c] = I[b,c] x potential_c / sum_b' I[b',c] (validated on the author tutorial week)
        cov = I_arr.sum(axis=0); pot_eff = np.where(cov > 0, pot.values / np.maximum(cov, 1e-12), 0.0)
        pot_bus = (I_arr * pot_eff[None]).sum(axis=(1, 2))
        for var in a.variant:
            if tech not in VARIANTS[var]:
                continue
            spec = VARIANTS[var][tech]
            corr, cf_cell = convert(cut_for(spec), plain(spec), capacity_factor=True)
            cf_cell = (corr * cf_cell).fillna(0.0).load()
            # float64: the cutout is float32 and numpy 1.x compares a float32 array against a float64 scalar in float32, where
            # cmax + 1e-9 rounds back to cmax and the best cell of a node falls out of the last class (found by the partition test)
            cfv = cf_cell.values.astype(np.float64)
            n_cls = max(1, a.classes)
            for b, node in enumerate(reg.index):
                w = I_arr[b] * pot_eff
                if w.sum() <= 0:
                    continue
                sel = w > 0; cmin, cmax = float(cfv[sel].min()), float(cfv[sel].max())
                edges = cmin + (cmax - cmin) * np.linspace(0, 1, n_cls + 1)
                wsum_cls = 0.0
                for k in range(n_cls):
                    m = sel & (cfv >= edges[k]) & ((cfv < edges[k + 1]) if k < n_cls - 1 else (cfv <= cmax))   # last class closed at cmax
                    if not m.any():
                        continue
                    wk = np.where(m, w, 0.0); wsum_cls += float(wk.sum())
                    results.append(dict(tech=tech, variant=var, node=node, country=reg.at[node, "country"], cls=k, cf_lo=float(edges[k]), cf_hi=float(edges[k + 1]), potential_mw=float(wk.sum()),
                                        potential_share=float(wk.sum() / w.sum()), cf_annual_weighted=float((wk * cfv).sum() / wk.sum()), cells=int(m.sum()), _w=wk))
                assert abs(wsum_cls - float(w.sum())) <= 1e-9 * float(w.sum()), ("class potentials do not partition the node potential", tech, var, node, wsum_cls, float(w.sum()))
            # time series per node x class: layout = potential x cf (PyPSA-Earth weighting)
            rows = [r for r in results if r["tech"] == tech and r["variant"] == var]
            if rows and not spec.get("cf_only"):
                mat = np.stack([r["_w"].reshape(-1) * cfv.reshape(-1) for r in rows]); mat = mat / mat.sum(axis=1, keepdims=True)
                from scipy import sparse
                M = sparse.csr_matrix(mat)
                _, ts = convert(cut_for(spec), plain(spec), matrix=M, layout=xr.ones_like(cf_cell), index=pd.Index([f"{r['node']}|{r['cls']}" for r in rows], name="bus"), per_unit=True, return_capacity=False)
                ts = (corr * ts).clip(max=1.0)
                ts3 = ts.resample(time="3h").mean()
                ts3.to_netcdf(a.output / f"profile_{tech}_{var}_c{n_cls}_3h.nc"); ts.to_netcdf(a.output / f"profile_{tech}_{var}_c{n_cls}_1h.nc")
                mean3 = ts3.mean("time").to_pandas()
                for r in rows:
                    r["cf_series_mean"] = float(mean3[f"{r['node']}|{r['cls']}"])
            log["timings"][f"{tech}:{var}"] = round(time.time() - t1, 1); t1 = time.time()
        log.setdefault("potential_by_node", {})[tech] = {n: float(v) for n, v in zip(reg.index, pot_bus)}
    for r in results:
        r.pop("_w", None)
    pd.DataFrame(results).to_csv(a.output / "S4A_PROFILE_CLASSES.csv", index=False)
    log["timings"]["total"] = round(time.time() - t0, 1); log["rows"] = len(results)
    (a.output / "S4A_PROFILES_LOG.json").write_text(json.dumps(log, indent=1, default=str))
    print(json.dumps(log["timings"]), "rows", len(results))


if __name__ == "__main__":
    main()
