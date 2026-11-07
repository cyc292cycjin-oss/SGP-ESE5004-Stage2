"""V31 W15 stage B, section 7.5-7.6: per-snapshot statistics from the solved networks, read selectively with xarray (not pypsa: a few
hundred MB per network instead of several GiB), plus the CO2 storage caps and the flows of the zero-cost components (read only; no solver).

  python -I w15b_dispatch.py --run F1=<solved nc>,<DUALS_BY_CONSTRAINT.nc>,<SOLVE_RECEIPT.json> ... --run V1=<365x24h solved nc>,<duals>,<receipt>
         --scan <ZERO_COST_SCAN.csv> --out <work/p1_v31_w15_20261106> [--font <ttf/ttc>]

Writes DISPATCH_STATS.csv, DIURNAL_PROFILE.csv, NIGHT_SUPPLY.csv, DIURNAL_SUPPLY.png, ZERO_COST_SCAN.csv (adds flow columns),
evidence/CO2_STORAGE_CAPS.json, evidence/DISPATCH_META.json.
Night = snapshots starting 12:00-21:00 UTC (19:00-07:00 at UTC+7, 20:00-08:00 at UTC+8); daily-resolution runs have no night.
"""
import argparse, json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ELEC_BUS = ("AC", "low voltage", "DC")
TRANSFER = ("B2B", "DC", "electricity distribution grid")   # transfers between electricity buses, never supply
SUPPLY_GROUP = [
    ("光伏", ("solar", "solar rooftop", "solar existing")),
    ("风电", ("onwind", "onwind existing", "offwind-ac", "offwind-dc", "offwind-float", "offwind existing")),
    ("水电", ("hydro", "hydro existing", "ror", "ror existing")),
    ("储能放电", ("battery discharger", "home battery discharger", "PHS", "PHS existing")),
    ("气电", ("CCGT", "CCGT CC", "CCGT existing", "OCGT", "OCGT existing", "OCGT methanol")),
    ("煤电与油电", ("coal existing", "lignite existing", "oil existing")),
    ("地热、生物质与核", ("geothermal", "geothermal existing", "biomass EOP", "biomass EOP CC", "nuclear", "nuclear SMR", "waste CHP")),
]
GROUP_OF = {c: g for g, cs in SUPPLY_GROUP for c in cs}
SINK = {"battery charger": "固定电池充电", "home battery charger": "户用电池充电", "BEV charger": "EV 充电", "H2 Electrolysis": "电解槽用电"}
PV = ("solar", "solar rooftop", "solar existing")
WIND = ("onwind", "onwind existing", "offwind-ac", "offwind-dc", "offwind-float", "offwind existing")


def names(ds, dim):
    return [str(x) for x in ds[dim].values]


def static(ds, comp, attr):
    v = f"{comp}_{attr}"
    return pd.Series(ds[v].values, index=names(ds, f"{comp}_i")) if v in ds else None


def tseries(ds, comp, attr, T):
    v = f"{comp}_t_{attr}"
    if v not in ds:
        return pd.DataFrame(index=range(T))
    return pd.DataFrame(ds[v].values.astype(float), columns=names(ds, f"{comp}_t_{attr}_i"))


