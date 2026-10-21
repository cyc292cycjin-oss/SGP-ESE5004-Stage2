"""SYNTHETIC_TEST_ONLY stand-in for s2_solve.py / l23_violation_analysis.py / s4o_c1_precision.py in the M08a runner test (no solver).

solve: writes SOLVE_RECEIPT.json, V5_GATES.json, EXPORTS.json (+ one exported file) consistent with the network file; appends one line
to <output>/../CALLS.txt per call. c1 run: writes PRECISION.json with the flags of FAKE_C1_<scenario> ("111" default). reference / regrade:
no-op files. Environment: FAKE_TERM (termination, default optimal), FAKE_OBJ_<profile> (objective).
M12 supplement 01 additions: the receipt records the costs table; c1 run records the --reference file (or "L23 default"); reference writes a
source; regrade (D9) appends a grade_history entry, takes the flags of FAKE_C1_REGRADE_<scenario> when set and appends "regrade <dir>" to
CALLS.txt. variants (D7, stand-in for m08a_variants.py): --base / --out / --set coalition.remove_countries=[CC] -> <out>/integrated_minusCC_
365_24h_unsolved.nc (base bytes + CC) and its VARIANT_RECEIPT.json (output.sha256); refuses to run without PYTHONHASHSEED=0."""
import hashlib
import json
import os
import sys
from pathlib import Path


def arg(name, argv):
    return argv[argv.index(name) + 1] if name in argv else None


def flags(f: str) -> dict:
    return dict(a_total_cost=dict(passed=f[0] == "1"), b_primal_violations=dict(passed=f[1] == "1"), c_prices=dict(passed=f[2] == "1"))


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
                   config_subset=dict(network="s" * 64, current="s" * 64), exports=ex, costs_table=arg("--costs-table", argv))
        (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
        (out / "EXPORTS.json").write_text(json.dumps(ex))
        (out / "V5_GATES.json").write_text(json.dumps(dict(A4=dict(passed=True, status="EXACT_SEMANTIC_ROUNDTRIP"), B16_LEDGER=dict(passed=True, relative_error=1e-10),
                                                           A1_A2_S4B=dict(dual_sign_normalized_max=1e-4, stationarity_normalized_max=1e-6, row_max_ratio_to_budget=0.5))))
    elif mode == "variants":
        if os.environ.get("PYTHONHASHSEED") != "0":
            return 2
        base = Path(arg("--base", argv)); out = Path(arg("--out", argv)); out.mkdir(parents=True, exist_ok=True)
        cc = arg("--set", argv).split("=", 1)[1].strip("[]")
        net = out / f"integrated_minus{cc}_365_24h_unsolved.nc"; net.write_bytes(base.read_bytes() + cc.encode())
        with open(out.parent / "CALLS.txt", "a") as f:
            f.write(f"variant {cc} stale={'--allow-stale-base' in argv}\n")
        (out / f"integrated_minus{cc}_365_24h_VARIANT_RECEIPT.json").write_text(json.dumps(dict(
            status="M08A_VARIANT_BUILT", base=dict(path=str(base), sha256=hashlib.sha256(base.read_bytes()).hexdigest()),
            output=dict(path=str(net), sha256=hashlib.sha256(net.read_bytes()).hexdigest(), scenario="integrated"), sets={"coalition.remove_countries": [cc]})))
    elif mode == "va":
        Path(arg("--out", argv)).write_text("{}")
    elif mode == "c1":
        sub = argv[1]
        if sub == "run":
            d = Path(arg("--solve-dir", argv)); sc = arg("--scenario", argv)
            f = os.environ.get(f"FAKE_C1_{sc}", "111")
            ref = arg("--reference", argv)
            (d / "PRECISION.json").write_text(json.dumps(dict(computable=True, **flags(f), reference=dict(source=f"fake run reference {ref or 'L23 default'}"))))
        elif sub == "reference":
            Path(arg("--out", argv)).write_text(json.dumps(dict(source="fake batch reference", differences_bn={})))
        elif sub == "regrade":
            d = Path(arg("--solve-dir", argv)); P = json.loads((d / "PRECISION.json").read_text())
            P.setdefault("grade_history", []).append(dict(reference_source=(P.get("reference") or {}).get("source"),
                                                          flags="".join("1" if (P.get(k) or {}).get("passed") else "0" for k in ("a_total_cost", "b_primal_violations", "c_prices"))))
            f = os.environ.get(f"FAKE_C1_REGRADE_{d.name.split('_')[0]}")
            if f:
                P.update(flags(f))
            P["reference"] = dict(source=f"fake regrade {arg('--reference', argv)}")
            (d / "PRECISION.json").write_text(json.dumps(P))
            with open(d.parent / "CALLS.txt", "a") as fh:
                fh.write(f"regrade {d.name}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
