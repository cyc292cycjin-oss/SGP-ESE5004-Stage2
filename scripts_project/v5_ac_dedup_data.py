"""V5 X20 revision 2-2 (decision 244; X20_SPEC.md 1.9; decision 246 Q6 (a)): domestic AC corridor correction table AC_DEDUP_V5.csv.

OSM prebuilt 0.1.1 (data/osm-plus-prebuilt/0.1.1/all_lines_build_network.csv) holds groups of identical rows (same way id, sorted end buses, voltage,
length rounded to 1 m), each with the full circuit count (X10 section 1(d): MY 294 ways in 3-4 rows each). Per OSM row the author chain sets
s_nom = sqrt(3) x i_nom(line type of the nearest voltage key, config.default.yaml lines.ac_types) x kV x circuits (base_network.py), and the cluster
step sums the rows between two clusters. This script
  1. maps every OSM bus to the nearest model AC node of the same country (lon / lat Euclidean, as X10 04b_x10_ac_reconstruct.py). The author busmap
     of the 100-node base is not available locally (only the tutorial elec_s_50 busmaps), and the S4A regions_onshore.geojson is the per-country
     Voronoi partition of the node coordinates (s4a_profiles.node_regions), i.e. the same nearest-node rule (X20 B finding, correcting X20_SPEC 1.9);
  2. sums per model node pair: counted (all rows), dedup_only (one row per duplicate group), dedup_cables (one row per group, circuits = OSM API tag
     cables / 3 where the tag exists and cables is a positive multiple of 3, research_inputs/corridors/OSM_WAY_TAGS_V5.csv);
  3. for every domestic stock line of the model (s_nom_min > 0, both ends in one country) with at least one duplicate row: factor = dedup / counted;
     applied only when counted / model s_nom is within [0.8, 1.25] (reconstruction check), otherwise listed with applied = False (limitation).
Inputs: --network (a built v4 network, lines and buses read through xarray only), --tags (OSM_WAY_TAGS_V5.csv).
    python scripts_project/v5_ac_dedup_data.py --network <integrated_2920_3h_unsolved.nc> --tags research_inputs/corridors/OSM_WAY_TAGS_V5.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OSM = ROOT / "data/osm-plus-prebuilt/0.1.1"

OUT = ROOT / "research_inputs/corridors/AC_DEDUP_V5.csv"
AC_TYPES = {132.: "243-AL1/39-ST1A 110.0", 220.: "Al/St 240/40 2-bundle 220.0", 275.: "Al/St 240/40 3-bundle 300.0",
            300.: "Al/St 240/40 3-bundle 300.0", 330.: "Al/St 240/40 4-bundle 380.0", 380.: "Al/St 240/40 4-bundle 380.0",
            500.: "Al/St 240/40 4-bundle 380.0", 750.: "Al/St 560/50 4-bundle 750.0"}   # config.default.yaml lines.ac_types.default (as X10 04b)
CHECK = (0.8, 1.25)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def model_tables(nc: Path):
    ds = xr.open_dataset(nc)
    def comp(c, attrs):
        idx = ds[f"{c}_i"].values.astype(str)
        return pd.DataFrame({a: ds[f"{c}_{a}"].values for a in attrs if f"{c}_{a}" in ds}, index=idx)
    buses = comp("buses", ["x", "y", "country", "carrier"]); lines = comp("lines", ["bus0", "bus1", "s_nom", "s_nom_min", "type", "num_parallel"])
    ds.close()
    for c in ("country", "carrier"):
        buses[c] = buses[c].astype(str)
    for c in ("bus0", "bus1", "type"):
        lines[c] = lines[c].astype(str)
    return buses, lines


def main(argv=None):
    import pypsa
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--tags", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=OUT); a = ap.parse_args(argv)
    lt = pd.read_csv(Path(pypsa.__file__).parent / "standard_types/line_types.csv", index_col=0)
    inom = {t: float(lt.loc[t, "i_nom"]) for t in set(AC_TYPES.values())}
    B = pd.read_csv(OSM / "all_buses_build_network.csv", index_col=0, dtype={"bus_id": str}).set_index("bus_id")
    L = pd.read_csv(OSM / "all_lines_build_network.csv", index_col=0, dtype={"line_id": str, "bus0": str, "bus1": str})
    L = L[~L["dc"].astype(str).str.lower().isin(["true", "1"])].copy()
    L["kv"] = L.voltage / 1000.0
    L["type"] = L.kv.map(lambda v: AC_TYPES[min(AC_TYPES, key=lambda k: abs(k - v))])
    L["way"] = L.line_id.str.split("-").str[0]
    L["key"] = list(zip(L.way, L[["bus0", "bus1"]].min(1), L[["bus0", "bus1"]].max(1), L.voltage, L.length.round(0)))
    L["dup_n"] = L.key.map(L.key.value_counts()); L["keep"] = ~L.duplicated("key")
    tags = pd.read_csv(a.tags, dtype={"way": str}).set_index("way")
    cab = pd.to_numeric(tags.cables, errors="coerce")
    circ_api = (cab / 3).where((cab > 0) & (cab % 3 == 0))
    L["circuits_api"] = L.way.map(circ_api)
    L["s_counted"] = np.sqrt(3) * L.type.map(inom) * L.kv * L.circuits
    L["s_dedup_only"] = np.where(L.keep, L.s_counted, 0.0)
    use_api = L.keep & (L.dup_n > 1) & L.circuits_api.notna()
    L["s_dedup_cables"] = np.where(L.keep, np.where(use_api, np.sqrt(3) * L.type.map(inom) * L.kv * L.circuits_api, L.s_counted), 0.0)
    L["cables_used"] = use_api
    # OSM bus -> model node: onshore region of the same country, else nearest node of the country
    buses, lines = model_tables(a.network)
    ac = buses[(buses.carrier == "AC") & ~buses.index.str.contains("dedicated|EV|low voltage", regex=True)]
    busmap, how = {}, {}
    for cc, g in B.groupby("country"):
        cand = ac[ac.country == cc]
        if cand.empty:
            continue
        xy = cand[["x", "y"]].values.astype(float)
        for bid, r in g.iterrows():
            d = (xy[:, 0] - r.lon) ** 2 + (xy[:, 1] - r.lat) ** 2
            busmap[bid] = cand.index[int(np.argmin(d))]; how[bid] = "nearest_same_country"
    L["m0"] = L.bus0.map(busmap); L["m1"] = L.bus1.map(busmap)
    X = L.dropna(subset=["m0", "m1"]); X = X[X.m0 != X.m1].copy()
    X["pair"] = ["|".join(sorted(p)) for p in zip(X.m0, X.m1)]
    agg = X.groupby("pair").agg(counted=("s_counted", "sum"), dedup_only=("s_dedup_only", "sum"), dedup_cables=("s_dedup_cables", "sum"),
                                rows=("line_id", "size"), dup_rows=("dup_n", lambda s: int((s > 1).sum())), cables_rows=("cables_used", "sum"),
                                ways=("way", lambda s: ";".join(sorted(set(s)))))
    rows = []
    for k, r in lines.iterrows():
        c0, c1 = buses.country.get(r.bus0), buses.country.get(r.bus1)
        if float(r.s_nom_min) <= 0 or c0 != c1:
            continue
        pr = "|".join(sorted((r.bus0, r.bus1)))
        if pr not in agg.index or agg.at[pr, "dup_rows"] == 0:
            continue
        g = agg.loc[pr]
        ratio = g.counted / float(r.s_nom)
        ok = CHECK[0] <= ratio <= CHECK[1]
        rows.append(dict(line=k, bus0=r.bus0, bus1=r.bus1, country=c0, frozen_s_nom_mw=float(r.s_nom), osm_counted_mw=float(g.counted),
                         osm_dedup_only_mw=float(g.dedup_only), osm_dedup_cables_mw=float(g.dedup_cables), recon_over_model=float(ratio),
                         factor_dedup_only=float(g.dedup_only / g.counted), factor_dedup_cables=float(g.dedup_cables / g.counted),
                         osm_rows=int(g.rows), osm_dup_rows=int(g.dup_rows), osm_rows_cables_tag=int(g.cables_rows), applied=bool(ok),
                         note=("" if ok else f"reconstruction check failed: counted / model = {ratio:.3f} outside {CHECK}; not changed (limitation)"),
                         osm_ways=g.ways))
    T = pd.DataFrame(rows).sort_values(["country", "line"])
    T["new_s_nom_dedup_only_mw"] = np.where(T.applied, T.frozen_s_nom_mw * T.factor_dedup_only, T.frozen_s_nom_mw)
    T["new_s_nom_dedup_cables_mw"] = np.where(T.applied, T.frozen_s_nom_mw * T.factor_dedup_cables, T.frozen_s_nom_mw)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    T.to_csv(a.output, index=False, lineterminator="\n")   # full precision: the build multiplies the frozen s_nom by the factor
    log = dict(script="scripts_project/v5_ac_dedup_data.py", network=str(a.network), network_sha256=sha(a.network), tags=str(a.tags), tags_sha256=sha(a.tags),
               osm_lines_sha256=sha(OSM / "all_lines_build_network.csv"), osm_buses_sha256=sha(OSM / "all_buses_build_network.csv"),
               bus_mapping={k: int(v) for k, v in pd.Series(how).value_counts().items()}, dup_groups=int((L[L.dup_n > 1].key.nunique())),
               lines=len(T), applied=int(T.applied.sum()), by_country=T.groupby("country").agg(lines=("line", "size"), applied=("applied", "sum"),
               frozen=("frozen_s_nom_mw", "sum"), dedup_cables=("new_s_nom_dedup_cables_mw", "sum")).round(1).to_dict("index"))
    a.output.with_suffix(".json").write_text(json.dumps(log, indent=1, default=str))
    print(T[["line", "country", "frozen_s_nom_mw", "recon_over_model", "factor_dedup_only", "factor_dedup_cables", "applied"]].to_string(index=False))
    print(json.dumps({k: v for k, v in log.items() if k in ("bus_mapping", "dup_groups", "lines", "applied")}))


if __name__ == "__main__":
    main()
