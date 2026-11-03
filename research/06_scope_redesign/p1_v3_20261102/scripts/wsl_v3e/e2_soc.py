"""V3 supplement 06 items 3 and 5, read-only: EV battery state of charge in the solved V1 / V2 (365x24h) and the 56-snapshot smokes:
SOC = e / e_nom, days below the 0.8 morning floor, longest run, throughput, equivalent cycles, cross-day transfer, and the storage rent
sum_t lambda_t * w_obj * (e_{t-1} - e_t) / w_store (lambda = nodal price of the EV battery bus; cyclic e_0 = e_T). No solver."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

W = Path("/home/jin/wt_v3_20261102"); OUT = W / "research/06_scope_redesign/p1_v3_20261102/evidence/evdiag"
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3")
X = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v3_20261102/cloud_results/final_20261103T063207Z/full_unpacked/export")
NETS = {"V1": X / "V1/integrated_DFX_365X24H_solved.nc", "V2": X / "V2/no_new_xb_DFX_365X24H_solved.nc",
        "smoke_s5_integrated": R / "smoke_s5/integrated/integrated_SMOKE_TEST_ONLY_solved.nc", "smoke_s5_no_new_xb": R / "smoke_s5/no_new_xb/no_new_xb_SMOKE_TEST_ONLY_solved.nc",
        "smoke_s1_integrated_E2": R / "smoke_s1/integrated/integrated_SMOKE_TEST_ONLY_solved.nc"}
FLOOR = 0.8; TOL = 1e-6


def snaps(ds):
    return pd.DatetimeIndex(pd.to_datetime(ds["snapshots_snapshot"].values), name="snapshot")


def tframe(ds, comp, attr, cols):
    v = f"{comp}_t_{attr}"; names = ds[v + "_i"].values.astype(str); pos = {s: i for i, s in enumerate(names)}
    return pd.DataFrame(ds[v].values[:, [pos[c] for c in cols]], index=snaps(ds), columns=cols)


def runs_below(mask):
    """longest run of True, linear and circular (the year is cyclic)."""
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0; best = max(best, cur)
    if mask.all():
        return len(mask), len(mask)
    head = int(np.argmin(mask)); tail = int(np.argmin(mask[::-1]))
    return best, max(best, head + tail)


summary, store_rows, daily = {}, [], None
for label, path in NETS.items():
    ds = xr.open_dataset(path)
    st = sorted(s for s in ds["stores_i"].values.astype(str) if s.endswith(" EV battery store")); nodes = [s[: -len(" EV battery store")] for s in st]
    e_nom = pd.Series(ds["stores_e_nom"].values, index=ds["stores_i"].values.astype(str))[st]
    e = tframe(ds, "stores", "e", st); emin = tframe(ds, "stores", "e_min_pu", st)
    w_st = pd.Series(ds["snapshots_stores"].values, index=e.index); w_obj = pd.Series(ds["snapshots_objective"].values, index=e.index)
    lam = tframe(ds, "buses", "marginal_price", [f"{n} EV battery" for n in nodes]); lam.columns = st
    soc = e / e_nom
    prev = e.shift(1); prev.iloc[0] = e.iloc[-1]; de = e - prev                        # cyclic
    rent = float((lam.mul(w_obj, axis=0) * (-de).div(w_st, axis=0)).sum().sum())
    floor_rows = emin.gt(0.5 * FLOOR)                                                   # 3 h: the morning snapshot; daily: none (0.1)
    daily_res = float(w_st.iloc[0]) == 24.0
    ac = [b for b in ds["buses_t_marginal_price_i"].values.astype(str) if b.endswith(" 0") and " " in b][:5]
    res = dict(file=str(path), snapshots=int(len(e)), w_store_h=float(w_st.iloc[0]), w_objective_h=float(w_obj.iloc[0]), e_nom_twh=float(e_nom.sum() / 1e6),
               e_min_pu_values=sorted({round(float(x), 10) for x in np.unique(emin.to_numpy())}),
               soc_min_store=float(soc.min().min()), soc_max_store=float(soc.max().max()),
               ev_battery_price_mean_eur_mwh=float(lam.to_numpy().mean()), sample_ac_price_mean=float(tframe(ds, "buses", "marginal_price", ac).to_numpy().mean()) if ac else None,
               storage_rent_bn_eur=rent / 1e9)
    E = e.sum(axis=1); En = float(e_nom.sum()); Ep = E.shift(1); Ep.iloc[0] = E.iloc[-1]; dE = E - Ep
    if daily_res:
        below = soc.lt(FLOOR - TOL)
        res.update(store_days_below_floor_share=float(below.to_numpy().mean()), store_days_below_floor_share_enom_weighted=float((below * e_nom).to_numpy().sum() / (En * len(e))),
                   store_days_at_0p1=float(soc.le(0.1 + 1e-4).to_numpy().mean()),
                   system_soc_min=float(E.min() / En), system_soc_max=float(E.max() / En), system_days_below_floor=int((E / En).lt(FLOOR - TOL).sum()),
                   system_longest_run_below_floor=runs_below((E / En).lt(FLOOR - TOL).to_numpy()),
                   throughput_twh=float(de.clip(lower=0).sum().sum() / 1e6), equivalent_cycles=float(de.clip(lower=0).sum().sum() / En),
                   cross_day_transfer_twh_sum_of_stores=float(de.clip(lower=0).sum().sum() / 1e6), cross_day_transfer_twh_system=float(dE.clip(lower=0).sum() / 1e6),
                   cross_day_limit_twh_floor_0p1=0.9 * En / 1e6, cross_day_limit_twh_floor_0p8=0.2 * En / 1e6, max_swing_share_of_enom=float(((e.max() - e.min()) / e_nom).max()),
                   max_swing_system_share=float((E.max() - E.min()) / En))
        for s, nd in zip(st, nodes):
            b = soc[s].lt(FLOOR - TOL).to_numpy(); lin, circ = runs_below(b)
            store_rows.append(dict(run=label, store=s, node=nd, e_nom_mwh=float(e_nom[s]), soc_min=float(soc[s].min()), soc_max=float(soc[s].max()), days_below_0p8=int(b.sum()),
                                   share_below_0p8=float(b.mean()), longest_run_below_0p8_linear=lin, longest_run_below_0p8_circular=circ, days_at_0p1=int(soc[s].le(0.1 + 1e-4).sum()),
                                   throughput_mwh=float(de[s].clip(lower=0).sum()), equivalent_cycles=float(de[s].clip(lower=0).sum() / e_nom[s]), rent_eur=float((lam[s] * w_obj * (-de[s]) / w_st).sum())))
        if label == "V1":
            daily = pd.DataFrame(dict(system_e_twh=E / 1e6, system_soc=E / En, delta_twh=dE / 1e6, price_mean_ev_bus=lam.mean(axis=1)))
            daily.to_csv(OUT / "EV_SOC_V1_DAILY.csv")
            m = daily.groupby(daily.index.month).agg(soc_mean=("system_soc", "mean"), soc_min=("system_soc", "min"), soc_max=("system_soc", "max"), charge_twh=("delta_twh", lambda x: x.clip(lower=0).sum()),
                                                      discharge_twh=("delta_twh", lambda x: -x.clip(upper=0).sum()), price=("price_mean_ev_bus", "mean"))
            m.to_csv(OUT / "EV_SOC_V1_MONTHLY.csv"); res["monthly"] = m.round(4).to_dict("index")
            res["corr_daily_delta_vs_price"] = float(np.corrcoef(dE.to_numpy(), lam.mean(axis=1).to_numpy())[0, 1])
    else:
        mor = soc.where(floor_rows)                                                     # SOC at the morning floor snapshots
        mor_e = e.where(floor_rows); md = []
        for s in st:
            x = mor_e[s].dropna().to_numpy(); d = np.diff(np.r_[x[-1], x]); md.append(np.clip(d, 0, None).sum())
        res.update(floor_snapshots_per_store=int(floor_rows.sum().iloc[0]), morning_soc_min=float(mor.min().min()), morning_soc_mean=float(np.nanmean(mor.to_numpy())),
                   morning_floor_binding_share=float((mor.lt(FLOOR + 1e-4) & mor.notna()).to_numpy().sum() / floor_rows.to_numpy().sum()),
                   morning_violations=int((mor.lt(FLOOR - 1e-6) & mor.notna()).to_numpy().sum()),
                   throughput_twh_per_window=float(de.clip(lower=0).sum().sum() / 1e6), morning_to_morning_positive_twh_per_window=float(sum(md) / 1e6),
                   power_shift_limit_gw=float(e_nom.sum() / w_st.iloc[0] / 1e3), annualise_factor=8760.0 / float(w_obj.sum()) if float(w_obj.sum()) < 8000 else 1.0,
                   soc_any_snapshot_below_0p8_share=float(soc.lt(FLOOR - TOL).to_numpy().mean()))
        x = (E / En).to_numpy(); res["system_soc_by_snapshot"] = [round(float(v), 4) for v in x]
    summary[label] = res
    ds.close()

pd.DataFrame(store_rows).to_csv(OUT / "EV_SOC_BY_STORE_365.csv", index=False)
(OUT / "EV_SOC_SUMMARY.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str) + "\n")
for k, v in summary.items():
    print("==", k, json.dumps({a: b for a, b in v.items() if a not in ("monthly", "file", "system_soc_by_snapshot")}, ensure_ascii=False, default=str))
print(json.dumps(summary["V1"].get("monthly"), ensure_ascii=False)[:1600])
print("smoke s5 system soc", summary["smoke_s5_integrated"]["system_soc_by_snapshot"])
t = pd.DataFrame(store_rows); print(t[t.run == "V1"].describe().round(3).to_string())
