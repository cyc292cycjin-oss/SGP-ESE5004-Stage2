"""SYNTHETIC_TEST_ONLY stand-in for s2_solve.py / l23_violation_analysis.py / s4o_c1_precision.py in the M08a runner test (no solver).

solve: writes SOLVE_RECEIPT.json, V5_GATES.json, EXPORTS.json (+ one exported file) consistent with the network file; appends one line
to <output>/../CALLS.txt per call. c1 run: writes PRECISION.json with the flags of FAKE_C1_<scenario> ("111" default). reference / regrade:
no-op files. Environment: FAKE_TERM (termination, default optimal), FAKE_OBJ_<profile> (objective)."""
import hashlib
import json
import os
import sys
from pathlib import Path


def arg(name, argv):
    return argv[argv.index(name) + 1] if name in argv else None


def main():
    argv = sys.argv[1:]
    mode = argv[0]
    if mode == "solve":
        out = Path(arg("--output", argv)); net = Path(arg("--network", argv)); prof = arg("--solver-profile", argv); tl = arg("--time-limit", argv)
        out.mkdir(parents=True, exist_ok=True)
        with open(out.parent / "CALLS.txt", "a") as f:
            f.write(f"solve {out.name} {prof} {tl}\n")
        sha = hashlib.sha256(net.read_bytes()).hexdigest()
        (out / "COUNTRY_COST_LEDGER.csv").write_text("entity,total\nVN,1\n")
        ex = {"COUNTRY_COST_LEDGER.csv": dict(sha256=hashlib.sha256((out / "COUNTRY_COST_LEDGER.csv").read_bytes()).hexdigest())}
        rec = dict(input_network=dict(path=str(net), sha256=sha, snapshots=(365 if "365_24h" in net.name else 2920)), lp=dict(num_col=10, num_row=20, nnz=30),
                   solution=dict(X=dict(count=10), Pi=dict(count=20), RC=dict(count=10)), solver_profile=prof,
                   solver_parameters=dict(BarConvTol=(1e-6 if prof.endswith("1e6_t16") else 1e-8), TimeLimit=float(tl)),
                   termination_condition=os.environ.get("FAKE_TERM", "optimal"), status="ok", objective=float(os.environ.get(f"FAKE_OBJ_{prof}", "1000000.0")),
                   config_subset=dict(network="s" * 64, current="s" * 64), exports=ex)
        (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
        (out / "EXPORTS.json").write_text(json.dumps(ex))
        (out / "V5_GATES.json").write_text(json.dumps(dict(A4=dict(passed=True, status="EXACT_SEMANTIC_ROUNDTRIP"), B16_LEDGER=dict(passed=True, relative_error=1e-10),
                                                           A1_A2_S4B=dict(dual_sign_normalized_max=1e-4, stationarity_normalized_max=1e-6, row_max_ratio_to_budget=0.5))))
    elif mode == "va":
        Path(arg("--out", argv)).write_text("{}")
    elif mode == "c1":
        sub = argv[1]
        if sub == "run":
            d = Path(arg("--solve-dir", argv)); sc = arg("--scenario", argv)
            f = os.environ.get(f"FAKE_C1_{sc}", "111")
            (d / "PRECISION.json").write_text(json.dumps(dict(computable=True, a_total_cost=dict(passed=f[0] == "1"), b_primal_violations=dict(passed=f[1] == "1"),
                                                            c_prices=dict(passed=f[2] == "1"), reference=dict(source="fake"))))
        elif sub == "reference":
            Path(arg("--out", argv)).write_text("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