def run_stats(label: str, nc: Path, duals: Path, receipt: Path):
    ds = xr.open_dataset(nc)
    snap = pd.to_datetime(pd.Series(ds["snapshots_snapshot"].values))
    T = len(snap)
    wg = ds["snapshots_generators"].values.astype(float) if "snapshots_generators" in ds else np.full(T, 8760.0 / T)
    ws = ds["snapshots_stores"].values.astype(float) if "snapshots_stores" in ds else wg
    hour = snap.dt.hour.to_numpy()
    night = np.isin(hour, (12, 15, 18, 21)) if T > 365 else np.zeros(T, bool)
    bcar = static(ds, "buses", "carrier").astype(str)
    elec = set(bcar[bcar.isin(ELEC_BUS)].index)
    out = dict(run=label, snapshots=T, weight_h=float(wg[0]), bus_carriers_used=sorted(set(bcar[bcar.isin(ELEC_BUS)])))
    # generators
    gcar = static(ds, "generators", "carrier").astype(str); gbus = static(ds, "generators", "bus").astype(str)
    gp = tseries(ds, "generators", "p", T).reindex(columns=gcar.index, fill_value=0.0)
    pnom = static(ds, "generators", "p_nom_opt").astype(float)
    pmax = pd.DataFrame(np.tile(static(ds, "generators", "p_max_pu").astype(float).to_numpy(), (T, 1)), columns=gcar.index)
    pmt = tseries(ds, "generators", "p_max_pu", T)
    if len(pmt.columns):
        pmax[pmt.columns] = pmt
    avail = pmax * pnom
    def ann(df, cols, w=wg):
        return float((df[cols].sum(axis=1).to_numpy() * w).sum()) if len(cols) else 0.0
    for nm, cs in (("pv", PV), ("wind", WIND)):
        cols = list(gcar.index[gcar.isin(cs)])
        e = ann(gp, cols); a = ann(avail, cols)
        out[f"{nm}_output_twh"] = e / 1e6; out[f"{nm}_available_twh"] = a / 1e6; out[f"{nm}_curtail_twh"] = (a - e) / 1e6
        out[f"{nm}_curtail_share"] = (a - e) / a if a else None
    # links
    lcar = static(ds, "links", "carrier").astype(str); b0 = static(ds, "links", "bus0").astype(str); b1 = static(ds, "links", "bus1").astype(str)
    p0 = tseries(ds, "links", "p0", T).reindex(columns=lcar.index, fill_value=0.0)
    p1 = tseries(ds, "links", "p1", T).reindex(columns=lcar.index, fill_value=0.0)
    lnom = static(ds, "links", "p_nom_opt").astype(float)
    # storage units / stores
    ucar = static(ds, "storage_units", "carrier").astype(str); ubus = static(ds, "storage_units", "bus").astype(str)
    ud = tseries(ds, "storage_units", "p_dispatch", T).reindex(columns=ucar.index, fill_value=0.0)
    usp = tseries(ds, "storage_units", "spill", T).reindex(columns=ucar.index, fill_value=0.0)
    out["hydro_spill_twh"] = ann(usp, list(ucar.index)) / 1e6
    scar = static(ds, "stores", "carrier").astype(str); senom = static(ds, "stores", "e_nom_opt").astype(float)
    sp = tseries(ds, "stores", "p", T).reindex(columns=scar.index, fill_value=0.0)
    for nm, chg, dis, st in (("battery", "battery charger", "battery discharger", "battery"), ("home_battery", "home battery charger", "home battery discharger", "home battery")):
        cin = ann(p0, list(lcar.index[lcar == chg])); dout = -ann(p1, list(lcar.index[lcar == dis]))
        cap = float(senom[scar == st].sum())
        out[f"{nm}_charge_in_twh"] = cin / 1e6; out[f"{nm}_discharge_out_twh"] = dout / 1e6; out[f"{nm}_energy_gwh"] = cap / 1e3
        out[f"{nm}_full_cycles"] = dout / cap if cap > 1 else None
        out[f"{nm}_discharge_power_gw"] = float(lnom[lcar == dis].sum()) / 1e3
    bev = list(lcar.index[lcar == "BEV charger"])
    out["bev_charge_twh"] = ann(p0, bev) / 1e6
    out["bev_charge_night_share"] = float((p0[bev].sum(axis=1).to_numpy() * wg)[night].sum() / max((p0[bev].sum(axis=1).to_numpy() * wg).sum(), 1e-9)) if T > 365 else None
    el = list(lcar.index[lcar == "H2 Electrolysis"])
    out["electrolysis_in_twh"] = ann(p0, el) / 1e6
    # electricity supply by group and snapshot
    sup = {}
    for g in [x for x, _ in SUPPLY_GROUP] + ["其他"]:
        sup[g] = np.zeros(T)
    ge = gcar.index[gbus.isin(elec)]
    for c in ge:
        sup[GROUP_OF.get(gcar[c], "其他")] += gp[c].to_numpy()
    le = lcar.index[b1.isin(elec) & ~b0.isin(elec) & ~lcar.isin(TRANSFER)]
    for c in le:
        sup[GROUP_OF.get(lcar[c], "其他")] += -p1[c].to_numpy()
    for c in ucar.index[ubus.isin(elec)]:
        sup[GROUP_OF.get(ucar[c], "其他")] += ud[c].to_numpy()
    other_carriers = sorted({gcar[c] for c in ge if gcar[c] not in GROUP_OF} | {lcar[c] for c in le if lcar[c] not in GROUP_OF} |
                            {ucar[c] for c in ucar.index[ubus.isin(elec)] if ucar[c] not in GROUP_OF})
    out["supply_other_carriers"] = other_carriers
    sinks = {k: -p0[list(lcar.index[lcar == c])].sum(axis=1).to_numpy() for c, k in SINK.items()}
    prof, night_rows = [], []
    for g, v in list(sup.items()) + list(sinks.items()):
        e = v * wg
        night_rows.append(dict(run=label, group=g, annual_twh=float(e.sum()) / 1e6, night_twh=float(e[night].sum()) / 1e6 if T > 365 else None,
                               day_twh=float(e[~night].sum()) / 1e6 if T > 365 else None, night_share=(float(e[night].sum() / e.sum()) if T > 365 and e.sum() else None)))
        if T > 365:
            s = pd.Series(v).groupby(hour).mean()
            for h, m in s.items():
                prof.append(dict(run=label, utc_hour=int(h), group=g, mean_gw=float(m) / 1e3))
    tot_night = sum(r["night_twh"] or 0 for r in night_rows if r["group"] in sup); tot = sum(r["annual_twh"] for r in night_rows if r["group"] in sup)
    for r in night_rows:
        if r["group"] in sup and T > 365:
            r["share_of_night_supply"] = (r["night_twh"] / tot_night) if tot_night else None
    out["electricity_supply_twh"] = tot; out["electricity_supply_night_twh"] = tot_night if T > 365 else None
    # checks of daily-resolution conclusions: dedicated plant lines by month (LA rainy-season shape), ship-link utilisation and capacity duals,
    # named components (Hongsa)
    month = snap.dt.month.to_numpy()
    ded = list(lcar.index[lcar == "dedicated plant line"])
    if ded:
        e = p0[ded].sum(axis=1).to_numpy() * wg; capmw = float(lnom[ded].sum())
        out["dedicated_lines_twh"] = float(e.sum()) / 1e6; out["dedicated_lines_capacity_gw"] = capmw / 1e3
        out["dedicated_lines_utilisation_by_month"] = {int(m): float(e[month == m].sum() / (capmw * wg[month == m].sum())) for m in range(1, 13)} if capmw else None
    ships = list(lcar.index[lcar.isin(("methanol ship", "ammonia ship", "oil non-fossil ship"))])
    if ships:
        util = (p0[ships].abs() / lnom[ships].replace(0, np.nan)).max().max()
        mu = tseries(ds, "links", "mu_upper", T)
        mu = mu[[c for c in ships if c in mu.columns]]
        out["ship_links"] = len(ships); out["ship_max_utilisation"] = float(util)
        out["ship_capacity_dual_nonzero_cells"] = int((mu.abs() > 1e-9).sum().sum()) if len(mu.columns) else 0
        out["ship_flow_twh"] = float((p0[ships].clip(lower=0).sum(axis=1).to_numpy() * wg).sum()) / 1e6
    named = {}
    for comp, idx, df in (("Link", lcar.index, p0), ("Generator", gcar.index, gp)):
        for c in idx:
            if "hongsa" in c.lower():
                named[f"{comp}:{c}"] = float((df[c].to_numpy() * wg).sum()) / 1e6
    out["named_flows_twh"] = named
    # zero-cost flows (annual MWh): generators p, links p0 (positive part and net), stores discharge, storage units dispatch
    flows = {}
    for c in gcar.index:
        flows[("Generator", c)] = float((gp[c].to_numpy() * wg).sum())
    for c in lcar.index:
        flows[("Link", c)] = float((p0[c].to_numpy() * wg).sum())
    for c in scar.index:
        flows[("Store", c)] = float((np.clip(sp[c].to_numpy(), 0, None) * ws).sum())
    for c in ucar.index:
        flows[("StorageUnit", c)] = float((ud[c].to_numpy() * wg).sum())
    # CO2 storage caps
    caps = {}
    if duals and Path(duals).exists():
        dd = xr.open_dataset(duals)
        R = json.loads(Path(receipt).read_text(encoding="utf-8"))
        seq = (R.get("co2_flows") or {}).get("sequestered_by_country") or {}
        for v in dd.data_vars:
            if v.startswith("research_co2_storage_cap-"):
                cc = v.split("-")[-1]; s = seq.get(cc, {})
                used, cap = s.get("final_level_t"), s.get("e_nom_max")
                caps[cc] = dict(dual_as_exported=float(np.nan_to_num(dd[v].values)), used_t=used, cap_t=cap,
                                slack_t=(cap - used) if used is not None and cap is not None else None, used_share=(used / cap) if used and cap else None)
        dd.close()
    ds.close()
    return out, prof, night_rows, flows, caps


