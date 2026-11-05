"""V4 S0 section 6: structure of the FfE and NREL curves, Calliope-Indonesia inventory and the quantities comparable with our ID nodes.

    python scripts/v4s0_curves.py --work <work dir> --network <integrated_2920_3h_unsolved.nc> --repo /home/jin/wt_v4_data

Read-only; writes evidence/CURVE_*.csv and evidence/CALLIOPE_INVENTORY.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads
import xarray as xr
import yaml

FFE_NAMES = {0: "Industry (total)", 1: "Iron & steel", 2: "Chemical and petrochemical", 3: "Non-ferrous metals", 4: "Non-metallic minerals", 5: "Transport equipment",
             6: "Machinery", 7: "Mining and quarrying", 8: "Food and tobacco", 9: "Paper, pulp and print", 10: "Wood and wood products", 11: "Construction",
             12: "Textile and leather", 13: "Non-specified (industry)"}
NAICS3 = {"311": "food", "312": "beverage/tobacco", "313": "textile mills", "314": "textile products", "321": "wood", "322": "paper", "324": "petroleum/coal products",
          "325": "chemicals", "326": "plastics/rubber", "327": "non-metallic minerals", "331": "primary metals", "332": "fabricated metals", "333": "machinery",
          "334": "electronics", "335": "electrical equipment", "336": "transport equipment", "337": "furniture", "339": "miscellaneous"}


def shape_stats(v: np.ndarray, idx: pd.DatetimeIndex) -> dict:
    s = pd.Series(v / v.mean(), index=idx)
    wk = s[idx.dayofweek < 5].mean(); we = s[idx.dayofweek >= 5].mean()
    mon = s.groupby(idx.month).mean(); hr = s.groupby(idx.hour).mean()
    return dict(peak_over_mean=float(s.max()), min_over_mean=float(s.min()), weekday_over_weekend=float(wk / we) if we > 0 else np.nan,
                month_max_over_min=float(mon.max() / mon.min()), diurnal_max_over_min=float(hr.max() / hr.min()), hour_of_daily_peak=int(hr.idxmax()),
                hours_below_half_mean=int((s < 0.5).sum()))


def ffe(work: Path, out: Path, R: dict):
    d = json.loads((work / "downloads/08_ffe_profiles/opendata.customization").read_text(encoding="utf-8"))
    idx = pd.date_range("2017-01-01", periods=8760, freq="h")   # reference year 2017 (metadata); the time zone is not stated in the file
    rows, vec = [], {}
    for r in d["data"]:
        i = int(r["internal_id"][0]); v = np.asarray(r["values"], dtype=float); vec[i] = v
        rows.append(dict(internal_id=i, branch=FFE_NAMES.get(i), n_values=len(v), sum_values=float(v.sum()), year=r["year"], id_region=r["id_region"], **shape_stats(v, idx)))
    T = pd.DataFrame(rows).sort_values("internal_id")
    ids = sorted(vec)
    groups, seen = [], set()
    for i in ids:
        if i in seen:
            continue
        g = [j for j in ids if np.array_equal(vec[i], vec[j])]
        seen |= set(g); groups.append(g)
    T["identical_group"] = T.internal_id.map({j: "+".join(map(str, g)) for g in groups for j in g})
    T.to_csv(out / "CURVE_FFE_STATS.csv", index=False, float_format="%.6f")
    R["ffe"] = dict(curves=len(ids), internal_ids=ids, missing_ids={k: v for k, v in FFE_NAMES.items() if k not in vec}, identical_groups=groups,
                    distinct_shapes=len(groups), normalisation="each curve sums to 1 over 8760 hourly values (share of annual energy)",
                    timestamps="none in the file; 8760 values for reference year 2017 (2017-01-01 is a Sunday); time zone not stated")


def nrel(work: Path, out: Path, R: dict):
    base = work / "extracted/09_nrel_heat"
    rows = []
    ds = pads.dataset(base / "heat_loadshapes_20190927/all_heat_loadshapes_20190927", partitioning="hive")
    t = ds.to_table(columns=["month", "dayofweek", "hour", "emp_size", "fraction_annual_energy", "hours_type", "schedule_type", "NAICS"]).to_pandas()
    t["naics"] = t.NAICS.astype(str); t["n3"] = t.naics.str[:3]
    for (n, es, ht), g in t.groupby(["naics", "emp_size", "hours_type"]):
        g = g.sort_values(["month", "dayofweek", "hour"])
        f = g.fraction_annual_energy.to_numpy()
        if len(f) != 2016:
            continue
        x = f / f.mean()
        dow = g.dayofweek.to_numpy(); mon = g.month.to_numpy(); hr = g.hour.to_numpy()
        mm = pd.Series(x).groupby(mon).mean(); hh = pd.Series(x).groupby(hr).mean()
        rows.append(dict(naics=n, naics3=n[:3], naics3_label=NAICS3.get(n[:3]), emp_size=es, hours_type=ht, schedule=g.schedule_type.iloc[0],
                         peak_over_mean=float(x.max()), min_over_mean=float(x.min()),
                         weekday_over_weekend=float(x[dow < 5].mean() / x[dow >= 5].mean()) if x[dow >= 5].mean() > 0 else np.nan,
                         month_max_over_min=float(mm.max() / mm.min()), diurnal_max_over_min=float(hh.max() / hh.min()) if hh.min() > 0 else np.inf))
    P = pd.DataFrame(rows); P.to_csv(out / "CURVE_NREL_PARQUET_STATS.csv", index=False, float_format="%.5f")
    agg = P.groupby(["naics3", "naics3_label"])[["peak_over_mean", "min_over_mean", "weekday_over_weekend", "month_max_over_min"]].median()
    agg["shapes"] = P.groupby(["naics3", "naics3_label"]).size()
    agg.to_csv(out / "CURVE_NREL_BY_NAICS3.csv", float_format="%.4f")
    csvs = {}
    for k in ("process_heat", "boiler"):
        c = pd.read_csv(base / f"all_load_shapes_{k}_decompressed/all_load_shapes_{k}.csv", usecols=["month", "dayofweek", "hour", "Weekly_op_hours", "naics", "Emp_Size"])
        csvs[k] = dict(rows=int(len(c)), naics=int(c.naics.nunique()), emp_sizes=sorted(c.Emp_Size.astype(str).unique().tolist()),
                       rows_per_naics_size=int(c.groupby(["naics", "Emp_Size"]).size().median()),
                       weekly_op_hours_range=[float(c.Weekly_op_hours.min()), float(c.Weekly_op_hours.max())])
    R["nrel"] = dict(parquet_partitions=int(t.naics.nunique()), parquet_rows=int(len(t)), emp_sizes=sorted(t.emp_size.unique().tolist()),
                     hours_types=sorted(t.hours_type.astype(str).unique().tolist()), schedules=sorted(t.schedule_type.astype(str).unique().tolist()),
                     structure="typical week per month: 12 months x 7 days x 24 h = 2016 steps per (NAICS, employment size, hours type); value = fraction of annual energy",
                     csv=csvs, naics3_present=sorted(t.n3.unique().tolist()))


def calliope(work: Path, net: Path, repo: Path, out: Path, R: dict):
    C = next((work / "extracted/11_calliope_indonesia").glob("*/calliope_indonesia"))
    loc = yaml.safe_load((C / "model_config/locations.yaml").read_text(encoding="utf-8"))["locations"]
    pot = {}
    for name, v in loc.items():
        for tech, tv in ((v or {}).get("techs") or {}).items():
            cons = (tv or {}).get("constraints") or {}
            for key in ("energy_cap_max", "energy_cap_equals", "energy_cap_min"):
                if key in cons and isinstance(cons[key], (int, float)):
                    pot.setdefault(tech, {}).setdefault(key, 0.0); pot[tech][key] += float(cons[key])
    links = {}
    for f in ("links_with_interconnection.yaml", "links_without_interconnection.yaml"):
        links[f] = len((yaml.safe_load((C / "model_config" / f).read_text(encoding="utf-8")) or {}).get("links") or {})
    dem = {}
    for f in sorted((C / "timeseries_data").glob("Demand_Profiles_*.csv")):
        d = pd.read_csv(f, index_col=0)
        dem[f.name] = dict(hours=int(len(d)), provinces=int(d.shape[1]), total_twh=float(-d.sum().sum() / 1e6), peak_gw=float(-d.sum(axis=1).min() / 1e3),
                           first=str(d.index[0]), last=str(d.index[-1]))
    d50 = pd.read_csv(C / "timeseries_data/Demand_Profiles_2050_MAY_RUPTL.csv", index_col=0)
    prov = (-d50.sum() / 1e6).rename("twh_2050_may_ruptl")
    prov.to_csv(out / "CALLIOPE_DEMAND_2050_BY_PROVINCE.csv", float_format="%.4f")
    # our ID electricity loads on AC nodes (F1 network): static p_set x 8760 + time series x weights
    ds = xr.open_dataset(net)
    L = pd.DataFrame({k[6:]: ds[k].values for k in ("loads_bus", "loads_carrier", "loads_p_set", "loads_country")}, index=ds["loads_i"].values)
    B = pd.DataFrame({k[6:]: ds[k].values for k in ("buses_carrier", "buses_country")}, index=ds["buses_i"].values)
    ac = set(B[(B.carrier == "AC") & (B.country == "ID")].index)
    w = ds["snapshots_generators"].values
    stat = L[L.bus.isin(ac)]
    ts_names = [str(x) for x in ds["loads_t_p_set_i"].values]
    ts = ds["loads_t_p_set"].to_pandas() if len(ts_names) else pd.DataFrame()
    ts.columns = ts_names
    ts_id = [c for c in ts.columns if c in stat.index]
    ts_twh = float((ts[ts_id].mul(w, axis=0)).sum().sum() / 1e6) if ts_id else 0.0
    static_twh = float(stat[~stat.index.isin(ts_id)].p_set.astype(float).sum() * 8760 / 1e6)
    by_car = stat.assign(twh=lambda q: q.p_set.astype(float) * 8760 / 1e6).groupby("carrier").twh.sum()
    for c in ts_id:
        by_car[stat.at[c, "carrier"]] = by_car.get(stat.at[c, "carrier"], 0.0) - float(stat.at[c, "p_set"]) * 8760 / 1e6 + float((ts[c] * w).sum() / 1e6)
    R["calliope"] = dict(path=str(C.relative_to(work)), calliope_version="0.6.8 (model.yaml)", locations=len(loc), techs_with_caps=pot, links=links, demand_files=dem,
                         licence="none in the repository; ask before citing",
                         our_id_ac_node_electricity_loads_twh=dict(static=static_twh, time_series=ts_twh, total=static_twh + ts_twh, by_carrier=by_car.round(3).to_dict(),
                                                                   ac_nodes=len(ac), note="F1 integrated 2920x3h network; fixed loads only (no electrolysis, heat pumps, DAC)"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); ap.add_argument("--network", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True); a = ap.parse_args()
    out = a.work / "evidence"; R = {}
    ffe(a.work, out, R); print("ffe", flush=True)
    nrel(a.work, out, R); print("nrel", flush=True)
    calliope(a.work, a.network, a.repo, out, R); print("calliope", flush=True)
    (out / "CURVES_AND_CALLIOPE.json").write_text(json.dumps(R, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
