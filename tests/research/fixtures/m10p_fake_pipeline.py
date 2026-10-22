"""SYNTHETIC_TEST_ONLY stand-ins for the M10P third-batch runner (run_batch3.sh): s2_solve.py, l23_violation_analysis.py, s4o_c1_precision.py,
m12_allocation.py, m12_rhs_audit.py and m08a_variants.py. No solver, no model. Every call appends one line to <OUT>/CALLS.txt (OUT = FAKE_OUT).

solve: receipt consistent with the network file (GATES_V6 G2.1-G2.3 pass); --stop-before-solve writes the pre-solve receipt of a dry run
(parameters = the registered profile of configs/research/baseline.yaml + TimeLimit); FAKE_SLEEP_<rid> / FAKE_SLEEP seconds of "solving";
FAKE_OBJ_<rid> objective; FAKE_TERM_<rid> termination; FAKE_NOSOL_<rid>=1 -> pre-solve receipt only, exit 1; FAKE_SUBSET_<rid>=differ -> the
configuration subset hash of the receipt differs from the network's (GATES_V6 G2.2 fails: an input problem). The call line records start / end
epoch, profile, TimeLimit and the GRB_LICENSE_FILE it saw. c1 run: PRECISION.json with the flags FAKE_C1_<rid> ("111" default; not computable
without solution/X.npy or without the --violations file, as the real s4o_c1_precision.py), reference "this batch: ..." when --reference is given;
regrade appends grade_history and takes FAKE_C1_REGRADE_<rid>.
M10A fault drill hooks: FAKE_IGNORE_TERM_<rid>=1 (the solve ignores SIGTERM: only the KILL of the process group ends it); FAKE_HANG_VA_<rid>=1 /
FAKE_HANG_M12_<rid>=1 (the step sleeps 120 s: timeout drill); FAKE_RAISE_M12_<rid>=1 (M12 run exits 1 without ALLOCATION.json);
FAKE_RAISE_RHS_LOO_<rid>=1 (the leave-one-out RHS check of that run exits 1). The solve line also records the OMP_NUM_THREADS and TMPDIR it saw
(omp= / tmp=), the va line its OMP_NUM_THREADS (thread budget of the auxiliary steps).
M10A supplement 01 D2 (retry drill): FAKE_FAIL_ONCE_VA_<rid>=1 / FAKE_FAIL_ONCE_C1_<rid>=1 - the first call of that step writes an incomplete
output (not JSON) and exits 1, the second call succeeds (marker file in FAKE_OUT); FAKE_FAIL_VA_<rid>=1 / FAKE_FAIL_C1_<rid>=1 - every call fails."""
import hashlib
import json
import os
import signal
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def arg(name, argv):
    return argv[argv.index(name) + 1] if name in argv else None


def call(line):
    out = Path(os.environ["FAKE_OUT"]); out.mkdir(parents=True, exist_ok=True)
    with open(out / "CALLS.txt", "a") as f:
        f.write(line + "\n")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def flags(f):
    return dict(a_total_cost=dict(passed=f[0] == "1", returned_relative=1e-9, returned_difference_bn=1e-4), b_primal_violations=dict(passed=f[1] == "1"),
                c_prices=dict(passed=f[2] == "1"), grade=dict(grade="fake", a=f[0] == "1", b=f[1] == "1", c=f[2] == "1"),
                acceptance=dict(accepted=f == "111", optimal=True))


def register(d: Path, name: str):
    ex = json.loads((d / "EXPORTS.json").read_text()) if (d / "EXPORTS.json").exists() else {}
    ex[name] = dict(sha256=sha(d / name)); (d / "EXPORTS.json").write_text(json.dumps(ex))


