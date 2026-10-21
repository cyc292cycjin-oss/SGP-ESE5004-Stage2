"""M08a A6.2 (M08-7, decisions 129, 131; registry renewable_offshore_rule): offshore wind eligible area, potentials, 3 h profiles and
connection distances under the PyPSA-Eur v2025.07.0 area rules - fixed-bottom AC / DC and the new floating carrier. Nothing is solved.

Rules (PyPSA-Eur v2025.07.0; config copy research_inputs/registry_v5/sources/pypsa_eur_v2025.07.0_config.default.yaml, SHA256 bfbe9160...;
scripts/determine_availability_matrix.py SHA256 bdddee1e..., scripts/build_renewable_profiles.py SHA256 12fe6776..., scripts/build_ship_raster.py
SHA256 bab4a06d..., read from GitHub tag v2025.07.0 on 2026-10-21):
  offwind-ac     config lines 201-219: 2 MW/km2, depth <= 60 m, shore distance <= 30 km, landfall 20 km
  offwind-dc     config lines 220-238: 2 MW/km2, depth <= 60 m, shore distance >= 30 km, landfall 30 km
  offwind-float  config lines 239-260: 2 MW/km2, 60 m < depth <= 1,000 m, no shore-distance rule, landfall 40 km,
                 NREL_ReferenceTurbine_5MW_offshore x 0.8855, add_cutout_windspeed
  all three      natura excluded; eligible land cover = open sea (corine [44, 255] -> Copernicus LC100 [80, 200], the author chain's
                 equivalent); shipping lanes excluded where density > ship_threshold 400 x 8760 x 6 (determine_availability_matrix.py
                 126-133; World Bank global shipping density, 6 years of hourly AIS positions); excluder resolution 200 m.
  exclusion semantics = determine_availability_matrix.py 96-156 (max_depth: exclude v < -max_depth, nodata -1000; min_depth: invert of
  v < -min_depth; min / max shore distance = buffer of the onshore country shapes, invert for max).
Registered adaptations (not PyPSA-Eur literal): excluder CRS ESRI:54009 (Mollweide, equal-area; the author chain's area_crs) instead of
EPSG:3035 (Europe-only LAEA); cell area in ESRI:54009; Copernicus LC100 instead of CORINE; GEBCO 2025 instead of GEBCO 2014; node
regions, 3 resource classes (linear bins between the node cf min and max, last class closed) and connection distances (cell centre ->
node onshore region, local azimuthal equidistant projection, layout-weighted) exactly as S4A / S4C-1 for the other carriers; ship
density clipped from the zip through /vsizip/ instead of extracting the 9.8 GB tif (same window as build_ship_raster.py).
Turbines unchanged for AC / DC (s4a_profiles.VARIANTS['pypsa_eur'], decision 131: types and wake factor already equal PyPSA-Eur).

--rules author re-computes the AC / DC potential with the author PyPSA-Earth rules (Copernicus [80, 200], natura, depth <= 50 m, shore
<= / >= 30 km, 2 / 3 MW/km2, no shipping lanes) for validation against the author potential used so far (s4a_profiles.author_potential).

    python scripts_project/m08a_offshore_profiles.py --output research_inputs/renewable_v5/offshore_m08a --work /home/jin/m08a_offshore_work --nprocesses 4
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
AUTHOR_DATA = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data")
DEFAULTS = dict(
    cutout=MAIN / "cutouts/asean_zenodo_20325289/cutout-2013-era5.nc",
    regions_offshore=MAIN / "research_inputs/renewable_v5/regions_offshore.geojson",   # S4A node regions (64 MB, local; MANIFEST.json SHA256)
    regions_onshore=MAIN / "research_inputs/renewable_v5/regions_onshore.geojson",
    nodes=MAIN / "results_project/s4a/analysis/AC_NODES_XY.csv",
    country_shapes=Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson"),
    natura=AUTHOR_DATA / "natura/natura.tiff",
    copernicus=AUTHOR_DATA / "copernicus/PROBAV_LC100_global_v3.0.1_2019-nrt_Discrete-Classification-map_EPSG-4326.tif",
    gebco=AUTHOR_DATA / "gebco/GEBCO_2025_sub_ice.nc",
    ship_zip=Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p2_data_intake/raw12/shipdensity_global.zip"),
)
SHIP_ZIP_SHA256 = "7d103de52acf355ffc2436909d5d98e9db93f74d6ad237680e5da6d6d24a9248"   # registry renewable_ship_density_raster
AREA_CRS = "ESRI:54009"
COMMON = dict(landcover_codes=[80, 200], natura=True, ship_threshold=400.0, excluder_resolution=200)
RULES = {
    "pypsa_eur_v2025_07": {
        "offwind-ac": dict(COMMON, capacity_per_sqkm=2.0, max_depth=60.0, max_shore_distance=30000.0, landfall_km=20.0, config_lines="201-219"),
        "offwind-dc": dict(COMMON, capacity_per_sqkm=2.0, max_depth=60.0, min_shore_distance=30000.0, landfall_km=30.0, config_lines="220-238"),
        "offwind-float": dict(COMMON, capacity_per_sqkm=2.0, min_depth=60.0, max_depth=1000.0, landfall_km=40.0, config_lines="239-260"),
    },
    "author": {   # pypsa-asean config.default.yaml 367-405 (author PyPSA-Earth chain): validation only
        "offwind-ac": dict(landcover_codes=[80, 200], natura=True, ship_threshold=None, excluder_resolution=200, capacity_per_sqkm=2.0, max_depth=50.0, max_shore_distance=30000.0),
        "offwind-dc": dict(landcover_codes=[80, 200], natura=True, ship_threshold=None, excluder_resolution=200, capacity_per_sqkm=3.0, max_depth=50.0, min_shore_distance=30000.0),
    },
}
# evidence only: the main rules without the shipping-lane exclusion (size of the ship_threshold effect)
RULES["pypsa_eur_v2025_07_no_ship_lanes"] = {t: dict(r, ship_threshold=None) for t, r in RULES["pypsa_eur_v2025_07"].items()}
FLOAT_SPEC = dict(method="wind", turbine="NREL_ReferenceTurbine_5MW_offshore", correction_factor=0.8855, add_cutout_windspeed=True)   # config lines 243-249
LINE_LENGTH_FACTOR = 1.25   # config line 325 (as S4C-1)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def spec_of(tech: str) -> dict:
    from s4a_profiles import VARIANTS
    return dict(FLOAT_SPEC) if tech == "offwind-float" else dict(VARIANTS["pypsa_eur"]["offwind-ac"])


def ship_raster(zip_path: Path, cutout, out: Path) -> dict:
    """build_ship_raster.py on the cutout extent (x - dx/2 ... X + dx/2), read through /vsizip/ (no 9.8 GB extraction)."""
    import rasterio
    from rasterio.windows import from_bounds
    x, X, y, Y = cutout.extent
    b = (x - cutout.dx / 2, y - cutout.dy / 2, X + cutout.dx / 2, Y + cutout.dy / 2)
    if out.exists():   # clipped by an earlier run of this script (same zip, same cutout)
        with rasterio.open(out) as r:
            return dict(path=str(out), sha256=sha(out), reused=True, bounds=b, raster_bounds=list(r.bounds), shape=[r.height, r.width], dtype=r.dtypes[0], max=float(r.read(1).max()))
    with rasterio.open(f"/vsizip/{zip_path}/shipdensity_global.tif") as src:
        w = from_bounds(*b, transform=src.transform).round_offsets().round_lengths()
        arr = src.read(1, window=w)
        prof = src.profile.copy()
        prof.update(height=arr.shape[0], width=arr.shape[1], transform=src.window_transform(w), compress="deflate", tiled=True, blockxsize=512, blockysize=512, BIGTIFF="IF_SAFER")
        prof.pop("photometric", None)
    out.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out, "w", **prof) as dst:
        dst.write(arr, 1)
    return dict(path=str(out), sha256=sha(out), reused=False, bounds=b, shape=list(arr.shape), dtype=str(arr.dtype), max=float(np.nanmax(arr)))


def excluder_for(rule: dict, paths: dict, ship_tif: Path | None):
    """ExclusionContainer with the determine_availability_matrix.py semantics (lines 96-156)."""
    import atlite
    ex = atlite.ExclusionContainer(crs=AREA_CRS, res=rule["excluder_resolution"])
    if rule.get("natura"):
        ex.add_raster(str(paths["natura"]), nodata=0, allow_no_overlap=True)                                  # 99-100
    ex.add_raster(str(paths["copernicus"]), codes=rule["landcover_codes"], invert=True, crs=4326)           # 112-118 (list -> grid_codes, invert)
    if rule.get("ship_threshold"):
        thr = rule["ship_threshold"] * 8760 * 6                                                               # 126-133
        ex.add_raster(str(ship_tif), codes=functools.partial(np.less, thr), crs=4326, allow_no_overlap=True)
    if rule.get("max_depth"):
        ex.add_raster(str(paths["gebco"]), codes=functools.partial(np.greater, -rule["max_depth"]), crs=4326, nodata=-1000)               # 135-140
    if rule.get("min_depth"):
        ex.add_raster(str(paths["gebco"]), codes=functools.partial(np.greater, -rule["min_depth"]), crs=4326, nodata=-1000, invert=True)  # 142-146
    if "min_shore_distance" in rule:
        ex.add_geometry(str(paths["country_shapes"]), buffer=rule["min_shore_distance"])                                                  # 148-150
    if "max_shore_distance" in rule:
        ex.add_geometry(str(paths["country_shapes"]), buffer=rule["max_shore_distance"], invert=True)                                     # 152-156
    return ex


def node_distances(cells_xy: np.ndarray, weights: np.ndarray, node: str, nodes: pd.DataFrame, on_reg) -> float:
    """S4C-1: layout-weighted distance (km) of the cell centres to the node onshore region, local azimuthal equidistant projection."""
    from pyproj import CRS, Transformer
    from shapely.geometry import Point
    from shapely.ops import transform
    if node not in on_reg.index:
        return float("nan")
    lon0, lat0 = float(nodes.at[node, "x"]), float(nodes.at[node, "y"])
    fwd = Transformer.from_crs("EPSG:4326", CRS.from_proj4(f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m"), always_xy=True).transform
    shore = transform(fwd, on_reg.loc[node, "geometry"])
    px, py = fwd(cells_xy[:, 0], cells_xy[:, 1])
    d = np.array([shore.distance(Point(a, b)) / 1e3 for a, b in zip(px, py)])
    return float((d * weights).sum() / weights.sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True); ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--rules", default="pypsa_eur_v2025_07", choices=sorted(RULES)); ap.add_argument("--techs", nargs="+", default=None)
    ap.add_argument("--classes", type=int, nargs="+", default=[1, 3]); ap.add_argument("--nprocesses", type=int, default=4)
    ap.add_argument("--regions-subset", nargs="+", default=None, help="timing test: only these node regions")
    ap.add_argument("--no-profiles", action="store_true", help="availability / potential only (validation, timing)")
    for k, v in DEFAULTS.items():
        ap.add_argument("--" + k.replace("_", "-"), type=Path, default=v)
    a = ap.parse_args()
    import atlite
    import geopandas as gpd
    import xarray as xr
    from scipy import sparse
    from s4a_profiles import author_potential, convert
    paths = {k: getattr(a, k) for k in DEFAULTS}
    t0 = time.time(); a.output.mkdir(parents=True, exist_ok=True); a.work.mkdir(parents=True, exist_ok=True)
    rules = RULES[a.rules]; techs = a.techs or list(rules)
    log = dict(schema="m08a-offshore-profiles-v1", rules=a.rules, rule_values=rules, techs=techs, area_crs=AREA_CRS, classes=a.classes, atlite=atlite.__version__,
               line_length_factor=LINE_LENGTH_FACTOR, solver_runs=0, inputs={}, timings={}, sources_pypsa_eur=dict(
                   tag="v2025.07.0", config_sha256="bfbe9160db09c3e960b97173bc755492b7638e0f4a5081ffaa1dddd4635da787",
                   determine_availability_matrix_sha256="bdddee1e16a9a21f40d8ac297d96d5951d54c3d8507744b4ac02aae3499db1a7",
                   build_renewable_profiles_sha256="12fe6776e65d05f86707077fab99406815d8604f18ebce3b895feb15735ec5c3",
                   build_ship_raster_sha256="bab4a06d8015d67b47a5da9a51c39388c070556e910f81913fd6ee76ccbae05a"))
    for k, p in paths.items():
        if k != "cutout":   # the 7.35 GB cutout: size + mtime (hash recorded by the S4A manifests)
            log["inputs"][k] = dict(path=str(p), sha256=sha(p) if p.stat().st_size < 2e9 else None, bytes=p.stat().st_size)
        else:
            log["inputs"][k] = dict(path=str(p), bytes=p.stat().st_size)
    if log["inputs"]["ship_zip"]["sha256"] != SHIP_ZIP_SHA256:
        raise SystemExit("shipdensity_global.zip SHA256 differs from the registered value")
    cutout = atlite.Cutout(str(paths["cutout"]))
    ship_tif = None
    if any(rules[t].get("ship_threshold") for t in techs):
        ship_tif = a.work / "shipdensity_asean_cutout_extent.tif"
        log["ship_raster"] = ship_raster(paths["ship_zip"], cutout, ship_tif); log["timings"]["ship_raster"] = round(time.time() - t0, 1)
    nodes = pd.read_csv(paths["nodes"], index_col=0)
    off = gpd.read_file(paths["regions_offshore"]).set_index("node"); on = gpd.read_file(paths["regions_onshore"]).set_index("node")
    if a.regions_subset:
        off = off.loc[[r for r in a.regions_subset if r in off.index]]
    area = cutout.grid.to_crs(AREA_CRS).area.values.reshape(cutout.shape) / 1e6
    xs, ys = np.meshgrid(cutout.data.x.values, cutout.data.y.values)
    ny, nx = cutout.shape
    rows, series, avail_out = [], {c: {} for c in a.classes}, {}
    cf_cache = {}
    for tech in techs:
        rule = rules[tech]; t1 = time.time()
        ex = excluder_for(rule, paths, ship_tif)
        av = cutout.availabilitymatrix(off.geometry, ex, nprocesses=a.nprocesses, disable_progressbar=True)   # bus x y x x: eligible share of the cell area
        if av.dims[0] != "node":
            av = av.rename({av.dims[0]: "node"})
        avail_out[tech] = av.astype("float32")
        log["timings"][f"{tech}:availability"] = round(time.time() - t1, 1)
        A = av.values.astype(np.float64)                                     # node x y x x
        pot = rule["capacity_per_sqkm"] * A * area[None]                     # MW per node x cell (p_nom_max = capacity_per_sqkm x availability @ area, line 285)
        log.setdefault("potential_mw_by_country", {})[tech] = pd.Series(pot.sum(axis=(1, 2)), index=av.node.values).groupby(off.country).sum().round(1).to_dict()
        if a.rules == "author":
            ref = author_potential(tech, cutout).values
            log.setdefault("author_validation", {})[tech] = dict(total_new_mw=float(pot.sum()), total_author_mw=float(ref.sum()),
                                                                  by_node=pd.DataFrame(dict(new=pot.sum(axis=(1, 2)))).set_index(av.node.values).new.round(1).to_dict())
        if a.no_profiles:
            continue
        spec = spec_of(tech); key = (spec["turbine"], spec["correction_factor"])
        if key not in cf_cache:
            corr, cf_cell = convert(cutout, dict(spec), capacity_factor=True)
            cf_cache[key] = (corr, (corr * cf_cell).fillna(0.0).load().values.astype(np.float64))
        corr, cfv = cf_cache[key]
        log["timings"][f"{tech}:cf"] = round(time.time() - t1, 1)
        for ncls in a.classes:
            mats, keys = [], []
            for b, node in enumerate(av.node.values):
                w = pot[b]
                if w.sum() <= 0:
                    continue
                sel = w > 0; cmin, cmax = float(cfv[sel].min()), float(cfv[sel].max())
                edges = cmin + (cmax - cmin) * np.linspace(0, 1, ncls + 1)
                tot = 0.0
                for k in range(ncls):
                    m = sel & (cfv >= edges[k]) & ((cfv < edges[k + 1]) if k < ncls - 1 else (cfv <= cmax))   # last class closed at cmax (S4A)
                    if not m.any():
                        continue
                    wk = np.where(m, w, 0.0); lw = wk * cfv; tot += float(wk.sum())
                    dist = node_distances(np.c_[xs[m], ys[m]], lw[m], node, nodes, on) if lw.sum() > 0 else float("nan")
                    rows.append(dict(rules=a.rules, tech=tech, classes=ncls, node=node, country=str(off.at[node, "country"]), cls=k, cf_lo=float(edges[k]), cf_hi=float(edges[k + 1]),
                                     cells=int(m.sum()), potential_mw=float(wk.sum()), potential_share=float(wk.sum() / w.sum()), cf_annual_weighted=float(lw.sum() / wk.sum()),
                                     average_distance_km=dist, landfall_km=rule.get("landfall_km"), line_length_factor=LINE_LENGTH_FACTOR,
                                     onshore_region=node in on.index, generator_key=f"{node}|{k}"))
                    if lw.sum() > 0:
                        mats.append(lw.reshape(-1) / lw.sum()); keys.append(f"{node}|{k}")
                assert abs(tot - float(w.sum())) <= 1e-9 * float(w.sum()), ("classes do not partition the node potential", tech, node)
            if mats:
                M = sparse.csr_matrix(np.stack(mats))
                ones = xr.DataArray(np.ones((ny, nx)), coords=dict(y=cutout.data.y, x=cutout.data.x), dims=["y", "x"])
                _, ts = convert(cutout, dict(spec), matrix=M, layout=ones, index=pd.Index(keys, name="bus"), per_unit=True, return_capacity=False)
                ts = (corr * ts).clip(max=1.0)
                series[ncls][tech] = ts.resample(time="3h").mean()
            log["timings"][f"{tech}:c{ncls}"] = round(time.time() - t1, 1)
    xr.Dataset({t.replace("-", "_"): v for t, v in avail_out.items()}).to_netcdf(a.output / f"AVAILABILITY_{a.rules}.nc")
    if not a.no_profiles:
        for ncls, d in series.items():
            if d:
                ds = xr.Dataset({t.replace("-", "_"): v for t, v in d.items()})
                ds.attrs.update(rules=a.rules, classes=ncls, note="3 h means of the hourly atlite series (2013), per_unit, x correction_factor, clipped at 1")
                ds.to_netcdf(a.output / f"profiles_offshore_{a.rules}_c{ncls}_3h.nc")
        pd.DataFrame(rows).to_csv(a.output / f"OFFSHORE_CLASSES_{a.rules}.csv", index=False)
    log["timings"]["total"] = round(time.time() - t0, 1)
    log["outputs"] = {p.name: dict(sha256=sha(p), bytes=p.stat().st_size) for p in sorted(a.output.glob(f"*{a.rules}*"))}
    (a.output / f"OFFSHORE_PROFILES_LOG_{a.rules}.json").write_text(json.dumps(log, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(dict(timings=log["timings"], potential_gw={t: round(sum(v.values()) / 1e3, 1) for t, v in log.get("potential_mw_by_country", {}).items()}), indent=1))


if __name__ == "__main__":
    main()
