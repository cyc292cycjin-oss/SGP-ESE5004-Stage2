"""V5 X20 revision 1-1 (decision 241; decision 246 Q1 (b)): GWA v4 100 m wind-speed correction fields for the ERA5 2013 cutout.

Outputs (--output, default research_inputs/renewable_v5):
  WIND_GWA_CELL_FACTOR_V5.nc        factor(y, x) = mean GWA v4 ws100 over the land pixels of the ERA5 cell / ERA5 2013 time-mean wnd100m of the cell;
                                    1 where the GWA land coverage of the cell is < 50 % or no GWA value; clipped to [0.5, 3] (as X03 04b_gwa_lc100.py:112).
                                    Used by the profile build (s4a_profiles.alpha_cutout, variant calibrated_gwa_v5).
  WIND_GWA_CELL_FACTOR_V5.csv       one row per cell with GWA coverage > 0 (iy, ix, x, y, gwa_mean, era5_mean, coverage, factor_raw, factor, clipped).
  WIND_GWA_FARM_POINT_FACTOR_V5.csv calibration farms of s4b_3_wind_calibration (GEM GIPT operating wind, start year <= 2024 or missing, with coordinates):
                                    factor_point = GWA ws100 at the farm point / ERA5 time-mean wnd100m of the farm's cell (same nearest-cell rule as
                                    s4b_3_wind_calibration.py:107); used by the calibration only (Q1 (b): removes the within-cell siting premium).
  WIND_GWA_V5_LOG.json              inputs (bytes, SHA256), counts, timing.
Cell geometry = the cutout grid: cell i spans x_i +- dx/2, y_j +- dy/2 (centres = cutout coordinates). Pixel weights = cos(latitude) (equal-area mean).
Land mask = author country shapes (country_shapes.geojson), so the buffer pixels of the GWA country files are not counted twice. Windowed reading (rows).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
CUTOUT = ROOT / "cutouts/asean_zenodo_20325289/cutout-2013-era5.nc"
GIPT = ROOT / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"
AUTHOR_SHAPES = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/shapes/country_shapes.geojson")
ISO3 = {"BN": "BRN", "KH": "KHM", "ID": "IDN", "LA": "LAO", "MY": "MYS", "MM": "MMR", "PH": "PHL", "SG": "SGP", "TH": "THA", "TL": "TLS", "VN": "VNM"}
COVERAGE_MIN = 0.5
CLIP = (0.5, 3.0)
ROWS = 1024


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def era5_mean(cutout: Path) -> xr.DataArray:
    ds = xr.open_dataset(cutout, chunks={"time": 730})
    return ds["wnd100m"].mean("time").compute().transpose("y", "x")


def cell_index(lon, lat, x0, y0, dx, dy, nx, ny):
    ix = np.round((lon - x0) / dx).astype(np.int64); iy = np.round((lat - y0) / dy).astype(np.int64)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    return ix, iy, ok


def gwa_cells(gwa_dir: Path, shapes, x0, y0, dx, dy, nx, ny, log):
    import rasterio
    from rasterio import features
    from rasterio.windows import Window
    sw = np.zeros(ny * nx); swv = np.zeros(ny * nx); area = np.zeros(ny * nx)
    for c, iso in ISO3.items():
        p = gwa_dir / f"{iso}_wind-speed_100m.tif"
        log["inputs"][str(p)] = dict(bytes=p.stat().st_size, sha256=sha(p))
        geom = shapes.at[c, "geometry"]
        with rasterio.open(p) as s:
            tr = s.transform; nod = s.nodata; resx, resy = abs(tr.a), abs(tr.e)
            lon = tr.c + tr.a * (np.arange(s.width) + 0.5)
            npx = 0
            for r0 in range(0, s.height, ROWS):
                h = min(ROWS, s.height - r0); win = Window(0, r0, s.width, h)
                ws = s.read(1, window=win).astype(np.float64)
                wtr = rasterio.windows.transform(win, tr)
                land = features.rasterize([(geom, 1)], out_shape=ws.shape, transform=wtr, fill=0, dtype="uint8") == 1
                ok = np.isfinite(ws) & land & (ws > 0)
                if nod is not None:
                    ok &= ws != nod
                if not ok.any():
                    continue
                lat = tr.f + tr.e * (r0 + np.arange(h) + 0.5)
                rr, cc = np.nonzero(ok)
                la, lo, v = lat[rr], lon[cc], ws[rr, cc]
                ix, iy, inb = cell_index(lo, la, x0, y0, dx, dy, nx, ny)
                w = np.cos(np.deg2rad(la))
                k = (iy * nx + ix)[inb]
                sw += np.bincount(k, weights=w[inb], minlength=ny * nx)
                swv += np.bincount(k, weights=(w * v)[inb], minlength=ny * nx)
                area += np.bincount(k, weights=(w * resx * resy)[inb], minlength=ny * nx)
                npx += int(inb.sum())
        log["pixels"][c] = npx
        print("gwa", c, npx, round(time.time() - log["t0"], 1), flush=True)
    return sw.reshape(ny, nx), swv.reshape(ny, nx), area.reshape(ny, nx)


NQ = 10            # C-2 (decision 252): equal-area quantile bins per cell
HBIN = 0.02        # histogram bin width of pass 1, m/s
NB = 1500          # histogram bins (0 - 30 m/s; faster pixels go to the last bin)


def _land_pixels(gwa_dir: Path, shapes, x0, y0, dx, dy, nx, ny):
    """yields (cell index, cos-latitude weight, GWA ws100) of the land pixels per row window - the same pixel set and weights as gwa_cells"""
    import rasterio
    from rasterio import features
    from rasterio.windows import Window
    for c, iso in ISO3.items():
        p = gwa_dir / f"{iso}_wind-speed_100m.tif"
        geom = shapes.at[c, "geometry"]
        with rasterio.open(p) as s:
            tr = s.transform; nod = s.nodata
            lon = tr.c + tr.a * (np.arange(s.width) + 0.5)
            for r0 in range(0, s.height, ROWS):
                h = min(ROWS, s.height - r0); win = Window(0, r0, s.width, h)
                ws = s.read(1, window=win).astype(np.float64)
                wtr = rasterio.windows.transform(win, tr)
                land = features.rasterize([(geom, 1)], out_shape=ws.shape, transform=wtr, fill=0, dtype="uint8") == 1
                ok = np.isfinite(ws) & land & (ws > 0)
                if nod is not None:
                    ok &= ws != nod
                if not ok.any():
                    continue
                lat = tr.f + tr.e * (r0 + np.arange(h) + 0.5)
                rr, cc = np.nonzero(ok)
                la, lo, v = lat[rr], lon[cc], ws[rr, cc]
                ix, iy, inb = cell_index(lo, la, x0, y0, dx, dy, nx, ny)
                yield (iy * nx + ix)[inb], np.cos(np.deg2rad(la))[inb], v[inb]


def gwa_cell_quantiles(gwa_dir: Path, shapes, x0, y0, dx, dy, nx, ny, log):
    """C-2 (decision 252, X20_C2_ONWIND_SUBGRID_SPEC.md): per cell NQ equal-area bins of the land-pixel GWA ws100 (cos-latitude weights).
    Pass 1: weighted histogram (HBIN m/s) per cell -> bin boundaries = the histogram bins where the cumulative weight first reaches q / NQ (q = 1..NQ-1);
    pass 2: every pixel goes to the bin = number of boundaries below its histogram bin; per cell and bin sum of weights and of weight x ws.
    Pixels of one histogram bin stay together, so the bins are equal-area up to one histogram bin; the actual area shares are returned and used as weights.
    Returns (sw[ncell, NQ], swv[ncell, NQ]); the land pixels are all land pixels of the cell (country land mask), not only the eligible land (L-C23)."""
    ncell = ny * nx
    H = np.zeros(ncell * NB)
    for k, w, v in _land_pixels(gwa_dir, shapes, x0, y0, dx, dy, nx, ny):
        b = np.minimum((v / HBIN).astype(np.int64), NB - 1)
        H += np.bincount(k * NB + b, weights=w, minlength=ncell * NB)
    H = H.reshape(ncell, NB); C = np.cumsum(H, axis=1); S = C[:, -1:]
    J = np.stack([np.argmax(C >= S * q / NQ - 1e-12 * S, axis=1) for q in range(1, NQ)], axis=1).astype(np.int16)   # boundary histogram bin per cell and q
    log["pass1_seconds"] = round(time.time() - log["t0"], 1); print("pass 1 done", log["pass1_seconds"], flush=True)
    del H, C
    sw = np.zeros(ncell * NQ); swv = np.zeros(ncell * NQ)
    for k, w, v in _land_pixels(gwa_dir, shapes, x0, y0, dx, dy, nx, ny):
        b = np.minimum((v / HBIN).astype(np.int64), NB - 1).astype(np.int16)
        d = np.zeros(len(b), dtype=np.int64)
        for q in range(NQ - 1):   # one boundary at a time (a window holds up to ~2e7 pixels)
            d += b > J[k, q]
        sw += np.bincount(k * NQ + d, weights=w, minlength=ncell * NQ); swv += np.bincount(k * NQ + d, weights=w * v, minlength=ncell * NQ)
    log["pass2_seconds"] = round(time.time() - log["t0"], 1); print("pass 2 done", log["pass2_seconds"], flush=True)
    return sw.reshape(ncell, NQ), swv.reshape(ncell, NQ)


def quantile_factors(sw, swv, era5_mean, use, fac_mean):
    """C-2: factor_q = (bin mean GWA ws) / ERA5 cell mean, clipped [0.5, 3] per bin; weight_q = area share of the bin. Cells outside `use` (coverage < 0.5, no GWA,
    ERA5 mean <= 0): factor_q = 1 and weight_q = 1 / NQ (as the cell rule). Empty bins of a used cell: weight 0, factor = the cell factor. Arrays (ncell, NQ)."""
    tot = sw.sum(axis=1, keepdims=True)
    wq = np.where(tot > 0, sw / np.maximum(tot, 1e-300), 1.0 / NQ)
    raw = np.where(sw > 0, swv / np.maximum(sw, 1e-300), np.nan) / era5_mean[:, None]
    f = np.where(sw > 0, np.clip(raw, *CLIP), fac_mean[:, None])
    u = use[:, None]
    return np.where(u, f, 1.0), np.where(u, wq, 1.0 / NQ), np.where(u, raw, np.nan)


def farm_points(gwa_dir: Path, wm: xr.DataArray, x0, y0, dx, dy, nx, ny, log):
    import rasterio
    gem = pd.read_csv(GIPT, low_memory=False)
    f = gem[(gem.Type == "wind") & (gem.Status == "operating") & (gem["Start year"].isna() | (gem["Start year"] <= 2024)) & gem.Latitude.notna()].copy()
    f["ix"] = np.clip(np.round((f.Longitude - x0) / dx).astype(int), 0, nx - 1); f["iy"] = np.clip(np.round((f.Latitude - y0) / dy).astype(int), 0, ny - 1)
    vals = []
    for _, r in f.iterrows():
        v = np.nan
        order = [r.iso] + [c for c in ISO3 if c != r.iso]
        for c in order:
            with rasterio.open(gwa_dir / f"{ISO3[c]}_wind-speed_100m.tif") as s:
                b = s.bounds
                if not (b.left <= r.Longitude <= b.right and b.bottom <= r.Latitude <= b.top):
                    continue
                x = float(next(s.sample([(r.Longitude, r.Latitude)]))[0])
                if np.isfinite(x) and x > 0 and (s.nodata is None or x != s.nodata):
                    v = x; break
        vals.append(v)
    f["gwa_point_ws100"] = vals
    f["era5_cell_mean_ws100"] = wm.values[f.iy.values, f.ix.values]
    raw = f.gwa_point_ws100 / f.era5_cell_mean_ws100
    f["factor_point_raw"] = raw
    f["factor_point"] = np.where(np.isfinite(raw), np.clip(raw, *CLIP), np.nan)
    log["farms"] = dict(rows=int(len(f)), with_gwa=int(np.isfinite(raw).sum()))
    return f[["GEM unit/phase ID", "Plant / Project name", "iso", "Technology", "Capacity (MW)", "Start year", "Latitude", "Longitude", "ix", "iy",
              "gwa_point_ws100", "era5_cell_mean_ws100", "factor_point_raw", "factor_point"]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--gwa-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=ROOT / "research_inputs/renewable_v5")
    ap.add_argument("--cutout", type=Path, default=CUTOUT)
    ap.add_argument("--quantiles", action="store_true", help="C-2: write only WIND_GWA_CELL_QUANTILES_V5.nc / .csv and their log; the cell-factor outputs are recomputed "
                                                              "and compared with the committed WIND_GWA_CELL_FACTOR_V5.nc, not rewritten")
    a = ap.parse_args(argv)
    if a.quantiles:
        return main_quantiles(a)
    import geopandas as gpd
    a.output.mkdir(parents=True, exist_ok=True)
    log = dict(script="scripts_project/v5_wind_gwa.py", t0=time.time(), inputs={}, pixels={}, coverage_min=COVERAGE_MIN, clip=CLIP)
    for p in (a.cutout, GIPT, AUTHOR_SHAPES):
        log["inputs"][str(p)] = dict(bytes=p.stat().st_size, sha256=sha(p))
    wm = era5_mean(a.cutout)
    xs, ys = wm.x.values, wm.y.values; nx, ny = len(xs), len(ys)
    x0, y0, dx, dy = float(xs[0]), float(ys[0]), float(xs[1] - xs[0]), float(ys[1] - ys[0])
    print("era5 mean", ny, nx, round(time.time() - log["t0"], 1), flush=True)
    shapes = gpd.read_file(AUTHOR_SHAPES).set_index("name")
    sw, swv, area = gwa_cells(a.gwa_dir, shapes, x0, y0, dx, dy, nx, ny, log)
    cell_area = abs(dx * dy) * np.cos(np.deg2rad(ys))[:, None] * np.ones((1, nx))
    gmean = np.where(sw > 0, swv / np.maximum(sw, 1e-300), np.nan)
    cov = area / cell_area
    raw = gmean / wm.values
    use = np.isfinite(raw) & (cov >= COVERAGE_MIN) & (wm.values > 0)
    fac = np.where(use, np.clip(raw, *CLIP), 1.0)
    clipped = use & ((raw < CLIP[0]) | (raw > CLIP[1]))
    da = xr.DataArray(fac, coords=dict(y=ys, x=xs), dims=["y", "x"], name="gwa_factor",
                      attrs=dict(description="GWA v4 ws100 land mean / ERA5 2013 time-mean wnd100m per cutout cell; 1 if coverage < 0.5 or no GWA; clipped [0.5, 3]",
                                 source="Global Wind Atlas v4 country GeoTIFFs (wind-speed 100 m), ERA5 2013 cutout (Zenodo 10.5281/zenodo.20325289)"))
    out_nc = a.output / "WIND_GWA_CELL_FACTOR_V5.nc"
    da.to_dataset().to_netcdf(out_nc)
    iy, ix = np.nonzero(cov > 0)
    rows = pd.DataFrame(dict(iy=iy, ix=ix, x=xs[ix], y=ys[iy], gwa_mean=gmean[iy, ix], era5_mean=wm.values[iy, ix], coverage=cov[iy, ix], factor_raw=raw[iy, ix],
                             factor=fac[iy, ix], used=use[iy, ix], clipped=clipped[iy, ix]))
    rows.to_csv(a.output / "WIND_GWA_CELL_FACTOR_V5.csv", index=False, float_format="%.10g")
    farms = farm_points(a.gwa_dir, wm, x0, y0, dx, dy, nx, ny, log)
    farms.to_csv(a.output / "WIND_GWA_FARM_POINT_FACTOR_V5.csv", index=False, float_format="%.10g")
    log.update(cells_with_coverage=int((cov > 0).sum()), cells_used=int(use.sum()), cells_clipped=int(clipped.sum()),
               factor_used_min=float(fac[use].min()), factor_used_max=float(fac[use].max()), factor_used_median=float(np.median(fac[use])),
               seconds=round(time.time() - log.pop("t0"), 1))
    for k in ("WIND_GWA_CELL_FACTOR_V5.nc", "WIND_GWA_CELL_FACTOR_V5.csv", "WIND_GWA_FARM_POINT_FACTOR_V5.csv"):
        log.setdefault("outputs", {})[k] = dict(bytes=(a.output / k).stat().st_size, sha256=sha(a.output / k))
    (a.output / "WIND_GWA_V5_LOG.json").write_text(json.dumps(log, indent=1, default=str))
    print(json.dumps({k: v for k, v in log.items() if k not in ("inputs",)}, default=str)[:1500])


def main_quantiles(a):
    """C-2 (decision 252): WIND_GWA_CELL_QUANTILES_V5.nc = factor(q, y, x) and weight(q, y, x), q = 0..NQ-1 (bins of increasing wind speed); the cell factor of
    WIND_GWA_CELL_FACTOR_V5.nc is recomputed with the same rules and must equal the committed file; sum_q weight x raw factor = the raw cell factor."""
    import geopandas as gpd
    log = dict(script="scripts_project/v5_wind_gwa.py --quantiles", t0=time.time(), inputs={}, pixels={}, nq=NQ, histogram_bin_ms=HBIN, histogram_bins=NB,
               coverage_min=COVERAGE_MIN, clip=CLIP, land_pixels="all land pixels of the cell (author country shapes), not restricted to the eligible land")
    for p in (a.cutout, AUTHOR_SHAPES):
        log["inputs"][str(p)] = dict(bytes=p.stat().st_size, sha256=sha(p))
    wm = era5_mean(a.cutout)
    xs, ys = wm.x.values, wm.y.values; nx, ny = len(xs), len(ys)
    x0, y0, dx, dy = float(xs[0]), float(ys[0]), float(xs[1] - xs[0]), float(ys[1] - ys[0])
    shapes = gpd.read_file(AUTHOR_SHAPES).set_index("name")
    sw0, swv0, area = gwa_cells(a.gwa_dir, shapes, x0, y0, dx, dy, nx, ny, log)
    cell_area = abs(dx * dy) * np.cos(np.deg2rad(ys))[:, None] * np.ones((1, nx))
    gmean = np.where(sw0 > 0, swv0 / np.maximum(sw0, 1e-300), np.nan); cov = area / cell_area; raw = gmean / wm.values
    use = np.isfinite(raw) & (cov >= COVERAGE_MIN) & (wm.values > 0)
    fac = np.where(use, np.clip(raw, *CLIP), 1.0)
    ref = xr.open_dataarray(a.output / "WIND_GWA_CELL_FACTOR_V5.nc").transpose("y", "x").values
    log["cell_factor_equals_committed"] = bool(np.array_equal(fac, ref))
    if not log["cell_factor_equals_committed"]:
        raise SystemExit("C-2: the recomputed cell factor differs from the committed WIND_GWA_CELL_FACTOR_V5.nc")
    sw, swv = gwa_cell_quantiles(a.gwa_dir, shapes, x0, y0, dx, dy, nx, ny, log)
    fq, wq, rq = quantile_factors(sw, swv, wm.values.reshape(-1), use.reshape(-1), fac.reshape(-1))
    u = use.reshape(-1)
    mean_raw_q = np.nansum(wq * np.where(np.isfinite(rq), rq, 0.0), axis=1)
    log["mean_identity_max_abs"] = float(np.nanmax(np.abs(mean_raw_q[u] - raw.reshape(-1)[u])))   # sum_q w_q raw_q = raw cell factor (up to rounding)
    share = wq[u]; log["bin_share_min"] = float(share[share > 0].min()); log["bin_share_max"] = float(share.max()); log["empty_bins_in_used_cells"] = int((share == 0).sum())
    log["cells_used"] = int(u.sum()); log["bins_clipped"] = int((u[:, None] & np.isfinite(rq) & ((rq < CLIP[0]) | (rq > CLIP[1]))).sum())
    log["spread_p90_over_p10_median"] = float(np.median((fq[u, -1] / fq[u, 0])))
    q = np.arange(NQ)
    ds = xr.Dataset(dict(factor=(("q", "y", "x"), fq.T.reshape(NQ, ny, nx)), weight=(("q", "y", "x"), wq.T.reshape(NQ, ny, nx))), coords=dict(q=q, y=ys, x=xs),
                    attrs=dict(description="C-2 (decision 252): per ERA5 cell NQ equal-area bins of the land-pixel GWA v4 ws100 / ERA5 2013 time-mean wnd100m; factor clipped [0.5, 3] per bin; "
                                           "weight = area share of the bin; cells with coverage < 0.5 or no GWA: factor 1, weight 1 / NQ",
                               land_pixels=log["land_pixels"], source="Global Wind Atlas v4 country GeoTIFFs (wind-speed 100 m), ERA5 2013 cutout (Zenodo 10.5281/zenodo.20325289)"))
    out_nc = a.output / "WIND_GWA_CELL_QUANTILES_V5.nc"
    ds.to_netcdf(out_nc)
    iy, ix = np.nonzero(use)
    k = iy * nx + ix
    rows = pd.DataFrame(dict(iy=iy, ix=ix, x=xs[ix], y=ys[iy], factor_mean=fac[iy, ix], **{f"factor_q{j}": fq[k, j] for j in q}, **{f"weight_q{j}": wq[k, j] for j in q}))
    rows.to_csv(a.output / "WIND_GWA_CELL_QUANTILES_V5.csv", index=False)
    log["seconds"] = round(time.time() - log.pop("t0"), 1)
    for kf in ("WIND_GWA_CELL_QUANTILES_V5.nc", "WIND_GWA_CELL_QUANTILES_V5.csv"):
        log.setdefault("outputs", {})[kf] = dict(bytes=(a.output / kf).stat().st_size, sha256=sha(a.output / kf))
    (a.output / "WIND_GWA_QUANTILES_V5_LOG.json").write_text(json.dumps(log, indent=1, default=str))
    print(json.dumps({kk: vv for kk, vv in log.items() if kk not in ("inputs",)}, default=str)[:1500])


if __name__ == "__main__":
    main()