def solve(argv):
    out = Path(arg("--output", argv)); net = Path(arg("--network", argv)); prof = arg("--solver-profile", argv); tl = float(arg("--time-limit", argv))
    rid = out.name; t0 = time.time(); out.mkdir(parents=True, exist_ok=True)
    import yaml
    params = dict(yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())["research"]["solver"]["profiles"][prof], TimeLimit=tl)
    snaps = int(arg("--truncate", argv) or 0) or (365 if "365_24h" in net.name else 2920)
    rec = dict(input_network=dict(path=str(net), sha256=sha(net), snapshots=snaps, truncated_to=None), scenario=arg("--scenario", argv), solver_profile=prof,
               solver_parameters=params, lp=dict(num_col=10, num_row=20, nnz=30, build_seconds=0.1),
               config_subset=dict(network="s" * 64, current=("t" if os.environ.get(f"FAKE_SUBSET_{rid}") == "differ" else "s") * 64),
               optimize_calls=0, costs_table=arg("--costs-table", argv), label=arg("--label", argv))
    if "--stop-before-solve" in argv:
        (out / "lp").mkdir(exist_ok=True); (out / "lp" / "MATH_PROBLEM.json").write_text("{}")
        rec.update(stop_before_solve=True, finished_epoch=time.time(), peak_rss_bytes=2**30)
        (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
        call(f"build {rid} {prof} {tl} {os.environ.get('GRB_LICENSE_FILE')}"); return 0
    (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
    seen = f"omp={os.environ.get('OMP_NUM_THREADS')} tmp={os.environ.get('TMPDIR')}"
    if os.environ.get(f"FAKE_IGNORE_TERM_{rid}") == "1":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(float(os.environ.get(f"FAKE_SLEEP_{rid}", os.environ.get("FAKE_SLEEP", "0.2"))))
    if os.environ.get(f"FAKE_NOSOL_{rid}") == "1":
        call(f"solve {rid} {prof} {tl} {t0:.2f} {time.time():.2f} {os.environ.get('GRB_LICENSE_FILE')} {seen} nosolution"); return 1
    (out / "solution").mkdir(exist_ok=True)
    for k, n in (("X", 10), ("Pi", 20), ("RC", 10)):
        np.save(out / "solution" / f"{k}.npy", np.zeros(n))
    led = "entity,total\n" + "".join(f"{c},{1e9 * (2 if rec['scenario'] == 'disconnected' else 1)}\n" for c in ("BN", "VN", "ASEAN_BUNKER"))
    (out / "COUNTRY_COST_LEDGER.csv").write_text(led)
    (out / f"{rec['scenario']}_{arg('--label', argv)}_solved.nc").write_bytes(b"solved")
    (out / "EXPORTS.json").write_text("{}"); register(out, "COUNTRY_COST_LEDGER.csv")
    (out / "V5_GATES.json").write_text(json.dumps(dict(A4=dict(passed=True, status="EXACT_SEMANTIC_ROUNDTRIP"), B16_LEDGER=dict(passed=True, relative_error=1e-10))))
    rec.update(solution=dict(X=dict(count=10), Pi=dict(count=20), RC=dict(count=10)), termination_condition=os.environ.get(f"FAKE_TERM_{rid}", "optimal"), status="ok",
               objective=float(os.environ.get(f"FAKE_OBJ_{rid}", "3e11" if rec["scenario"] == "disconnected" else "2e11")), optimize_calls=1,
               finished_epoch=time.time(), solve_seconds=time.time() - t0, peak_rss_bytes=2**31, exports=json.loads((out / "EXPORTS.json").read_text()))
    (out / "SOLVE_RECEIPT.json").write_text(json.dumps(rec))
    call(f"solve {rid} {prof} {tl} {t0:.2f} {time.time():.2f} {os.environ.get('GRB_LICENSE_FILE')} {seen}")
    return 0


VARIANT_TAG = {"coalition.remove_countries": lambda v: "minus" + v.strip("[]"), "disconnected.co2_shipping_intra_asean": lambda v: "noco2ship",
               "cross_border.stock_mode": lambda v: "keepstock", "finance.wacc_mode": lambda v: "wacccountry"}


def variants(argv):
    if os.environ.get("PYTHONHASHSEED") != "0":
        return 2
    base = Path(arg("--base", argv)); out = Path(arg("--out", argv)); out.mkdir(parents=True, exist_ok=True); key, val = arg("--set", argv).split("=", 1)
    scen = "disconnected" if key == "cross_border.stock_mode" else base.name.split("_")[0]
    res = "365_24h" if "365_24h" in base.name else "2920_3h"
    name = f"{scen}_{VARIANT_TAG[key](val)}"
    net = out / f"{name}_{res}_unsolved.nc"; net.write_bytes(base.read_bytes() + arg("--set", argv).encode())
    call(f"variant {out.name} {arg('--set', argv)} costs={arg('--costs', argv)} stale={'--allow-stale-base' in argv}")
    (out / f"{name}_{res}_VARIANT_RECEIPT.json").write_text(json.dumps(dict(status="M08A_VARIANT_BUILT", base=dict(path=str(base), sha256=sha(base), stale_config=False),
        output=dict(path=str(net), sha256=sha(net), bytes=net.stat().st_size, scenario=scen), sets={key: val}, research_config_sha256="r", research_config_subset_sha256="s")))
    return 0


def fail_now(step, rid, out_file):
    """M10A supplement 01 D2 drill: True when this call of <step> for <rid> must fail (always, or only the first call); writes an incomplete output."""
    if os.environ.get(f"FAKE_FAIL_{step}_{rid}") == "1":
        Path(out_file).write_text("{incomplete"); call(f"{step.lower()} {rid} fail"); return True
    if os.environ.get(f"FAKE_FAIL_ONCE_{step}_{rid}") == "1":
        marker = Path(os.environ["FAKE_OUT"]) / f".failed_once_{step}_{rid}"
        if not marker.exists():
            marker.write_text("1"); Path(out_file).write_text("{incomplete"); call(f"{step.lower()} {rid} fail"); return True
    return False


def c1(argv):
    sub = argv[0]
    if sub == "run":
        d = Path(arg("--solve-dir", argv)); ref = arg("--reference", argv); viol = arg("--violations", argv)
        if fail_now("C1", d.name, d / "PRECISION.json"):
            return 1
        if not (d / "solution" / "X.npy").exists() or not (viol and Path(viol).exists()):
            (d / "PRECISION.json").write_text(json.dumps(dict(computable=False, missing=["solution" if not (d / "solution" / "X.npy").exists() else str(viol)],
                                                              reference=dict(source="L23 fake default"))))
        else:
            P = flags(os.environ.get(f"FAKE_C1_{d.name}", "111")); P.update(computable=True, reference=dict(source=(f"this batch: fake {ref}" if ref else "L23 fake default")))
            (d / "PRECISION.json").write_text(json.dumps(P))
        call(f"c1 {d.name} ref={'batch' if ref else 'default'}")
    elif sub == "reference":
        Path(arg("--out", argv)).write_text(json.dumps(dict(source="this batch: fake reference", differences_bn={}))); call("c1_reference")
    elif sub == "regrade":
        d = Path(arg("--solve-dir", argv)); P = json.loads((d / "PRECISION.json").read_text())
        P.setdefault("grade_history", []).append(dict(reference_source=(P.get("reference") or {}).get("source"), grade="fake"))
        f = os.environ.get(f"FAKE_C1_REGRADE_{d.name}")
        if f:
            P.update(flags(f))
        P["reference"] = dict(source="this batch: fake regrade"); (d / "PRECISION.json").write_text(json.dumps(P)); call(f"regrade {d.name}")
    return 0


def m12(argv):
    sub = argv[0]
    if sub == "run":
        d = Path(arg("--solve-dir", argv))
        if os.environ.get(f"FAKE_HANG_M12_{d.name}") == "1":
            call(f"m12 {d.name} hang"); time.sleep(120)
        if os.environ.get(f"FAKE_RAISE_M12_{d.name}") == "1":
            call(f"m12 {d.name} raise"); return 1
        (d / "ALLOCATION.json").write_text(json.dumps(dict(computable=True))); register(d, "ALLOCATION.json"); call(f"m12 {d.name}")
    elif sub == "loo":
        o = Path(arg("--out", argv)); o.mkdir(parents=True, exist_ok=True)
        loo = [s.split("=", 1)[0] for i, s in enumerate(argv) if i > 0 and argv[i - 1] == "--loo"]
        (o / "LOO_CHECK.json").write_text(json.dumps(dict(check=dict(all_passed=True, indivisible_cost_sign="positive",
                                                                      countries={c: dict(margin=1e8, tolerance=1e7, passed=True, market_form_passed=True) for c in loo}))))
        call(f"m12_loo {' '.join(sorted(loo))} standalone={Path(arg('--standalone', argv)).name}")
    elif sub == "benefit":
        o = Path(arg("--out", argv)); o.mkdir(parents=True, exist_ok=True)
        (o / "BENEFIT.json").write_text(json.dumps(dict(b6_eur=1e11, owen=dict(negative_benefit=[])))); call(f"m12_benefit loo_check={'--loo-check' in argv}")
    return 0


def m12a(argv):
    sub = argv[0]
    if sub == "audit":
        d = Path(arg("--solve-dir", argv)); o = Path(arg("--out", argv)); o.mkdir(parents=True, exist_ok=True)
        (o / "OWEN.json").write_text(json.dumps(dict(alpha_main=0.5, allocation_eur={"0.5": {"BN": 1e9, "VN": 2e9, "BUNKER": 3e9}}, usable_for_allocation=True)))
        (o / "RHS_BY_FAMILY_OWNER.csv").write_text("family,owner,rhs_sum,rows\n"); call(f"m12_owen {d.name}")
    elif sub == "loo":
        rid = Path(arg("--variant", argv)).parent.parent.name
        if os.environ.get(f"FAKE_RAISE_RHS_LOO_{rid}") == "1":
            call(f"rhs_loo {rid} raise"); return 1
        o = Path(arg("--out", argv)); o.mkdir(parents=True, exist_ok=True); (o / "LOO_RHS_CHECK.json").write_text(json.dumps(dict(passed=True)))
        call(f"rhs_loo {rid} removed={arg('--removed', argv)}")
    elif sub == "regrade":
        Path(arg("--out", argv)).write_text(json.dumps(dict(new=dict(usable_for_allocation=True)))); call(f"owen_regrade {Path(arg('--owen', argv)).parent.parent.name}")
    return 0


def main():
    mode, argv = sys.argv[1], sys.argv[2:]
    if mode == "va":
        rid = Path(arg("--solve-dir", argv)).name
        if fail_now("VA", rid, arg("--out", argv)):
            return 1
        if os.environ.get(f"FAKE_HANG_VA_{rid}") == "1":
            call(f"va {rid} hang"); time.sleep(120)
        Path(arg("--out", argv)).write_text("{}"); call(f"va {rid} omp={os.environ.get('OMP_NUM_THREADS')}"); return 0
    return dict(solve=solve, variants=variants, c1=c1, m12=m12, m12a=m12a)[mode](argv)


if __name__ == "__main__":
    sys.exit(main())
