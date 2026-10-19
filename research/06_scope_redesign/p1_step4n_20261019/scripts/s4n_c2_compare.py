"""S4N supplement 02 C2 (decision 119 / decision 107 (c)): solver-profile calibration - pypsa_eur_default vs profile A (S4M-2), same S4M-1 networks
(2920x3h builds, --truncate 56). READ ONLY: receipts, gates, ledgers, price tables, dual files; the S4M-2 reference duals of the country CO2 rows are
mapped from solution/Pi.npy through a model rebuild (no solve, nothing written into the S4M-2 folders).

Acceptance (decision 107, fixed beforehand): objective |cal / ref - 1| <= 1e-5 (each scenario); B16 <= 1e-6 (each calibration run); per country the
change of the "disconnected - integrated" ledger difference <= max(1 % of the reference difference, 0.01 bn EUR).
Information only: termination, iterations, times; nodal prices (bus means: mean and max absolute difference); country CO2 shadow prices; BN / SG / VN
solid-biomass shadow prices.

    PYTHONHASHSEED=0 python s4n_c2_compare.py --repo <research repo> --ref <S4M-2 solves dir> --cal <C2 solves dir> --builds <S4M-1 builds dir> --out-json .. --out-md ..
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCEN = ("integrated", "disconnected", "integrated_nze")
COUNTRIES = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN")
ENTITIES = COUNTRIES + ("ASEAN_BUNKER",)
STD = dict(objective_rel_tol=1e-5, b16_tol=1e-6, country_pct=0.01, country_floor_bn_eur=0.01, source="decision 107 (c), fixed beforehand; S4N supplement 02 C2 point 3")


def co2_duals_from_file(d: Path) -> dict:
    import xarray as xr
    p = d / "DUALS_BY_CONSTRAINT.nc"
    if not p.exists():
        return {}
    D = xr.open_dataset(p)
    return {k.split("-")[-1]: float(D[k].values) for k in D.data_vars if k.startswith("research_country_co2_limit-") and D[k].size == 1}


def co2_duals_from_pi(repo: Path, d: Path, network: Path, scenario: str) -> dict:
    sys.path.insert(0, str(repo / "scripts_project"))
    from l23_violation_analysis import build_model
    rec = json.loads((d / "SOLVE_RECEIPT.json").read_text())
    n, m, cfg = build_model(repo, network, scenario, int((rec.get("input_network") or {}).get("truncated_to") or 0) or None, rec.get("label", "SMOKE_TEST_ONLY"))
    cl = np.load(d / "lp" / "clabels.npy"); pi = np.load(d / "solution" / "Pi.npy")
    if len(cl) != len(pi) or int(m.ncons) != len(pi):
        raise RuntimeError(f"row count mismatch: clabels {len(cl)} Pi {len(pi)} model {m.ncons}")
    pos = {int(l): i for i, l in enumerate(cl)}
    out = {}
    for k in m.constraints:
        if str(k).startswith("research_country_co2_limit-"):
            lab = int(np.asarray(m.constraints[k].labels).ravel()[0])
            out[str(k).split("-")[-1]] = float(pi[pos[lab]]) if lab in pos else None
    return out


def main():
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    for k in ("repo", "ref", "cal", "builds", "out-json", "out-md"):
        ap.add_argument("--" + k, type=Path, required=True)
    ap.add_argument("--ref-tag", default="s4m_A_"); ap.add_argument("--cal-tag", default="cal_")
    ap.add_argument("--ref-duals-integrated", type=Path, default=None, help="folder with the in-run/offline DUALS file of the same reference LP (S4M-S2 re-run)")
    a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    from s4l_2_summary import bus_means, ledger_totals, prices, run_row
    runs = {}
    for sc in SCEN:
        runs[f"ref_{sc}"] = run_row(a.ref / f"{a.ref_tag}{sc}", f"ref_{sc}")
        runs[f"cal_{sc}"] = run_row(a.cal / f"{a.cal_tag}{sc}", f"cal_{sc}")
    res = dict(standard=STD, runs=runs)
    # objective and B16
    obj = {sc: (abs(runs[f"cal_{sc}"]["objective"] / runs[f"ref_{sc}"]["objective"] - 1) if (runs[f"cal_{sc}"]["objective"] and runs[f"ref_{sc}"]["objective"]) else None) for sc in SCEN}
    b16 = {sc: runs[f"cal_{sc}"]["B16_relative_error"] for sc in SCEN}
    res["objective_rel_diff"] = obj; res["b16_cal"] = b16
    # country differences (disconnected - integrated)
    li_r, ld_r = ledger_totals(a.ref / f"{a.ref_tag}integrated"), ledger_totals(a.ref / f"{a.ref_tag}disconnected")
    li_c, ld_c = ledger_totals(a.cal / f"{a.cal_tag}integrated"), ledger_totals(a.cal / f"{a.cal_tag}disconnected")
    ctry = {}
    for c in ENTITIES:
        dr = float(ld_r.get(c, np.nan) - li_r.get(c, np.nan)); dc = float(ld_c.get(c, np.nan) - li_c.get(c, np.nan)); tol = max(STD["country_pct"] * abs(dr), STD["country_floor_bn_eur"])
        ctry[c] = dict(ref_diff_bn=dr, cal_diff_bn=dc, change_bn=dc - dr, tolerance_bn=tol, within=bool(abs(dc - dr) <= tol) if np.isfinite(dc - dr) else False)
    res["country_differences"] = ctry
    b6r = runs["ref_disconnected"]["objective"] - runs["ref_integrated"]["objective"]; b6c = runs["cal_disconnected"]["objective"] - runs["cal_integrated"]["objective"]
    res["B6_bn_eur"] = dict(ref=b6r / 1e9, cal=b6c / 1e9, change=(b6c - b6r) / 1e9)
    res["nze_minus_integrated_bn_eur"] = dict(ref=(runs["ref_integrated_nze"]["objective"] - runs["ref_integrated"]["objective"]) / 1e9,
                                              cal=(runs["cal_integrated_nze"]["objective"] - runs["cal_integrated"]["objective"]) / 1e9)
    res["accepted"] = dict(objective=bool(all(v is not None and v <= STD["objective_rel_tol"] for v in obj.values())),
                           b16=bool(all(v is not None and v <= STD["b16_tol"] for v in b16.values())),
                           countries=bool(all(v["within"] for v in ctry.values())))
    res["accepted"]["all"] = bool(all(res["accepted"].values()))
    res["all_optimal"] = bool(all(runs[f"cal_{sc}"]["termination"] == "optimal" for sc in SCEN))
    # information: prices
    info = {}
    for sc in SCEN:
        pr, pc = prices(a.ref / f"{a.ref_tag}{sc}"), prices(a.cal / f"{a.cal_tag}{sc}")
        car_diff = {}
        for car in ("AC", "H2", "gas", "solid biomass"):
            r, c = bus_means(a.ref / f"{a.ref_tag}{sc}", car), bus_means(a.cal / f"{a.cal_tag}{sc}", car)
            common = r.index.intersection(c.index)
            if len(common):
                d = (c[common] - r[common]).abs()
                car_diff[car] = dict(buses=int(len(common)), mean_abs_diff=float(d.mean()), max_abs_diff=float(d.max()), max_bus=str(d.idxmax()))
        bio = {cc: dict(ref=(pr.get(f"solid biomass|{cc}") or {}).get("mean_of_bus_means"), cal=(pc.get(f"solid biomass|{cc}") or {}).get("mean_of_bus_means")) for cc in ("BN", "SG", "VN")}
        for v in bio.values():
            v["diff"] = (v["cal"] - v["ref"]) if (v["cal"] is not None and v["ref"] is not None) else None
        info[sc] = dict(nodal_price_bus_mean_differences=car_diff, solid_biomass_shadow_price_eur_per_mwh=bio)
    # country CO2 shadow prices
    nets = dict(integrated=a.builds / "integrated" / "integrated_2920_3h_unsolved.nc", disconnected=a.builds / "disconnected" / "disconnected_2920_3h_unsolved.nc",
                integrated_nze=a.builds / "integrated_nze" / "integrated_2920_3h_unsolved.nc")
    scen_of = dict(integrated="integrated", disconnected="disconnected", integrated_nze="integrated")
    for sc in SCEN:
        c_cal = co2_duals_from_file(a.cal / f"{a.cal_tag}{sc}")
        if sc == "integrated" and a.ref_duals_integrated is not None and (a.ref_duals_integrated / "DUALS_BY_CONSTRAINT.nc").exists():
            c_ref = co2_duals_from_file(a.ref_duals_integrated); src = f"in-run / offline file of the identical reference LP ({a.ref_duals_integrated.name})"
        else:
            try:
                c_ref = co2_duals_from_pi(a.repo, a.ref / f"{a.ref_tag}{sc}", nets[sc], scen_of[sc]); src = "solution/Pi.npy mapped by a model rebuild (read only)"
            except Exception as e:   # noqa: BLE001
                c_ref = {}; src = f"not available: {str(e)[:200]}"
        info[sc]["country_co2_shadow_price_raw_dual"] = {cc: dict(ref=c_ref.get(cc), cal=c_cal.get(cc), diff=((c_cal[cc] - c_ref[cc]) if (c_cal.get(cc) is not None and c_ref.get(cc) is not None) else None)) for cc in COUNTRIES}
        info[sc]["co2_reference_source"] = src
    res["information"] = info
    a.out_json.write_text(json.dumps(res, indent=1, default=str))
    # markdown
    L = ["# C2 求解档案标定：pypsa_eur_default vs 档案 A（S4M-2，同一网络 56×3h）", "",
         f"- 接受标准（第 107 项事先固定）：目标相对差 ≤ 1e-5；B16 ≤ 1e-6；每国差额变化 ≤ max(1 %, 0.01 bn)。判定：目标 {res['accepted']['objective']}，B16 {res['accepted']['b16']}，分国 {res['accepted']['countries']} → **{res['accepted']['all']}**", "",
         "| 运行 | 终止 | 迭代 | barrier s | 求解 s | 目标 EUR | 与档案 A 相对差 | B16 | 求解器容差门槛（不含 B12） |", "|---|---|---|---|---|---|---|---|---|"]
    for sc in SCEN:
        for side in ("ref", "cal"):
            r = runs[f"{side}_{sc}"]
            L.append(f"| {side}_{sc} | {r['termination']} | {r.get('barrier_iterations')} | {r.get('barrier_seconds')} | {round(r['solve_seconds'] or 0, 1)} | {r['objective']} | {(obj[sc] if side == 'cal' else '')} | {r['B16_relative_error']} | {r.get('all_passed_solver_tolerances_excl_B12')}（失败：{','.join(r.get('failed_gates_solver_tolerance_set') or [])}） |")
    L += ["", "| 国 | 档案 A 差额 bn | 标定差额 bn | 变化 bn | 容差 bn | 通过 |", "|---|---|---|---|---|---|"]
    L += [f"| {c} | {v['ref_diff_bn']:.4f} | {v['cal_diff_bn']:.4f} | {v['change_bn']:+.4f} | {v['tolerance_bn']:.4f} | {v['within']} |" for c, v in ctry.items()]
    L += ["", f"- B6（不互联 − 一体化）bn：档案 A {res['B6_bn_eur']['ref']:.4f}，标定 {res['B6_bn_eur']['cal']:.4f}，变化 {res['B6_bn_eur']['change']:+.4f}；NZE − 一体化：{res['nze_minus_integrated_bn_eur']['ref']:.4f} / {res['nze_minus_integrated_bn_eur']['cal']:.4f}", "",
          "## 只作信息", ""]
    for sc in SCEN:
        L.append(f"- {sc}：节点价格（母线平均价）差：" + "；".join(f"{car} 平均 {v['mean_abs_diff']:.4g} / 最大 {v['max_abs_diff']:.4g} EUR/MWh" for car, v in info[sc]["nodal_price_bus_mean_differences"].items()))
        L.append(f"  - 固体生物质影子价格 EUR/MWh（档案 A → 标定）：" + "；".join(f"{cc} {v['ref']} → {v['cal']}" for cc, v in info[sc]["solid_biomass_shadow_price_eur_per_mwh"].items()))
        cd = info[sc]["country_co2_shadow_price_raw_dual"]
        L.append(f"  - 各国 CO₂ 上限对偶（原始 LP 对偶，档案 A → 标定；来源：{info[sc]['co2_reference_source']}）：" + "；".join(f"{cc} {v['ref']} → {v['cal']}" for cc, v in cd.items() if v['ref'] is not None or v['cal'] is not None))
    a.out_md.write_text("\n".join(L) + "\n")
    print(json.dumps(dict(accepted=res["accepted"], all_optimal=res["all_optimal"], objective=obj, b16=b16, B6=res["B6_bn_eur"],
                          worst_country=max(((c, abs(v["change_bn"]) / v["tolerance_bn"]) for c, v in ctry.items()), key=lambda t: t[1])), default=str))


if __name__ == "__main__":
    main()
