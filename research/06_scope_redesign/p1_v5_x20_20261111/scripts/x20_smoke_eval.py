"""X20 §3 第 6 步的整理（不求解，只读回执）：v5 56 时段回归 F1 / F2 与 v4 同截取冒烟（D2c smoke56，W14 冒烟的期望值）对照——
是否 optimal、目标值与差、求解时长与峰值、V6 验收标签、停止分类、Owen 前提与恒等式、各国 Owen 分摊（α 0.5）与受益（F2 − F1）的符号。
按指令不对 56 时段结果作任何数量结论；数值只作记录。只读许可证无关字段。
用法：python x20_smoke_eval.py   输出 evidence/SMOKE56_V5_RESULTS.json、SMOKE56_OWEN_SIGNS_V5.csv"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
RP = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4d2c/smoke56")
RUNS = dict(F1=(D / "smoke56/F1", RP / "v4d2c_F1"), F2=(D / "smoke56/F2", RP / "v4d2c_F2"))
W14_EXPECTED = dict(F1=363190038821.0828, F2=376143650003.4369)   # W14 HPC package smoke expectation = D2c smoke objectives (W14 §2.3)
PLAYERS = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER"]


def jl(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:   # noqa: BLE001
        return None


def sign(x, tol=1e3):
    if x is None:
        return None
    return "+" if x > tol else ("-" if x < -tol else "0")


def run(d: Path) -> dict:
    r = jl(d / "SOLVE_RECEIPT.json") or {}
    o = jl(d / "m12_owen/OWEN.json") or {}
    v6 = jl(d / "V6_ACCEPTANCE.json") or {}
    sc = jl(d / "STOP_CLASS.json") or {}
    pr = jl(d / "PRECISION.json") or {}
    alloc = (o.get("allocation_eur") or {}).get("0.5") or {}
    return dict(termination=r.get("termination_condition"), status=r.get("status"), objective=r.get("objective"), objective_lp=r.get("objective_lp"),
                solve_seconds=r.get("solve_seconds"), peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30, input_network_sha256=(r.get("input_network") or {}).get("sha256"),
                optimize_calls=r.get("optimize_calls"), retry=r.get("retry"), decision=r.get("decision"),
                v6_label=v6.get("label") or v6.get("acceptance") or v6.get("decision"), stop_class=sc.get("cls") or sc.get("class"), stop_action=sc.get("action"),
                precision_grade=pr.get("grade"), precision_c_passed=pr.get("c_passed"),
                owen_premise_passed=(o.get("premise") or {}).get("passed"), owen_identity=(o.get("identity") or {}), owen_dual_acceptance_passed=(o.get("c1_c_dual") or {}).get("passed"),
                owen_bunker_standalone_passed=(o.get("bunker_standalone") or {}).get("passed"), owen_usable=o.get("usable_for_allocation"),
                owen_allocation_alpha_half_eur={p: alloc.get(p) for p in PLAYERS})


res, rows = {}, []
for rid, (v5d, v4d) in RUNS.items():
    a, b = run(v5d), run(v4d)
    res[rid] = dict(v5=a, v4_d2c=b, objective_minus_v4_eur=(a["objective"] - b["objective"]) if a["objective"] and b["objective"] else None,
                    objective_rel_vs_v4=((a["objective"] / b["objective"]) - 1.0) if a["objective"] and b["objective"] else None,
                    v4_objective_equals_w14_expected=b["objective"] == W14_EXPECTED[rid])
    for p in PLAYERS:
        x, y = a["owen_allocation_alpha_half_eur"].get(p), b["owen_allocation_alpha_half_eur"].get(p)
        rows.append(dict(run=rid, player=p, quantity="Owen allocation alpha 0.5", v4_d2c_eur=y, v5_eur=x, v4_sign=sign(y), v5_sign=sign(x)))
bn5, bn4 = jl(D / "smoke56/M12_BENEFIT/BENEFIT.json") or {}, jl(RP / "M12_BENEFIT/BENEFIT.json") or {}
res["B6"] = dict(v5=bn5.get("b6_eur"), v4_d2c=bn4.get("b6_eur"))
for p in PLAYERS:
    def ben(bb):
        ow = bb.get("owen") or {}
        v = (ow.get("benefit_eur") or {}).get(p); iv = (ow.get("benefit_interval_eur") or {}).get(p) or {}
        return v, iv.get("min"), iv.get("max")
    x, xl, xh = ben(bn5); y, yl, yh = ben(bn4)
    rows.append(dict(run="F2-F1", player=p, quantity="Owen benefit alpha 0.5 (disconnected - integrated)", v4_d2c_eur=y, v5_eur=x, v4_sign=sign(y), v5_sign=sign(x),
                     v4_interval_signs=f"{sign(yl)}/{sign(yh)}", v5_interval_signs=f"{sign(xl)}/{sign(xh)}"))
t = pd.DataFrame(rows); t.to_csv(D / "SMOKE56_OWEN_SIGNS_V5.csv", index=False, lineterminator="\n")
res["owen_sign_changes"] = t[(t.v4_sign != t.v5_sign)][["run", "player", "quantity", "v4_sign", "v5_sign"]].to_dict("records")
# new-build hydro (research_new_hydro_inflow_tie candidates) built in the 56-snapshot solutions, v5 vs v4 (L-C10 signal; record only)
import pypsa   # noqa: E402
hy = []
for rid, (v5d, v4d) in RUNS.items():
    for lab, d in (("v5", v5d), ("v4_d2c", v4d)):
        f = sorted(d.glob("*_SMOKE_TEST_ONLY_solved.nc"))
        if not f:
            continue
        n = pypsa.Network(str(f[0])); su = n.storage_units; su = su[su.index.str.endswith("hydro_new")]
        g = su.assign(country=su.bus.map(n.buses.country)).groupby("country").agg(cap_mw=("p_nom_max", "sum"), built_mw=("p_nom_opt", "sum"))
        for c, r in g.iterrows():
            hy.append(dict(run=rid, set=lab, country=c, new_hydro_cap_mw=float(r.cap_mw), new_hydro_built_mw=float(r.built_mw), built_share=float(r.built_mw / r.cap_mw) if r.cap_mw else None))
        del n
H = pd.DataFrame(hy); H.to_csv(D / "evidence/SMOKE56_NEW_HYDRO_BUILT.csv", index=False, lineterminator="\n")
res["new_hydro_built"] = H.pivot_table(index=["run", "country"], columns="set", values="new_hydro_built_mw").round(1).reset_index().to_dict("records") if len(H) else None
res["note"] = "SMOKE_TEST_ONLY: no quantitative conclusion is drawn from the 56-snapshot runs (instruction section 3 step 6)"
(D / "evidence/SMOKE56_V5_RESULTS.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
print(json.dumps({k: v for k, v in res.items() if k in ("F1", "F2")}, indent=1, default=str)[:5000])
print("B6", res["B6"]); print("sign changes", res["owen_sign_changes"])
print(t.to_string())
