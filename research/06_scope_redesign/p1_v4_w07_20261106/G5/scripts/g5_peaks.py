"""G5 step 4: effect of the proposed profiles on industrial load peaks (annual energy unchanged), v3 2050 quantities. Read-only, no solve.

    PYTHONHASHSEED=0 python g5_peaks.py --s0 <work/p1_v4_data_20261105> --repo /home/jin/wt_v4_g5 --network <F1 integrated_2920_3h_unsolved.nc> --g5 <G5 dir>

Quantities: v3 INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv case main (electricity; heat bands heat / heat_high / heat_medium_a / heat_medium_b);
dispersed split to PyPSA-Eur sectors by the S0 table V3_DISPERSED_BY_UNSD_ROW.csv (row energy, all carriers, used as weights for every carrier: INFERENCE);
ID split to UTC+7 / +8 / +9 with INDUSTRY_NODE_SHARES_V3.csv (ammonia uses the petrochem shares).
Country fixed AC load at 3 h = network 'electricity' time series + static 'agriculture machinery electric' + 'industry electricity' (EV, electrolysis,
heat pumps and other endogenous loads excluded).
Writes evidence/G5_PEAK_IMPACT.csv, evidence/G5_HEAT_PEAKS.csv, evidence/G5_INDUSTRY_COMPOSITION.csv, evidence/G5_PEAKS.json, evidence/fig_g5_*.png.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

V3_KEY = {"steel": "steel", "cement": "cement", "ammonia": "ammonia", "nonferrous_nickel": "nickel", "nonferrous_aluminium_primary": "aluminium_primary",
          "nonferrous_alumina": "alumina", "nonferrous_copper": "copper", "other": "other"}
SHARE_KEY = {"ammonia": "petrochem"}
HEAT = ["heat", "heat_high", "heat_medium_a", "heat_medium_b"]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--s0", type=Path, required=True); ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--network", type=Path, required=True); ap.add_argument("--g5", type=Path, required=True); a = ap.parse_args()
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from g5_profiles import SECTOR_KEY
    ev = a.g5 / "evidence"; R = dict(script="scripts/g5_peaks.py")
    P = pd.read_parquet(a.g5 / "PROFILES_8760.parquet"); I = pd.read_csv(a.g5 / "PROFILE_INDEX.csv")
    T = pd.read_csv(a.repo / "research_inputs/industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); T = T[T.case == "main"]
    NS = pd.read_csv(a.repo / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    TZ = pd.read_csv(a.repo / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    D = pd.read_csv(a.s0 / "evidence/V3_DISPERSED_BY_UNSD_ROW.csv"); D["key"] = D.pypsa_eur_sector.map(SECTOR_KEY)
    # ---- composition: country x zone x key x etype (MWh/a)
    rows, notes = [], []
    for _, r in T.iterrows():
        et = "elec" if r.carrier == "electricity" else ("heat" if r.carrier in HEAT else None)
        if et is None or r.mwh_2050 == 0:
            continue
        c = r.country
        if r.subsector == "dispersed":
            d = D[D.country == c]
            if len(d) and d.twh_2050.sum() > 0:
                parts = (d.groupby("key").twh_2050.sum() / d.twh_2050.sum()).to_dict()
            else:
                parts = {"other": 1.0}; notes.append(f"{c} dispersed {r.carrier} {r.mwh_2050:.0f} MWh: no row split in S0 table -> 'other' shape")
        else:
            parts = {V3_KEY[r.subsector]: 1.0}
        if c == "ID":
            ns = NS[(NS.country == "ID") & (NS.subsector == SHARE_KEY.get(r.subsector, r.subsector))]
            if ns.empty:
                raise ValueError("no ID node shares for " + r.subsector)
            zs = ns.assign(z=ns.node.map(TZ)).groupby("z").share.sum()
            zs = zs / zs.sum()
        else:
            zs = pd.Series({float(TZ[TZ.index.str.startswith(c)].iloc[0]): 1.0})
        for k, f in parts.items():
            for z, s in zs.items():
                rows.append(dict(country=c, zone=f"UTC+{z:g}", key=k, etype=et, carrier=r.carrier, mwh=r.mwh_2050 * f * s))
    C = pd.DataFrame(rows).groupby(["country", "zone", "key", "etype"], as_index=False).mwh.sum()
    C.to_csv(ev / "G5_INDUSTRY_COMPOSITION.csv", index=False, float_format="%.3f")
    # ---- network: base electricity series, static AC loads, industry electricity by country / ID zone
    ds = xr.open_dataset(a.network)
    sn = pd.DatetimeIndex(ds["snapshots_snapshot"].values)
    B = pd.DataFrame({k: ds[f"buses_{k}"].values for k in ("carrier", "country")}, index=[str(i) for i in ds["buses_i"].values])
    L = pd.DataFrame({k: ds[f"loads_{k}"].values for k in ("bus", "carrier", "p_set")}, index=[str(i) for i in ds["loads_i"].values])
    L["country"] = L.bus.map(B.country); L["bc"] = L.bus.map(B.carrier)
    lt = ds["loads_t_p_set"].to_pandas(); lt.columns = [str(c) for c in ds["loads_t_p_set_i"].values]; lt.index = sn
    chk = []
    for c in sorted(C.country.unique()):
        net = float(L[(L.carrier == "industry electricity") & (L.country == c)].p_set.sum() * 8760)
        tab = float(C[(C.country == c) & (C.etype == "elec")].mwh.sum())
        chk.append(dict(country=c, network_industry_electricity_mwh=net, table_electricity_mwh=tab, diff_mwh=tab - net))
    for z in (7.0, 8.0, 9.0):
        nodes = TZ[(TZ == z) & TZ.index.str.startswith("ID")].index
        net = float(L[(L.carrier == "industry electricity") & L.bus.isin(nodes)].p_set.sum() * 8760)
        tab = float(C[(C.country == "ID") & (C.zone == f"UTC+{z:g}") & (C.etype == "elec")].mwh.sum())
        chk.append(dict(country=f"ID@UTC+{z:g}", network_industry_electricity_mwh=net, table_electricity_mwh=tab, diff_mwh=tab - net))
    R["composition_check"] = chk; R["composition_notes"] = notes
    # ---- curves per variant
    var = list(I.variant.unique())
    def curve(v, key, et, c, zone):
        q = I[(I.variant == v) & (I.subsector == key) & (I.etype == et)]
        zz = q[q.zone == zone]                      # tz-generic variants: "UTC+7"
        if zz.empty:                                # holiday variants are per country: "TH@UTC+7"
            zz = q[q.zone == f"{c}@{zone}"]
        if len(zz) != 1:
            raise ValueError(f"curve lookup {v} {key} {et} {c} {zone}: {len(zz)}")
        return P[zz.curve_id.iloc[0]].to_numpy()
    out, heat_out = [], []
    agg3 = lambda y: y.reshape(2920, 3).mean(1)
    aggd = lambda y: y.reshape(365, 24).mean(1)
    for c in sorted(C.country.unique()):
        cc = C[C.country == c]
        base = lt[[l for l in L.index[(L.carrier == "electricity") & (L.country == c)] if l in lt.columns]].sum(axis=1).to_numpy()
        static = float(L[(L.bc == "AC") & (L.country == c) & (L.carrier.isin(["agriculture machinery electric", "industry electricity"]))].p_set.sum())
        ind_flat = float(L[(L.carrier == "industry electricity") & (L.country == c)].p_set.sum())
        tot_flat = base + static
        for et in ("elec", "heat"):
            ce = cc[cc.etype == et]
            if ce.mwh.sum() == 0:
                continue
            mean = ce.mwh.sum() / 8760
            for v in ["FLAT"] + var:
                y = np.full(8760, mean) if v == "FLAT" else sum(r.mwh / 8760 * curve(v, r.key, et, c, r.zone) for r in ce.itertuples())
                y3, yd = agg3(y), aggd(y)
                rec = dict(country=c, etype=et, variant=v, annual_twh=ce.mwh.sum() / 1e6, mean_gw=mean / 1e3, peak_1h_gw=y.max() / 1e3, peak_3h_gw=y3.max() / 1e3,
                           peak_daily_gw=yd.max() / 1e3, min_3h_gw=y3.min() / 1e3, peak_over_mean_1h=y.max() / mean, peak_over_mean_3h=y3.max() / mean,
                           peak_over_mean_daily=yd.max() / mean, peak_3h_snapshot_utc=str(sn[int(y3.argmax())]))
                if et == "elec":
                    tot = base + (static - ind_flat) + y3      # base series + agriculture machinery (static) + profiled industry
                    rec.update(ac_fixed_load_peak_flat_gw=tot_flat.max() / 1e3, ac_fixed_load_peak_gw=tot.max() / 1e3,
                               ac_fixed_load_peak_change_gw=(tot.max() - tot_flat.max()) / 1e3, ac_fixed_load_peak_change_pct=100 * (tot.max() / tot_flat.max() - 1),
                               ac_fixed_load_mean_gw=tot.mean() / 1e3, industry_share_of_ac_fixed_energy=ind_flat / tot_flat.mean(),
                               ac_peak_snapshot_utc=str(sn[int(tot.argmax())]))
                    out.append(rec)
                else:
                    heat_out.append(rec)
    O = pd.DataFrame(out)
    for k in ("1h", "3h", "daily"):
        O[f"peak_change_{k}_gw"] = O[f"peak_{k}_gw"] - O.groupby("country")[f"peak_{k}_gw"].transform(lambda s: s.iloc[0])
    O.to_csv(ev / "G5_PEAK_IMPACT.csv", index=False, float_format="%.5f")
    Hh = pd.DataFrame(heat_out); Hh.to_csv(ev / "G5_HEAT_PEAKS.csv", index=False, float_format="%.5f")
    # ASEAN totals (coincident, 3 h)
    tot_rows = []
    for v in ["FLAT"] + var:
        y = np.zeros(2920); yt = np.zeros(2920)
        for c in sorted(C.country.unique()):
            ce = C[(C.country == c) & (C.etype == "elec")]
            yy = np.full(8760, ce.mwh.sum() / 8760) if v == "FLAT" else sum(r.mwh / 8760 * curve(v, r.key, "elec", c, r.zone) for r in ce.itertuples())
            y += agg3(yy)
            base = lt[[l for l in L.index[(L.carrier == "electricity") & (L.country == c)] if l in lt.columns]].sum(axis=1).to_numpy()
            static = float(L[(L.bc == "AC") & (L.country == c) & (L.carrier.isin(["agriculture machinery electric", "industry electricity"]))].p_set.sum())
            ind_flat = float(L[(L.carrier == "industry electricity") & (L.country == c)].p_set.sum())
            yt += base + static - ind_flat + agg3(yy)
        tot_rows.append(dict(variant=v, industry_peak_3h_gw=y.max() / 1e3, industry_mean_gw=y.mean() / 1e3, ac_fixed_peak_3h_gw=yt.max() / 1e3, ac_fixed_mean_gw=yt.mean() / 1e3))
    TT = pd.DataFrame(tot_rows); TT["ac_fixed_peak_change_gw"] = TT.ac_fixed_peak_3h_gw - TT.ac_fixed_peak_3h_gw.iloc[0]
    TT["industry_peak_change_gw"] = TT.industry_peak_3h_gw - TT.industry_peak_3h_gw.iloc[0]
    TT.to_csv(ev / "G5_PEAK_IMPACT_ASEAN.csv", index=False, float_format="%.4f")
    R["asean"] = TT.round(4).to_dict("records")
    R["main_by_country"] = O[O.variant == "MAIN"][["country", "annual_twh", "mean_gw", "peak_over_mean_1h", "peak_over_mean_3h", "peak_over_mean_daily", "peak_change_3h_gw",
                                                  "ac_fixed_load_peak_change_gw", "ac_fixed_load_peak_change_pct"]].round(4).to_dict("records")
    (ev / "G5_PEAKS.json").write_text(json.dumps(R, indent=1, default=str) + "\n", encoding="utf-8")
    # ---- figure
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        show = ["MAIN", "S2_OTHER_FLAT", "S3_OTHER_FFE13", "S1_SOURCE", "S8_UPPER"]
        pv = O[O.variant.isin(show)].pivot(index="country", columns="variant", values="ac_fixed_load_peak_change_pct")[show]
        fig, ax = plt.subplots(figsize=(9, 4.2)); pv.plot.bar(ax=ax, width=0.8, color=["#2a6f97", "#9db4c0", "#c97b63", "#7a9e7e", "#5c4d7d"])
        ax.axhline(0, color="#333", lw=0.8); ax.set_ylabel("change of fixed AC load peak, 3 h (%)"); ax.set_xlabel("")
        ax.set_title("Industrial profiles vs flat (v3 2050 energy unchanged)", loc="left", fontsize=10); ax.legend(fontsize=8, ncol=3, frameon=False)
        fig.tight_layout(); fig.savefig(ev / "fig_g5_peak_change.png", dpi=150); plt.close(fig)
        W = pd.read_csv(a.g5 / "WEEK_TEMPLATES_168.csv")
        fig, ax = plt.subplots(figsize=(9, 4.2))
        for k, col in [("FFE_NONSPEC", "#c97b63"), ("FFE_FOOD", "#e0a458"), ("FFE_NMM", "#7a9e7e"), ("MIX_DISPERSED_elec", "#2a6f97"), ("NREL_ALL", "#5c4d7d"), ("FLAT", "#333")]:
            ax.plot(np.arange(168), W[k], label=k, color=col, lw=1.2)
        ax.set_xticks(range(0, 169, 24)); ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun", ""]); ax.set_ylabel("load / annual mean")
        ax.set_title("Local-clock week templates (season removed)", loc="left", fontsize=10); ax.legend(fontsize=8, ncol=3, frameon=False)
        fig.tight_layout(); fig.savefig(ev / "fig_g5_week_templates.png", dpi=150); plt.close(fig)
    except Exception as e:   # figure is optional
        R["figure_error"] = repr(e)
    print(json.dumps(R["composition_check"], indent=0)[:2500]); print(notes)
    print(O[O.variant.isin(["MAIN", "S2_OTHER_FLAT", "S3_OTHER_FFE13", "S1_SOURCE", "S8_UPPER"])][["country", "variant", "annual_twh", "mean_gw", "peak_over_mean_1h",
          "peak_over_mean_3h", "peak_over_mean_daily", "ac_fixed_load_peak_change_gw", "ac_fixed_load_peak_change_pct"]].round(3).to_string())
    print(TT.round(3).to_string())


if __name__ == "__main__":
    main()
