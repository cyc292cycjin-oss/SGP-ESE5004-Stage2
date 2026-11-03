"""V3 supplement 06 items 1-2, read-only: EV battery e_nom, participation, e_min_pu and charger p_max_pu as stored in the 2920x3h, 365x24h and
56-snapshot networks (xarray, only the needed variables; no solver, no network written)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

W = Path("/home/jin/wt_v3_20261102"); OUT = W / "research/06_scope_redesign/p1_v3_20261102/evidence/evdiag"; OUT.mkdir(parents=True, exist_ok=True)
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
X = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export")
NETS = {"2920x3h integrated (unsolved)": R / "builds_op/integrated/integrated_2920_3h_unsolved.nc",
        "2920x3h no_new_xb (unsolved)": R / "builds_op/no_new_xb/no_new_xb_2920_3h_unsolved.nc",
        "365x24h integrated (unsolved)": R / "builds_op/integrated/integrated_365_24h_unsolved.nc",
        "365x24h V1 (solved)": X / "V1/integrated_DFX_365X24H_solved.nc",
        "365x24h V2 no_new_xb (solved)": X / "V2/no_new_xb_DFX_365X24H_solved.nc",
        "56 smoke s5 integrated (solved)": R / "smoke_s5/integrated/integrated_SMOKE_TEST_ONLY_solved.nc",
        "56 smoke s1 integrated E2 (solved)": R / "smoke_s1/integrated/integrated_SMOKE_TEST_ONLY_solved.nc"}
TZ = pd.read_csv(W / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node")
REG = pd.read_csv(W / "research_inputs/registry_v5/DATA_REGISTRY.csv", low_memory=False)
KEY = [c for c in REG.columns if REG[c].astype(str).eq("share_bev_dsm_restriction_value").any()][0]
REG = REG.drop_duplicates(KEY).set_index(KEY)
RV = {k: float(REG.at[k, "value"]) for k in ("share_bev_dsm_restriction_value", "share_bev_dsm_restriction_time", "share_bev_dsm_availability", "share_bev_energy", "share_bev_charge_rate",
                                             "share_bev_charge_efficiency", "ev_annual_km_per_vehicle", "share_transport_electric_efficiency")}


def snaps(ds):
    """PyPSA writes the snapshot positions as `snapshots` and the timestamps as `snapshots_snapshot`."""
    idx = pd.DatetimeIndex(pd.to_datetime(ds["snapshots_snapshot"].values), name="snapshot")
    if idx[0] != pd.Timestamp("2013-01-01") or len(idx) not in (56, 365, 2920):
        raise ValueError("unexpected snapshots " + str(idx[:3]))
    return idx


def tframe(ds, comp, attr):
    v = f"{comp}_t_{attr}"
    idx = snaps(ds)
    return pd.DataFrame(ds[v].values, index=idx, columns=ds[v + "_i"].values.astype(str)) if v in ds else pd.DataFrame(index=idx)


def static(ds, comp, attr):
    return pd.Series(ds[f"{comp}_{attr}"].values, index=ds[f"{comp}_i"].values.astype(str))


summary, rows, timing, country = {}, [], [], None
for label, path in NETS.items():
    if not path.exists():
        summary[label] = "missing: " + str(path); continue
    ds = xr.open_dataset(path)
    st = [s for s in ds["stores_i"].values.astype(str) if s.endswith(" EV battery store")]
    w = pd.Series(ds["snapshots_stores"].values, index=snaps(ds)); hours = float(w.iloc[0])
    e_nom = static(ds, "stores", "e_nom")[st]
    emin = tframe(ds, "stores", "e_min_pu").reindex(columns=st)
    if emin.isna().all().all():
        emin = pd.DataFrame(np.tile(static(ds, "stores", "e_min_pu")[st].to_numpy(), (len(w), 1)), index=w.index, columns=st)
    day = emin.index.normalize()
    nz_per_day = emin.gt(0).groupby(day).sum(); mean_day = emin.groupby(day).mean(); max_day = emin.groupby(day).max()
    nodes = [s[: -len(" EV battery store")] for s in st]
    ch = [f"{nd} BEV charger" for nd in nodes]
    pmax = tframe(ds, "links", "p_max_pu").reindex(columns=ch)
    ld = [f"{nd} land transport EV" for nd in nodes]
    pset = tframe(ds, "loads", "p_set").reindex(columns=ld)
    wg = pd.Series(ds["snapshots_generators"].values, index=w.index)
    summary[label] = dict(file=str(path), snapshots=int(len(w)), hours_per_snapshot=hours, ev_stores=len(st), e_nom_total_twh=float(e_nom.sum() / 1e6),
                          e_min_pu_distinct=sorted({round(float(x), 12) for x in np.unique(emin.to_numpy())}),
                          nonzero_e_min_snapshots_per_utc_day=sorted({int(x) for x in np.unique(nz_per_day.to_numpy())}),
                          daily_mean_e_min_pu=[float(mean_day.to_numpy().min()), float(mean_day.to_numpy().max())],
                          daily_max_e_min_pu=[float(max_day.to_numpy().min()), float(max_day.to_numpy().max())],
                          charger_p_max_pu=dict(min=float(np.nanmin(pmax.to_numpy())), mean=float(np.nanmean(pmax.to_numpy())), max=float(np.nanmax(pmax.to_numpy()))) if pmax.notna().any().any() else None,
                          charger_p_nom_gw=float(static(ds, "links", "p_nom")[ch].sum() / 1e3),
                          ev_load_twh=float(pset.mul(wg, axis=0).sum().sum() / 1e6) if pset.notna().any().any() else None,
                          e_cyclic=sorted({bool(x) for x in static(ds, "stores", "e_cyclic")[st]}))
    rows.append(dict(network=label, **{k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in summary[label].items() if k != "file"}))
    if hours == 3.0:
        for s, nd in zip(st, nodes):
            hit = emin.index[emin[s].gt(0)]
            off = float(TZ.at[nd, "utc_offset_h"]); h = sorted(set(hit.hour))
            timing.append(dict(network=label, store=s, utc_offset_h=off, hit_utc_hours=";".join(map(str, h)), local_start=";".join(str((x + off) % 24) for x in h), local_end_of_snapshot=";".join(str((x + 3 + off) % 24) for x in h), hits=len(hit)))
    if label == "365x24h V1 (solved)":
        cty = static(ds, "stores", "country")[st] if "stores_country" in ds else pd.Series([TZ.at[n, "country"] for n in nodes], index=st)
        p_nom = static(ds, "links", "p_nom")[ch]; N = p_nom.to_numpy() / RV["share_bev_charge_rate"]
        load = pset.mul(wg, axis=0).sum().to_numpy()
        df = pd.DataFrame(dict(store=st, node=nodes, country=cty.to_numpy(), e_nom_mwh=e_nom.to_numpy(), charger_mw=p_nom.to_numpy(), fleet_equiv=N, ev_load_mwh=load))
        df["participation"] = df.e_nom_mwh / (df.fleet_equiv * RV["share_bev_energy"])
        df.to_csv(OUT / "EV_STORES_V1.csv", index=False)
        g = df.groupby("country").agg(stores=("store", "size"), e_nom_twh=("e_nom_mwh", lambda x: x.sum() / 1e6), charger_gw=("charger_mw", lambda x: x.sum() / 1e3), fleet_m=("fleet_equiv", lambda x: x.sum() / 1e6),
                                      ev_load_twh=("ev_load_mwh", lambda x: x.sum() / 1e6))
        g.loc["合计"] = g.sum(); g["days_of_ev_load"] = g.e_nom_twh / (g.ev_load_twh / 365.0); g["participation"] = g.e_nom_twh * 1e6 / (g.fleet_m * 1e6 * RV["share_bev_energy"])
        g.to_csv(OUT / "EV_ENOM_BY_COUNTRY_V1.csv"); country = g
        meta = json.loads(ds.attrs.get("meta", "{}")) if isinstance(ds.attrs.get("meta"), str) else {}
        summary["V1_meta_research_ev"] = meta.get("research_ev")
    ds.close()

# hourly definition (registry rows; PyPSA-Earth prepare_transport_data.py: value at the restriction hour of each local day, 0 otherwise)
v, h = RV["share_bev_dsm_restriction_value"], RV["share_bev_dsm_restriction_time"]
hourly = np.zeros(24); hourly[int(h)] = v
summary["hourly_definition"] = dict(registry=RV, nonzero_hours_per_day=1, value=v, local_hour=h, daily_mean=float(hourly.mean()), daily_max=float(hourly.max()),
                                    upstream_max_rule_3h=dict(nonzero_snapshots_per_day=1, value=v), upstream_max_rule_24h=dict(value_every_day=v),
                                    mean_rule_24h_from_3h=dict(value_every_day=v / 8.0), mean_rule_24h_from_1h=dict(value_every_day=v / 24.0))
pd.DataFrame(rows).to_csv(OUT / "EMIN_STATS.csv", index=False)
t = pd.DataFrame(timing); t.to_csv(OUT / "EMIN_3H_TIMING.csv", index=False)
summary["timing_by_offset"] = t.groupby(["network", "utc_offset_h", "hit_utc_hours", "local_start", "local_end_of_snapshot"]).size().reset_index(name="stores").to_dict("records") if len(t) else []
(OUT / "EV_DATA_V3.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str) + "\n")
pd.set_option("display.width", 250, "display.max_columns", 30)
print(pd.DataFrame(rows).drop(columns=["e_cyclic"]).to_string())
print(json.dumps(summary["timing_by_offset"], ensure_ascii=False)[:1500])
print(country.round(4).to_string() if country is not None else "no V1")
print(json.dumps(summary["hourly_definition"], ensure_ascii=False))
print(json.dumps(summary.get("V1_meta_research_ev"), ensure_ascii=False)[:800])
