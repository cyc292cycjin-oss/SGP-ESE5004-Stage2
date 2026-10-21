"""M08b section 4: evaluate the local 56x3h smoke runs against the instruction's pass criteria (read-only, no solve).

    python scripts_project/m08b_smoke_eval.py --run <smoke dir with integrated/ disconnected/> --out <evidence dir>

Criteria, both runs: GATES_V6 label ACCEPTED_LAYER2 (gates_v6.py accept), B6 = objective(disconnected) - objective(integrated) > 0, ledger identity
(V5_GATES B16_LEDGER, LEDGER_IDENTITY.json), no fixed methane overflow demand (solved network loads), LNG terminals not bound by a capacity cap
(p_nom_max = inf, p_nom_opt finite), report and export files complete (EXPORTS.json members present, G2.3). Writes M08B_SMOKE_RESULT.json.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pypsa

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from v5.v5_gates import gate_b6_cost   # noqa: E402

logging.getLogger("pypsa").setLevel(logging.ERROR)
SCEN = ["integrated", "disconnected"]
REPORT_FILES = ["SOLVE_RECEIPT.json", "V5_GATES.json", "LEDGER_IDENTITY.json", "COUNTRY_COST_LEDGER.csv", "PRECISION.json", "V6_ACCEPTANCE.json", "EXPORTS.json", "GUROBI_LOG_SCRUBBED.txt"]


def jl(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def one(d: Path, sc: str) -> dict:
    rec, v5, v6, prec, exp = (jl(d / f) for f in ("SOLVE_RECEIPT.json", "V5_GATES.json", "V6_ACCEPTANCE.json", "PRECISION.json", "EXPORTS.json"))
    out = dict(termination_condition=rec.get("termination_condition"), status=rec.get("status"), objective_eur=rec.get("objective"), solve_seconds=rec.get("solve_seconds"),
               peak_rss_gib=(rec.get("peak_rss_bytes") or 0) / 2**30, truncated_to=(rec.get("input_network") or {}).get("truncated_to"), label=rec.get("label"),
               v6_label=v6.get("label"), v6_g1=v6.get("G1"), v6_g2=v6.get("G2"), c1_grade=(prec.get("grade") or {}).get("grade"), c1_accepted=(prec.get("acceptance") or {}).get("accepted"),
               ledger_identity_passed=(v5.get("B16_LEDGER") or {}).get("passed"), v5_all_passed=v5.get("all_passed"))
    missing = [f for f in REPORT_FILES if not (d / f).exists()] + [f"EXPORTS:{k}" for k in (exp or {}) if not (d / k).exists()]
    out["report_files_missing"] = missing
    solved = d / f"{sc}_SMOKE_TEST_ONLY_solved.nc"
    if solved.exists():
        n = pypsa.Network(solved)
        acc = n.loads.get("account")
        ov = int(acc.isin(["IndustryBiomassOverflowToGas", "AgricultureBiomassOverflowToGas"]).sum()) if acc is not None else None
        lng = n.generators[n.generators.carrier == "LNG import"]
        out.update(methane_overflow_loads=ov, lng_terminals=int(len(lng)), lng_p_nom_max_all_inf=bool(np.isinf(lng.p_nom_max).all()),
                   lng_p_nom_opt_gw=float(lng.p_nom_opt.sum()) / 1e3, lng_p_nom_opt_finite=bool(np.isfinite(lng.p_nom_opt).all()))
    else:
        out.update(methane_overflow_loads=None, lng_terminals=None, solved_network_missing=True)
    out["criteria"] = dict(gates_v6_accepted_layer2=out["v6_label"] == "ACCEPTED_LAYER2", ledger_identity=bool(out["ledger_identity_passed"]),
                           no_fixed_methane_overflow=out["methane_overflow_loads"] == 0,
                           lng_not_capacity_bound=bool(out.get("lng_p_nom_max_all_inf") and out.get("lng_p_nom_opt_finite")),
                           reports_and_exports_complete=not missing and bool(((v6.get("G2") or {}).get("G2_3") or {}).get("passed", not missing)))
    return out


def main():
    p = argparse.ArgumentParser(); p.add_argument("--run", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    res = {sc: one(a.run / sc, sc) for sc in SCEN}
    oi, od = res["integrated"]["objective_eur"], res["disconnected"]["objective_eur"]
    b6 = gate_b6_cost(oi, od) if (oi is not None and od is not None) else dict(passed=False, note="objective missing")
    b6_value = (od - oi) if (oi is not None and od is not None) else None
    res["B6"] = dict(gate=b6, b6_eur=b6_value, b6_bn_eur=(b6_value / 1e9 if b6_value is not None else None), positive=bool(b6_value is not None and b6_value > 0))
    res["passed"] = bool(res["B6"]["positive"] and all(all(res[sc]["criteria"].values()) for sc in SCEN))
    (a.out / "M08B_SMOKE_RESULT.json").write_text(json.dumps(res, indent=1, default=str, sort_keys=True))
    print(json.dumps({sc: res[sc]["criteria"] | dict(v6=res[sc]["v6_label"], cond=res[sc]["termination_condition"], seconds=res[sc]["solve_seconds"]) for sc in SCEN}
                     | dict(B6_bn=res["B6"]["b6_bn_eur"], passed=res["passed"]), indent=1, default=str))


if __name__ == "__main__":
    main()
