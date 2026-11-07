"""V4 D2a section 7 (Fable F-22; decision 220): two-factor Shapley attribution of the v4 cost increase on the 56-snapshot smoke runs.

Factors: D = v4 demand (industry tables, curves, process emissions, feedstock carbon); P = v4 resource caps (biomass potential incl. T04, 0.99 cap, marketed
gas caps). Corners (every other v4 change at its v4 value):
  (D4, P4)   section-6 smoke  results_project/v4d2a/smoke56/v4d2a_F1 | _F2
  (D4, P31)  attrib56/d4p31_F1 | _F2        (D31, P4)  attrib56/d31p4_F1 | _F2
  (D31, P31) not solved (budget): APPROXIMATED (INFERENCE) = the W08 R0 run (v3.1 network on the W08 code, integrated) and, for no_new_xb, the v3.1 local
             smoke of the v3.1 package, plus the known other v4 changes on the v3.1 network: the D1 proxy cost (+1.449 bn, the trunk pools used in full),
             the D2a PHS reclassification and the methanol coefficient (first-order terms of SMOKE56_D2A.md section 1 applied to the v3.1 solution as a proxy).
Shapley (two players): phi_D = 1/2 [Z(D4,P31) - Z(D31,P31) + Z(D4,P4) - Z(D31,P4)], phi_P = 1/2 [Z(D31,P4) - Z(D31,P31) + Z(D4,P4) - Z(D4,P31)];
phi_D + phi_P = Z(D4,P4) - Z(D31,P31). Applied to the integrated objective, the no_new_xb objective, B6 = Z(F2) - Z(F1) and, per country, to the Owen
allocation of the corners (M12_BENEFIT*/BENEFIT.csv) and the country cost ledgers. 56 snapshots: direction only.

    <env python> scripts/attribution.py
Writes ATTRIBUTION_56.md (tables) and evidence/ATTRIBUTION_56.json.
"""
import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
RUNS = {("D4", "P4", "F1"): RP / "v4d2a/smoke56/v4d2a_F1", ("D4", "P4", "F2"): RP / "v4d2a/smoke56/v4d2a_F2",
        ("D4", "P31", "F1"): RP / "v4d2a/attrib56/d4p31_F1", ("D4", "P31", "F2"): RP / "v4d2a/attrib56/d4p31_F2",
        ("D31", "P4", "F1"): RP / "v4d2a/attrib56/d31p4_F1", ("D31", "P4", "F2"): RP / "v4d2a/attrib56/d31p4_F2"}
BENEFIT = {("D4", "P4"): RP / "v4d2a/smoke56/M12_BENEFIT/BENEFIT.csv", ("D4", "P31"): RP / "v4d2a/attrib56/M12_BENEFIT_d4p31/BENEFIT.csv",
           ("D31", "P4"): RP / "v4d2a/attrib56/M12_BENEFIT_d31p4/BENEFIT.csv"}
W08_R0 = RP / "v4w08/smoke56/v31_F1"           # v3.1 network solved on the W08 code (integrated)
V31_SMOKE = {"F1": None, "F2": None}           # filled from the v3.1 local smoke receipts when found (ATTRIB_INPUTS.json)
PLAYERS = ["MY", "ID", "SG", "BUNKER"]


def receipt(p: Path) -> dict:
    r = json.loads((p / "SOLVE_RECEIPT.json").read_text())
    return dict(objective=float(r["objective"]), objective_lp=float(r.get("objective_lp", float("nan"))), termination=r.get("termination_condition"),
                network_sha256=(r.get("input_network") or {}).get("sha256"), gates_v6=None)


def ledger(p: Path) -> dict:
    """Country cost ledger total per entity (EUR) of a run."""
    L = pd.read_csv(p / "COUNTRY_COST_LEDGER.csv").set_index("entity")
    col = [c for c in L.columns if c.startswith("total")]
    col = col[0] if col else L.columns[-1]
    return {str(k): float(v) for k, v in L[col].items()}


def benefit(p: Path) -> dict:
    if not p.exists():
        return {}
    B = pd.read_csv(p).set_index("player")
    return {str(k): float(v) for k, v in B.owen_benefit_eur.items()}