def figure(prof: pd.DataFrame, path: Path, font: str | None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    if font and Path(font).exists():
        font_manager.fontManager.addfont(font); matplotlib.rcParams["font.family"] = font_manager.FontProperties(fname=font).get_name()
    matplotlib.rcParams["axes.unicode_minus"] = False
    SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    groups = ["光伏", "风电", "水电", "储能放电", "气电", "煤电与油电", "地热、生物质与核", "其他"]
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]   # reference palette, slots 1-8 in fixed order
    runs = [r for r in ("F1", "F2") if r in set(prof.run)]
    fig, axes = plt.subplots(1, len(runs), figsize=(6.6 * len(runs), 5.6), sharey=True, facecolor=SURF)
    axes = np.atleast_1d(axes)
    for ax, r in zip(axes, runs):
        ax.set_facecolor(SURF)
        p = prof[prof.run == r].pivot_table(index="utc_hour", columns="group", values="mean_gw", aggfunc="sum").reindex(columns=groups).fillna(0.0)
        x = np.arange(len(p.index)); bottom = np.zeros(len(x))
        for g, col in zip(groups, colors):
            v = p[g].clip(lower=0).to_numpy()
            ax.bar(x, v, bottom=bottom, color=col, width=0.78, label=g, edgecolor=SURF, linewidth=1.0)
            bottom += v
        ax.set_xticks(x); ax.set_xticklabels([f"{h:02d}–{h + 3:02d}\n(+7: {(h + 7) % 24:02d})" for h in p.index], fontsize=8, color=INK2)
        ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.spines["left"].set_color(GRID); ax.spines["bottom"].set_color(GRID); ax.tick_params(colors=INK2)
        ax.set_title({"F1": "F1 一体化", "F2": "F2 no_new_xb"}[r] + "：各 3 小时时段的平均供电（GW，全年平均）", color=INK, fontsize=10.5, loc="left")
        ax.set_xlabel("时段（UTC；括号内为 UTC+7 的起始时刻）", color=INK2)
    axes[0].set_ylabel("东盟电力供给（GW）", color=INK2)
    axes[-1].legend(frameon=False, loc="upper left", bbox_to_anchor=(1.0, 1.0), labelcolor=INK, fontsize=9)
    fig.text(0.01, 0.01, "来源：v3.1 HPC 结果包已解网络（2920×3h）；供给 = 电力母线（AC、低压、DC）上的发电机、自非电力母线输入的链路与储能单元出力（不含 DC、B2B、配电网等母线间转运）；时段为 UTC。", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150, facecolor=SURF)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="label=<solved nc>,<duals nc>,<SOLVE_RECEIPT.json>")
    ap.add_argument("--scan", required=True); ap.add_argument("--out", required=True); ap.add_argument("--font")
    a = ap.parse_args()
    OUT = Path(a.out)
    stats, prof, night, flows, caps = [], [], [], {}, {}
    for spec in a.run:
        lab, rest = spec.split("=", 1); nc, du, rc = rest.split(",")
        s, p, nr, fl, cp = run_stats(lab, Path(nc), Path(du), Path(rc))
        stats.append(s); prof += p; night += nr; flows[lab] = fl; caps[lab] = cp
        print(lab, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items() if k not in ("supply_other_carriers",)})
    nested = ("dedicated_lines_utilisation_by_month", "named_flows_twh")
    keys = [k for k in stats[0] if k not in ("run", "bus_carriers_used", "supply_other_carriers") + nested]
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "DISPATCH_NESTED.json").write_text(json.dumps({s["run"]: {k: s.get(k) for k in nested} for s in stats}, indent=1, ensure_ascii=False) + "\n",
                                                          encoding="utf-8", newline="\n")
    with (OUT / "DISPATCH_STATS.csv").open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("metric," + ",".join(s["run"] for s in stats) + "\n")
        for k in keys:
            fh.write(k + "," + ",".join("" if s.get(k) is None else repr(s.get(k)) for s in stats) + "\n")
    pd.DataFrame(prof).to_csv(OUT / "DIURNAL_PROFILE.csv", index=False, lineterminator="\n")
    pd.DataFrame(night).to_csv(OUT / "NIGHT_SUPPLY.csv", index=False, lineterminator="\n")
    scan = pd.read_csv(a.scan, keep_default_na=False, dtype=str)
    for lab, fl in flows.items():
        if lab.startswith("F"):
            scan[f"flow_mwh_{lab}"] = [repr(fl.get((c, n))) if (c, n) in fl else "" for c, n in zip(scan.component, scan.name)]
    scan["output_note"] = "阶段 B：flow_mwh_* = 年流量（发电机出力、链路 p0、Store 放出、储能单元出力），由已解网络读出"
    scan.to_csv(a.scan, index=False, lineterminator="\n")
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "CO2_STORAGE_CAPS.json").write_text(json.dumps(dict(
        note="dual of research_co2_storage_cap-<country> as exported in DUALS_BY_CONSTRAINT.nc (same values W10 used); used / cap from SOLVE_RECEIPT co2_flows", runs=caps),
        indent=1) + "\n", encoding="utf-8", newline="\n")
    (OUT / "evidence" / "DISPATCH_META.json").write_text(json.dumps(dict(
        definitions=dict(night="snapshots starting at 12, 15, 18, 21 UTC (2920x3h only)", electricity_buses=list(ELEC_BUS), transfers_excluded=list(TRANSFER),
                         supply="generators on electricity buses + links from a non-electricity bus into an electricity bus (-p1) + storage-unit dispatch",
                         groups={g: list(cs) for g, cs in SUPPLY_GROUP}),
        runs={s["run"]: dict(snapshots=s["snapshots"], weight_h=s["weight_h"], bus_carriers=s["bus_carriers_used"], other_carriers=s["supply_other_carriers"]) for s in stats}),
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    if prof:
        figure(pd.DataFrame(prof), OUT / "DIURNAL_SUPPLY.png", a.font)
    print("caps", {lab: {cc: (round(v["dual_as_exported"], 4), v["used_share"]) for cc, v in cp.items()} for lab, cp in caps.items()})


if __name__ == "__main__":
    main()
