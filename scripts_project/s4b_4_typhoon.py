"""S4B-4 (decision 76): tropical-cyclone exposure of the wind candidates from IBTrACS v04r01 (WP + NI basins, 1980-2024).

Per 0.3 deg cell of the ASEAN cutout grid: number of distinct storms whose centre passed within 100 km while the sustained wind was
>= 50 m/s (= 97.19 kt), per 10 years (count x 10 / 45). Wind: USA_WIND (JTWC / NHC, 1-min sustained, kt) where reported; otherwise
WMO_WIND (reporting agency, mostly 10-min) / 0.93 (WMO guidance Harper et al. 2010, at-sea 1-min -> 10-min ratio 0.93) - this fallback is
recorded per point. Tracks are interpolated linearly to 30-min steps (position and wind) between consecutive valid records of a storm.
Node exposure: share of the node's wind potential (author layout potential per cell, onshore regions for onwind, offshore regions for
offwind-ac/dc; S4A-1 node regions) lying in cells at or above the frequency threshold; a node-technology is flagged when that share is >= 0.5.
Thresholds: 1 per 10 years (default) and 0.5 / 2 per 10 years as the sensitivity range.

    python scripts_project/s4b_4_typhoon.py --ibtracs <dir with ibtracs.WP/NI.list.v04r01.csv> --output research_inputs/renewable_v5
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KT_50MS = 50.0 / 0.514444
WMO_TO_1MIN = 1 / 0.93
YEARS = (1980, 2024)
THRESHOLDS = (0.5, 1.0, 2.0)
DEFAULT = 1.0


def load(ib_dir: Path):
    frames = []
    for b in ["WP", "NI"]:
        d = pd.read_csv(ib_dir / f"ibtracs.{b}.list.v04r01.csv", skiprows=[1], low_memory=False, usecols=["SID", "SEASON", "BASIN", "NAME", "ISO_TIME", "LAT", "LON", "WMO_WIND", "WMO_AGENCY", "USA_WIND"])
        frames.append(d.assign(file_basin=b))
    d = pd.concat(frames, ignore_index=True)
    for c in ["SEASON", "LAT", "LON", "WMO_WIND", "USA_WIND"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[(d.SEASON >= YEARS[0]) & (d.SEASON <= YEARS[1]) & d.LAT.notna() & d.LON.notna()].copy()
    d["time"] = pd.to_datetime(d.ISO_TIME)
    d["wind_kt_1min"] = d.USA_WIND.where(d.USA_WIND.notna(), d.WMO_WIND * WMO_TO_1MIN)
    d["wind_source"] = np.where(d.USA_WIND.notna(), "USA_WIND", np.where(d.WMO_WIND.notna(), "WMO_WIND/0.93", "none"))
    return d.drop_duplicates(["SID", "time"]).sort_values(["SID", "time"])


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2); dl = np.radians(lon2 - lon1)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def main():
    import atlite, geopandas as gpd, xarray as xr
    from s4a_profiles import CUTOUT, AUTHOR, author_potential
    ap = argparse.ArgumentParser(); ap.add_argument("--ibtracs", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); a = ap.parse_args()
    d = load(a.ibtracs)
    cut = atlite.Cutout(str(CUTOUT)); xs, ys = cut.data.x.values.astype(float), cut.data.y.values.astype(float)
    count = np.zeros((len(ys), len(xs)), dtype=np.int32); storms_used = 0; pts_used = 0; src_counts = {}
    for sid, g in d.groupby("SID"):
        g = g[g.wind_kt_1min.notna()]
        if len(g) < 1 or g.wind_kt_1min.max() < KT_50MS:
            continue
        t = (g.time - g.time.iloc[0]).dt.total_seconds().values / 3600.0
        if len(g) > 1:
            tt = np.arange(0.0, t[-1] + 1e-9, 0.5)
            lat = np.interp(tt, t, g.LAT.values); lon = np.interp(tt, t, g.LON.values); wind = np.interp(tt, t, g.wind_kt_1min.values)
        else:
            lat, lon, wind = g.LAT.values, g.LON.values, g.wind_kt_1min.values
        m = wind >= KT_50MS
        if not m.any():
            continue
        hit = np.zeros_like(count, dtype=bool)
        for la, lo in zip(lat[m], lon[m]):
            if la < ys.min() - 1.5 or la > ys.max() + 1.5 or lo < xs.min() - 1.5 or lo > xs.max() + 1.5:
                continue
            iy = np.where(np.abs(ys - la) <= 1.0)[0]; ix = np.where(np.abs(xs - lo) <= 1.0 / max(np.cos(np.radians(la)), 0.3))[0]
            if not len(iy) or not len(ix):
                continue
            Y, X = np.meshgrid(ys[iy], xs[ix], indexing="ij")
            near = haversine(la, lo, Y, X) <= 100.0
            hit[np.ix_(iy, ix)] |= near
        if hit.any():
            count += hit; storms_used += 1; pts_used += int(m.sum())
            for s_, k in g.wind_source.value_counts().items():
                src_counts[s_] = src_counts.get(s_, 0) + int(k)
    freq = count * 10.0 / (YEARS[1] - YEARS[0] + 1)
    da = xr.DataArray(freq, coords=dict(y=ys, x=xs), dims=["y", "x"], name="cat_ge50ms_passages_per_decade")
    da.attrs.update(description="storms per 10 years with centre within 100 km and sustained wind >= 50 m/s (1-min), IBTrACS v04r01 WP+NI 1980-2024", source="IBTrACS v04r01 (NOAA NCEI)")
    da.to_dataset().to_netcdf(a.output / "TYPHOON_FREQ_0P3_IBTRACS_1980_2024.nc", encoding={"cat_ge50ms_passages_per_decade": dict(zlib=True, complevel=5, dtype="float32")})
    # country distribution (land and sea shapes of the author chain)
    on = gpd.read_file(AUTHOR / "shapes/country_shapes.geojson").set_index("name"); off = gpd.read_file(AUTHOR / "shapes/offshore_shapes.geojson").set_index("name")
    crow = []
    for kind, shp in [("onshore", on), ("offshore", off)]:
        I = cut.indicatormatrix(shp.geometry).toarray().reshape(len(shp), len(ys), len(xs))
        for i, c in enumerate(shp.index):
            w = I[i]
            if w.sum() <= 0:
                continue
            r = dict(country=c, area=kind, cells=float(w.sum()), freq_max=float(freq[w > 0].max()), freq_area_mean=float((w * freq).sum() / w.sum()))
            for th in THRESHOLDS:
                r[f"area_share_ge_{th:g}"] = float((w * (freq >= th)).sum() / w.sum())
            crow.append(r)
    C = pd.DataFrame(crow)
    # node exposure by potential
    regions = {"onshore": gpd.read_file(ROOT / "research_inputs/renewable_v5/regions_onshore.geojson").set_index("node"),
               "offshore": gpd.read_file(ROOT / "research_inputs/renewable_v5/regions_offshore.geojson").set_index("node")}
    nrow = []
    for tech, kind in [("onwind", "onshore"), ("offwind-ac", "offshore"), ("offwind-dc", "offshore")]:
        reg = regions[kind]; pot = author_potential(tech, cut).values
        I = cut.indicatormatrix(reg.geometry).toarray().reshape(len(reg), len(ys), len(xs)); cov = I.sum(axis=0)
        pe = np.where(cov > 0, pot / np.maximum(cov, 1e-12), 0.0)
        for b, node in enumerate(reg.index):
            w = I[b] * pe
            if w.sum() <= 0:
                continue
            r = dict(node=node, country=str(reg.at[node, "country"]), tech=tech, potential_mw=float(w.sum()), freq_potential_weighted=float((w * freq).sum() / w.sum()), freq_max=float(freq[w > 0].max()))
            for th in THRESHOLDS:
                r[f"potential_share_ge_{th:g}"] = float((w * (freq >= th)).sum() / w.sum()); r[f"flag_ge_{th:g}"] = bool(r[f"potential_share_ge_{th:g}"] >= 0.5)
            nrow.append(r)
    N = pd.DataFrame(nrow)
    C.to_csv(a.output / "TYPHOON_EXPOSURE_BY_COUNTRY.csv", index=False); N.to_csv(a.output / "TYPHOON_EXPOSURE_BY_NODE.csv", index=False)
    summ = {f"flagged_ge_{th:g}": {t: sorted(N[(N.tech == t) & N[f"flag_ge_{th:g}"]].node.tolist()) for t in N.tech.unique()} for th in THRESHOLDS}
    flagged_mw = {f"{th:g}": N[N[f"flag_ge_{th:g}"]].groupby(["tech", "country"]).potential_mw.sum().div(1e3).round(1).reset_index().to_dict("records") for th in THRESHOLDS}
    ev = dict(method=__doc__.split("\n\n")[0], years=YEARS, threshold_kt=KT_50MS, wmo_to_1min=WMO_TO_1MIN, storms_counted=storms_used, points_ge_threshold=pts_used, wind_source_points=src_counts,
              grid=dict(x=[float(xs[0]), float(xs[-1])], y=[float(ys[0]), float(ys[-1])], dx=0.3), freq_max=float(freq.max()), default_threshold=DEFAULT, flagged=summ, flagged_potential_gw=flagged_mw)
    (a.output / "TYPHOON_EXPOSURE_S4B4.json").write_text(json.dumps(ev, indent=1, default=float))
    pd.set_option("display.width", 220)
    print("storms", storms_used, "max freq", float(freq.max()), src_counts)
    print(C.round(3).to_string(index=False))
    print(N.groupby(["tech", "country"])[[f"flag_ge_{th:g}" for th in THRESHOLDS]].sum().to_string())


if __name__ == "__main__":
    main()