def shapley(z: dict) -> dict:
    """z: {(D, P): value}; returns phi_D, phi_P and the two orderings."""
    dD_P31 = z[("D4", "P31")] - z[("D31", "P31")]; dD_P4 = z[("D4", "P4")] - z[("D31", "P4")]
    dP_D31 = z[("D31", "P4")] - z[("D31", "P31")]; dP_D4 = z[("D4", "P4")] - z[("D4", "P31")]
    return dict(phi_D=0.5 * (dD_P31 + dD_P4), phi_P=0.5 * (dP_D31 + dP_D4), total=z[("D4", "P4")] - z[("D31", "P31")],
                D_first=dict(D=dD_P31, P=dP_D4), P_first=dict(P=dP_D31, D=dD_P4), interaction=dD_P4 - dD_P31)


def main():
    inp = json.loads((W / "evidence/ATTRIB_INPUTS.json").read_text())   # written by hand before the run: v3.1 smoke objectives and the other-change terms (INFERENCE)
    out = dict(method=__doc__, corners={}, approximation=inp)
    Z = {}
    for (d, p, f), path in RUNS.items():
        if (path / "SOLVE_RECEIPT.json").exists():
            r = receipt(path); Z[(d, p, f)] = r["objective"]; out["corners"][f"{d},{p},{f}"] = dict(r, run=str(path), owen=benefit(BENEFIT[(d, p)]) if f == "F1" else None, ledger=ledger(path))
    # (D31, P31) approximation
    for f in ("F1", "F2"):
        base = float(inp["v31_objective_eur"][f]); other = sum(float(v) for v in inp["other_v4_changes_on_v31_eur"][f].values())
        Z[("D31", "P31", f)] = base + other
        out["corners"][f"D31,P31,{f}"] = dict(objective=base + other, v31_objective_eur=base, other_changes_eur=inp["other_v4_changes_on_v31_eur"][f], grade="INFERENCE (approximated, not solved)")
    res = {}
    for f in ("F1", "F2"):
        z = {(d, p): Z[(d, p, f)] for (d, p) in (("D4", "P4"), ("D4", "P31"), ("D31", "P4"), ("D31", "P31"))}
        res[f] = dict(values=dict((f"{d},{p}", v) for (d, p), v in z.items()), shapley=shapley(z))
    b6 = {(d, p): Z[(d, p, "F2")] - Z[(d, p, "F1")] for (d, p) in (("D4", "P4"), ("D4", "P31"), ("D31", "P4"), ("D31", "P31"))}
    res["B6"] = dict(values=dict((f"{d},{p}", v) for (d, p), v in b6.items()), shapley=shapley(b6))
    # per-country: Owen benefit (B6 split) and integrated cost ledger per player; (D31,P31) per country from the approximation inputs
    own = {}
    for key, lab in (("owen", "Owen benefit (B6 allocation)"), ("ledger_F1", "integrated cost ledger")):
        own[key] = {}
        for pl in PLAYERS:
            z = {}
            for (d, p) in (("D4", "P4"), ("D4", "P31"), ("D31", "P4")):
                c = out["corners"][f"{d},{p},F1"]
                src = c["owen"] if key == "owen" else c["ledger"]
                k = pl if pl in src else ("ASEAN_BUNKER" if pl == "BUNKER" and "ASEAN_BUNKER" in src else pl)
                z[(d, p)] = float(src.get(k, float("nan")))
            z[("D31", "P31")] = float(inp["v31_by_player"][key].get(pl, float("nan")))
            own[key][pl] = dict(values=dict((f"{d},{p}", v) for (d, p), v in z.items()), shapley=shapley(z), label=lab)
    out["results"] = res; out["by_player"] = own
    (W / "evidence/ATTRIBUTION_56.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    # ---- markdown
    bn = lambda v: f"{v / 1e9:+.3f}"   # noqa: E731
    L = ["# v4 成本上升归因（56 时段，两因素 Shapley；V4 D2a 第 7 节；Fable F-22）", "",
         "- **因素：** 需求 D（v4 需求与工业表、曲线、过程排放与原料碳）；资源上限 P（v4 生物质潜力含 T04、0.99 上限、商品气上限）。其余 v4 改动在所有角上取 v4 值。",
         "- **角：** (D4,P4) = 第 6 节冒烟；(D4,P31)、(D31,P4) = 本节 4 次求解；**(D31,P31) 未求解（额度）**，用 v3.1 网络的冒烟值加已知其他改动近似（INFERENCE，`evidence/ATTRIB_INPUTS.json`）。",
         "- **56 时段结果只给方向，不作结论**（冬夏季节与储能跨期在 56 时段中不存在）。", ""]
    L += ["## 1. 目标值（EUR，含常数项）", "", "| 角 | F1 一体化 | F2 `no_new_xb` | B6 = F2 − F1 | 等级 |", "|---|---:|---:|---:|---|"]
    for (d, p) in (("D31", "P31"), ("D4", "P31"), ("D31", "P4"), ("D4", "P4")):
        g = "INFERENCE（近似）" if (d, p) == ("D31", "P31") else "VERIFIED（求解回执）"
        L.append(f"| ({d},{p}) | {Z[(d, p, 'F1')]:,.2f} | {Z[(d, p, 'F2')]:,.2f} | {b6[(d, p)]:,.2f} | {g} |")
    L += ["", "## 2. Shapley 拆分（bn EUR）", "", "| 量 | 总变化 (D4,P4) − (D31,P31) | φ_D 需求 | φ_P 资源上限 | 交互项 (D 在 P4 − D 在 P31) | D 先 / P 先 |", "|---|---:|---:|---:|---:|---|"]
    for f, lab in (("F1", "一体化目标值"), ("F2", "`no_new_xb` 目标值"), ("B6", "B6")):
        s = res[f]["shapley"]
        L.append(f"| {lab} | {bn(s['total'])} | {bn(s['phi_D'])} | {bn(s['phi_P'])} | {bn(s['interaction'])} | D 先: D {bn(s['D_first']['D'])} P {bn(s['D_first']['P'])}; P 先: P {bn(s['P_first']['P'])} D {bn(s['P_first']['D'])} |")
    L += ["", "## 3. 按参与者（bn EUR）", "", "| 参与者 | 量 | (D31,P31) | (D4,P31) | (D31,P4) | (D4,P4) | φ_D | φ_P |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for key in ("owen", "ledger_F1"):
        for pl in PLAYERS:
            o = own[key][pl]; v = o["values"]; s = o["shapley"]
            L.append(f"| {pl} | {o['label']} | {bn(v['D31,P31'])} | {bn(v['D4,P31'])} | {bn(v['D31,P4'])} | {bn(v['D4,P4'])} | {bn(s['phi_D'])} | {bn(s['phi_P'])} |")
    L += ["", "## 4. 近似项（(D31,P31)）", "", "| 项 | F1 | F2 | 来源 |", "|---|---:|---:|---|",
          f"| v3.1 网络冒烟目标值 | {inp['v31_objective_eur']['F1']:,.2f} | {inp['v31_objective_eur']['F2']:,.2f} | {inp['v31_source']} |"]
    for k in inp["other_v4_changes_on_v31_eur"]["F1"]:
        L.append(f"| {k} | {inp['other_v4_changes_on_v31_eur']['F1'][k]:,.2f} | {inp['other_v4_changes_on_v31_eur']['F2'][k]:,.2f} | {inp['other_v4_changes_notes'].get(k, '')} |")
    L += ["", "## 5. 读法", "", "- φ_D 与 φ_P 之和恒等于总变化；交互项（D 的边际在 P4 与 P31 下的差）衡量两因素的非可加性。",
          "- 参与者行：Owen 受益是 B6 的分摊（正 = 互联受益），一体化台账是各国在 F1 的成本份额；(D31,P31) 行来自 v3.1 冒烟的分摊 + 其他改动的按国近似。",
          "- 本表只给方向；正式归因在 2920×3h 批次上重做（Fable F-22 第 3 点）。"]
    (W / "ATTRIBUTION_56.md").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({f: {k: round(v / 1e9, 4) for k, v in res[f]["shapley"].items() if not isinstance(v, dict)} for f in res}, indent=1))


if __name__ == "__main__":
    main()
