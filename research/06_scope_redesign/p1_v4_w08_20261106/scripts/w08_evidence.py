"""W08: EVIDENCE.json (every number with status EXACT / VERIFIED / INFERENCE / PROPOSED and data grade A-E) from the W08 tables and evidence files.

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_evidence.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
R = Path("/home/jin/wt_v4_w08")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    rows = []
    add = lambda k, v, unit, st, gr, src, note="": rows.append(dict(id=k, value=v, unit=unit, status=st, grade=gr, source=src, note=note))   # noqa: E731
    add("instruction.sha256", sha(W / "V4_W08_INSTRUCTION.md"), "sha256", "VERIFIED", "-", "V4_W08_INSTRUCTION.md", "= V4_W08_SHA256.txt")
    ref = json.loads((W / "evidence/W08_ref.json").read_text())
    add("reference.copy_check", dict(i2chk=ref["copy_check_i2chk_vs_i2_S1_S7_TWh"], iid_S0_S1=ref["copy_check_iid_S0_S1_vs_i2_TWh"]), "TWh (max abs T, other)", "EXACT", "-",
        "evidence/W08_ref.json", "reference engine without the two changes = I2")
    for run in ("MAIN", "IID"):
        t = pd.read_csv(W / f"REFERENCE_V4_{run}.csv")
        for r in t[(t.step == "S7")].itertuples():
            add(f"reference.{run.lower()}.S7.{r.country}", dict(T_v2=r.T_v2_2050_TWh, other=r.other_2050_TWh, share=r.other_share), "TWh", "PROPOSED", "C",
                f"REFERENCE_V4_{run}.csv", "decision 211 reference (quantified)")
    c = pd.read_csv(W / "CHECKPOINTS.csv")
    for run, g in c.groupby("run"):
        add(f"checkpoints.{run}", dict(steps=sorted(g.step.unique().tolist()), max_abs_diff_T_TWh=float(g.diff_T_TWh.abs().max()), all_within_1e6=bool(g.within_1e6.all())),
            "TWh", "EXACT", "-", "CHECKPOINTS.csv", "repository chain vs reference engine (A0 / A1)")
    st = json.loads((W / "STATIC_CHECKS.json").read_text())
    for k, v in st.items():
        add(f"static.{k}", {kk: vv for kk, vv in v.items() if not isinstance(vv, (dict, list))}, "-", "VERIFIED", "-", "STATIC_CHECKS.json")
    zs = json.loads((W / "evidence/ZERO_SLACK_CHECK_V4.json").read_text())
    add("static.zero_slack_gate", zs.get("result", zs.get("passed", zs.get("summary"))), "-", "VERIFIED", "-", "evidence/ZERO_SLACK_CHECK_V4.json")
    fo = json.loads((W / "evidence/W08_first_order.json").read_text())["pairs"]
    for k, v in fo.items():
        if k == "substitute_valuation":
            add("first_order.substitute_valuation", v, "EUR/MWh", "INFERENCE", "C", "evidence/W08_first_order.json"); continue
        add(f"first_order.{k}", dict(estimate_eur=v["first_order_delta_eur"], band_eur=v["band_eur"], raw_dual_eur=v["first_order_delta_raw_dual_eur"], by_term=v["by_term"]),
            "EUR", "INFERENCE", "C", "evidence/W08_first_order.json", "registered before any W08 solve")
    sm = W / "evidence/W08_smoke56.json"
    if sm.exists():
        s = json.loads(sm.read_text())
        for k, v in s["runs"].items():
            add(f"smoke56.{k}", {kk: vv for kk, vv in v.items() if kk != "gates"}, "-", "VERIFIED", "-", "evidence/W08_smoke56.json (SOLVE_RECEIPT / V5_GATES / PRECISION / V6)")
        add("smoke56.criteria", s["criteria"], "-", "VERIFIED", "-", "evidence/W08_smoke56.json")
    br = W / "evidence/W08_bracket.json"
    if br.exists():
        for k, v in json.loads(br.read_text())["pairs"].items():
            add(f"smoke56.bracket.{k}", dict(lower_eur=v["lower_bound_v31_duals_eur"], solved_eur=v["solved_delta_eur"], upper_eur=v["upper_bound_v4_duals_eur"],
                                             inside=v["inside"], upper_terms=v["upper_terms"], unpriced_upper_mwh=v["unpriced_upper_mwh"]),
                "EUR", "EXACT", "-", "evidence/W08_bracket.json", "LP convexity rule with VERIFIED duals; completion of removed components INFERENCE")
    rg = W / "evidence/W08_pool_regime.json"
    if rg.exists():
        add("smoke56.pool_duals", json.loads(rg.read_text())["pairs"], "EUR/MWh, TWh", "VERIFIED", "-", "evidence/W08_pool_regime.json")
    hp = W / "tables/W08_SMOKE56_HEAT_PRICES.csv"
    if hp.exists():
        h = pd.read_csv(hp)
        add("smoke56.heat_prices", h.round(4).to_dict("records"), "EUR/MWh, TWh", "VERIFIED", "-", "tables/W08_SMOKE56_HEAT_PRICES.csv",
            "price drop with demand = second-order term of the cost difference (INFERENCE)")
    ft = W / "logs/full_tests.txt"
    if ft.exists():
        add("tests.full_tests_research", ft.read_text().strip().splitlines()[-2:], "-", "VERIFIED", "-", "logs/full_tests.txt (scripts/full_tests.sh)")
    oc = W / "tables/W08_OUTPUT_CHECKS.json"
    if oc.exists():
        add("outputs.checks_vs_I2", json.loads(oc.read_text()), "-", "EXACT", "-", "tables/W08_OUTPUT_CHECKS.json")
    reg = pd.read_csv(R / "research_inputs/registry_v5/fragments/v4_w08.csv", dtype=str, keep_default_na=False)
    add("registry.fragment_rows", int(len(reg)), "rows", "VERIFIED", "-", "research_inputs/registry_v5/fragments/v4_w08.csv")
    head = subprocess.run(["git", "-C", str(R), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    add("git.head_at_evidence", head, "sha", "VERIFIED", "-", "git rev-parse HEAD (worktree)")
    files = {p.relative_to(W).as_posix(): sha(p) for p in sorted(W.rglob("*")) if p.is_file() and p.suffix != ".zip" and "logs" not in p.parts and p.name != "EVIDENCE.json"
             and not p.name.startswith("msg_")}
    (W / "EVIDENCE.json").write_text(json.dumps(dict(schema="v4-w08-evidence-1", n=len(rows), entries=rows, files=files), indent=1, ensure_ascii=False, default=str) + "\n",
                                     encoding="utf-8")
    print(len(rows), "entries,", len(files), "files")


if __name__ == "__main__":
    main()
