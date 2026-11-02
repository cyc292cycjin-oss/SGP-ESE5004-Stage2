"""V3 phase 3 item 4: evaluate the two local 56x3h smoke runs against the instruction's criteria (read-only, no solve).

    PYTHONHASHSEED=0 python scripts_project/v3_smoke_eval.py --run <smoke dir with integrated/ no_new_xb/> --out <evidence dir> [--v2-run <v2 smoke dir>]

Criteria, both runs: Gurobi optimal (or decision 119 (a)(b) from PRECISION.json), ledger identity B16_LEDGER; B6 = objective(no_new_xb) - objective(integrated) > 0, SG marine fuel has a
source, no shedding or slack component in use. Reported in addition: capacity dual of every ship and transit link (review decision D161-10, non-zero = reported), national liquid
balances and duals, the integrated cross-border build, the Indonesian industry shares and, for the 56-snapshot level only, the v2 smoke objectives. Writes V3_SMOKE_RESULT.json,
V3_SHIP_CAPACITY_DUALS.csv, V3_LIQUID_BALANCE.csv.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from v3_layers import LOAD_CARRIERS, SHIP_CARRIERS, TRANSIT_CARRIER   # noqa: E402
from v5.v5_gates import gate_b5_no_new_xb, gate_b6_cost   # noqa: E402

logging.getLogger("pypsa").setLevel(logging.ERROR)
SCEN = ["integrated", "no_new_xb"]
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
DUAL_TOL = 1e-6   # EUR/MWh; interior-point duals without crossover are not exact zeros: everything above is listed
SLACK_WORDS = ("slack", "shed", "lost load", "overflow")


def jl(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def energy(n, df_t: pd.DataFrame, names) -> pd.Series:
    """annual-equivalent MWh of a time series frame, by column"""
    names = [x for x in names if x in df_t.columns]
    return df_t[names].mul(n.snapshot_weightings.generators, axis=0).sum()


def ship_duals(n, sc: str) -> pd.DataFrame:
    L = n.links; x = L[L.carrier.isin(list(SHIP_CARRIERS.values()) + [TRANSIT_CARRIER])]
    mu = n.links_t["mu_upper"].reindex(columns=x.index) if "mu_upper" in n.links_t else pd.DataFrame(index=n.snapshots, columns=x.index, dtype=float)
    p0 = n.links_t.p0.reindex(columns=x.index).fillna(0.0)
    out = pd.DataFrame(dict(scenario=sc, carrier=x.carrier.astype(str), origin=x.bus0.astype(str), destination=x.bus1.astype(str), p_nom_mw=x.p_nom, flow_twh=energy(n, n.links_t.p0, x.index).reindex(x.index).fillna(0.0) / 1e6,
                            max_utilisation=(p0.max() / x.p_nom.replace(0.0, np.nan)), mu_upper_max_abs=mu.abs().max(), mu_available=mu.notna().any()))
    return out.rename_axis("link").reset_index()


def liquid_balance(n, sc: str) -> pd.DataFrame:
    """annual-equivalent TWh at each national liquid bus, by term; a term is positive when it brings energy to the bus"""
    L = n.links; rows = []
    ship = set(SHIP_CARRIERS.values()) | {TRANSIT_CARRIER}
    for c in COUNTRIES:
        for k in LOAD_CARRIERS:
            b = f"{c} {k}"
            if b not in n.buses.index:
                continue
            g = n.generators[n.generators.bus == b]
            if len(g):
                rows.append(dict(term="import outside ASEAN", origin="", twh=float(energy(n, n.generators_t.p, g.index).sum()) / 1e6))
                rows[-1].update(country=c, carrier=k)
            s = n.stores[n.stores.bus == b]
            if len(s):
                rows.append(dict(term="store net", origin="", twh=float(energy(n, n.stores_t.p, s.index).sum()) / 1e6, country=c, carrier=k))
            for col, sign, flow in (("bus0", -1.0, "p0"), ("bus1", -1.0, "p1"), ("bus2", -1.0, "p2"), ("bus3", -1.0, "p3")):
                if col not in L or flow not in n.links_t:
                    continue
                y = L[L[col].astype(str) == b]
                for name, z in y.iterrows():
                    v = float(energy(n, n.links_t[flow], [name]).sum()) * sign / 1e6
                    if abs(v) < 1e-9:
                        continue
                    cr = str(z.carrier)
                    if cr in ship:
                        term, org = ("ship in", str(z.bus0)[:2]) if col == "bus1" else ("ship out", str(z.bus1)[:2])
                    else:
                        term, org = cr, ""
                    rows.append(dict(term=term, origin=org, twh=v, country=c, carrier=k))
    t = pd.DataFrame(rows, columns=["country", "carrier", "term", "origin", "twh"])
    t = t.groupby(["country", "carrier", "term", "origin"], as_index=False).twh.sum(); t.insert(0, "scenario", sc)
    return t


def sg_marine(n, bal: pd.DataFrame) -> dict:
    """the SG methanol bus feeds the SG marine load: delivered shares by origin; the load itself from the ASEAN-tagged loads on SG nodes"""
    w = n.snapshot_weightings.generators
    l = n.loads[(n.loads.country.astype(str) == "ASEAN") & (n.loads.carrier.astype(str) == "shipping methanol") & (n.loads.bus.astype(str).str.startswith("SG"))]
    load = float(n.get_switchable_as_dense("Load", "p_set")[l.index].mul(w, axis=0).sum().sum()) / 1e6
    b = bal[(bal.country == "SG") & (bal.carrier == "methanol")]
    ins = b[b.term == "ship in"].set_index("origin").twh.to_dict(); ext = float(b[b.term == "import outside ASEAN"].twh.sum())
    local = float(b[(b.twh > 0) & ~b.term.isin(["ship in", "import outside ASEAN", "store net"])].twh.sum())
    supplied = sum(ins.values()) + ext + local
    return dict(marine_load_twh=load, ship_in_twh_by_origin=ins, import_outside_asean_twh=ext, local_production_twh=local, supplied_twh=supplied, ship_share=(sum(ins.values()) / supplied if supplied else None),
                has_source=bool(load > 0 and supplied >= load * (1 - 1e-6)))


def slack_use(n) -> dict:
    out = {}
    for typ, frame, p in (("Generator", n.generators, n.generators_t.p), ("Link", n.links, n.links_t.p0)):
        x = frame[frame.carrier.astype(str).str.lower().str.contains("|".join(SLACK_WORDS))]
        out[typ] = dict(components=int(len(x)), carriers=sorted(set(x.carrier.astype(str))), abs_twh=float(energy(n, p.abs(), x.index).sum()) / 1e6)
    return out


def xb_build(n) -> dict:
    lines = n.lines[n.lines.border_class == "cross_border"]; links = n.links[n.links.border_class == "cross_border"]
    return dict(ac_gw=float(lines.s_nom_opt.sum()) / 1e3, ac_added_gw=float((lines.s_nom_opt - lines.s_nom_min).sum()) / 1e3, link_gw_by_carrier={k: float(v) / 1e3 for k, v in links.groupby(links.carrier.astype(str)).p_nom_opt.sum().items()})


def id_industry(n) -> dict:
    l = n.loads[(n.loads.carrier.astype(str).str.startswith("industry")) & (n.loads.bus.astype(str).str.startswith("ID_"))]
    p = n.get_switchable_as_dense("Load", "p_set")[l.index].mean() * 8760.0 / 1e6
    r = p.groupby(l.bus.astype(str).str.extract(r"ID_([A-Za-z-]+?)\d")[0]).sum()
    return {k: float(v / r.sum()) for k, v in r.items()}


def one(d: Path, sc: str) -> dict:
    rec, v5, v6, prec = (jl(d / f) for f in ("SOLVE_RECEIPT.json", "V5_GATES.json", "V6_ACCEPTANCE.json", "PRECISION.json"))
    acc = prec.get("acceptance") or {}
    out = dict(termination_condition=rec.get("termination_condition"), status=rec.get("status"), objective_eur=rec.get("objective"), solve_seconds=rec.get("solve_seconds"), peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30,
               truncated_to=(rec.get("input_network") or {}).get("truncated_to"), label=rec.get("label"), profile=rec.get("solver_profile"), v6_label=v6.get("label"), c1=acc, c1_grade=(prec.get("grade") or {}).get("grade"),
               ledger_identity_passed=(v5.get("B16_LEDGER") or {}).get("passed"), ledger_relative_error=(v5.get("B16_LEDGER") or {}).get("relative_error"), v5_all_passed=v5.get("all_passed"),
               v5_failed=sorted(k for k, v in v5.items() if isinstance(v, dict) and v.get("passed") is False))
    optimal = str(out["termination_condition"]) == "optimal"
    out["criterion_optimal_or_119ab"] = bool(optimal or (acc.get("a") and acc.get("b")))
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument("--run", type=Path, required=True); p.add_argument("--out", type=Path, required=True); p.add_argument("--v2-run", type=Path, default=None)
    a = p.parse_args()
    res = {sc: one(a.run / sc, sc) for sc in SCEN}; nets, duals, bal = {}, [], []
    for sc in SCEN:
        f = a.run / sc / f"{sc}_SMOKE_TEST_ONLY_solved.nc"
        res[sc]["solved_network"] = f.exists()
        if not f.exists():
            continue
        n = nets[sc] = pypsa.Network(f)
        d = ship_duals(n, sc); b = liquid_balance(n, sc); duals.append(d); bal.append(b)
        nz = d[d.mu_upper_max_abs.fillna(0.0) > DUAL_TOL]
        res[sc]["ship_capacity_duals"] = dict(links=int(len(d)), available=bool(d.mu_available.all()), above_tolerance=int(len(nz)), tolerance_eur_per_mwh=DUAL_TOL, max_abs_eur_per_mwh=float(d.mu_upper_max_abs.max()), max_utilisation=float(d.max_utilisation.max()))
        res[sc]["sg_marine_fuel"] = sg_marine(n, b); res[sc]["slack"] = slack_use(n); res[sc]["cross_border"] = xb_build(n); res[sc]["id_industry_shares"] = id_industry(n)
        res[sc]["liquid_dual_annual_mean_eur_per_mwh"] = {k: {c: float(n.buses_t.marginal_price[f"{c} {k}"].mean()) for c in COUNTRIES if f"{c} {k}" in n.buses_t.marginal_price} for k in LOAD_CARRIERS}
        res[sc]["ship_flow_twh"] = {str(k): float(v) for k, v in d.groupby("carrier").flow_twh.sum().items()}
        res[sc]["criterion_no_slack"] = bool(all(v["abs_twh"] <= 1e-6 for v in res[sc]["slack"].values()))
    if duals:
        a.out.mkdir(parents=True, exist_ok=True)
        pd.concat(duals).sort_values(["scenario", "mu_upper_max_abs"], ascending=[True, False]).to_csv(a.out / "V3_SHIP_CAPACITY_DUALS.csv", index=False); pd.concat(bal).to_csv(a.out / "V3_LIQUID_BALANCE.csv", index=False)
    oi, or_ = res["integrated"]["objective_eur"], res["no_new_xb"]["objective_eur"]
    v = (or_ - oi) if (oi is not None and or_ is not None) else None
    res["B6"] = dict(gate=gate_b6_cost(oi, or_, "integrated", "no_new_xb") if v is not None else dict(passed=False, note="objective missing"), b6_eur=v, b6_bn_eur=(v / 1e9 if v is not None else None), positive=bool(v is not None and v > 0))
    if len(nets) == 2:
        res["B5_NO_NEW_XB_solved"] = gate_b5_no_new_xb(nets["integrated"], nets["no_new_xb"])
    if a.v2_run:
        o = {sc: jl(a.v2_run / sc / "SOLVE_RECEIPT.json").get("objective") for sc in ("integrated", "disconnected")}
        res["v2_smoke_same_56_snapshots"] = dict(objective_eur=o, b6_bn_eur=(o["disconnected"] - o["integrated"]) / 1e9, note="profile formal_barrier_1e6_t16 and the fully separated reference: level comparison only, not the 365x24h figure of the prediction")
    sg = res["integrated"].get("sg_marine_fuel", {}).get("has_source"), res["no_new_xb"].get("sg_marine_fuel", {}).get("has_source")
    res["criteria"] = dict(optimal_or_119ab=all(res[s]["criterion_optimal_or_119ab"] for s in SCEN), b16_ledger=all(bool(res[s]["ledger_identity_passed"]) for s in SCEN), b6_positive=res["B6"]["positive"],
                           sg_marine_fuel_has_source=all(bool(x) for x in sg), no_slack=all(bool(res[s].get("criterion_no_slack")) for s in SCEN))
    res["passed"] = all(res["criteria"].values())
    a.out.mkdir(parents=True, exist_ok=True); (a.out / "V3_SMOKE_RESULT.json").write_text(json.dumps(res, indent=1, default=str, sort_keys=True))
    print(json.dumps(dict(criteria=res["criteria"], passed=res["passed"], B6_bn=res["B6"]["b6_bn_eur"], **{sc: dict(cond=res[sc]["termination_condition"], seconds=res[sc]["solve_seconds"], obj=res[sc]["objective_eur"], v6=res[sc]["v6_label"]) for sc in SCEN}), indent=1, default=str))


if __name__ == "__main__":
    main()
