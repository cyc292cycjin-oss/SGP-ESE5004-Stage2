"""V3 DIAG step 3: map an IIS (iis_lp.py) back to linopy names, PyPSA components, buses, countries and snapshots - no solver, no licence.

The window build is redone exactly as the build that wrote the problem file (diag_build.py: package network, window, s2_solve.main with the
recorded arguments) into a scratch folder; its label vectors must equal the build's lp/vlabels.npy and lp/clabels.npy (deterministic build).
The model object is then the one whose LP Gurobi read (store energy scaling and KVL row normalisation applied by main before the problem file),
so Model.constraints.print_labels (= the body of Model.print_infeasibilities) shows the coefficients Gurobi saw.

    python iis_map.py --iis-dir <dir with IIS_LP.json, iis.ilp> --build-dir <build dir> --scratch <new dir>
"""
import argparse
import collections
import contextlib
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diag_build as D  # noqa: E402  (installs the window class and the problem-file capture)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(a):
    idir, bdir, scratch = Path(a.iis_dir), Path(a.build_dir), Path(a.scratch)
    iis = json.loads((idir / "IIS_LP.json").read_text())
    win = json.loads((bdir / "DIAG_WINDOW.json").read_text())
    sargs = list(win["s2_solve_args"])
    o = sargs.index("--output"); sargs[o + 1] = str(scratch)
    scratch.mkdir(parents=True, exist_ok=False)
    q = D.argparse.ArgumentParser()
    q.add_argument("--repo", type=Path, default=D.s2_solve.HERE.parent); q.add_argument("--network", type=Path, required=True); q.add_argument("--scenario", required=True); q.add_argument("--output", type=Path, required=True)
    q.add_argument("--solver-profile", default=None); q.add_argument("--scaling", choices=["on", "off"], default=None); q.add_argument("--kvl-norm", choices=["on", "off"], default=None)
    q.add_argument("--costs-table", type=Path, default=None); q.add_argument("--solver", choices=["highs", "gurobi"], default="highs"); q.add_argument("--truncate", type=int, default=0)
    q.add_argument("--label", default="SMOKE_TEST_ONLY"); q.add_argument("--authorization", required=True); q.add_argument("--time-limit", type=float, default=3600.0); q.add_argument("--highs-ipm", action="store_true")
    q.add_argument("--stop-before-solve", action="store_true"); q.add_argument("--split-stage", choices=["build", "assign"], default=None)
    sa = q.parse_args(sargs)
    D.STATE.update(target=str(sa.network), start=int(win["window_start"]), len=int(win["window_len"]))
    rc = D.s2_solve.main(sa)
    if rc != 0:
        raise SystemExit(f"rebuild failed rc={rc}")
    same = {k: sha(scratch / "lp" / f"{k}.npy") == sha(bdir / "lp" / f"{k}.npy") for k in ("vlabels", "clabels")}
    same["problem_lp"] = (sha(scratch / "split" / "problem.lp") == json.loads((bdir / "split" / "SPLIT_BUILD.json").read_text())["problem_sha256"])
    if not all(same.values()):
        raise SystemExit(f"rebuild differs from the build: {same}")
    n, m = D.STATE["n"], D.STATE["m"]
    labels = [int(x) for x in iis.get("iis_constraint_labels", [])]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m.constraints.print_labels(labels)
    (idir / "IIS_PRINT.txt").write_text(buf.getvalue())
    mapping = D.map_iis(n, m, labels, idir / "iis.ilp")
    by_con = collections.Counter(c["constraint"] for c in mapping["constraints"])
    by_var = collections.Counter(t["variable"] for c in mapping["constraints"] for t in c.get("terms", []))
    by_country = collections.Counter(); by_carrier = collections.Counter(); by_snap = collections.Counter()
    for c in mapping["constraints"]:
        for k, v in c["coords"].items():
            if k.endswith("@"):
                by_country[v.get("country", "?")] += 1; by_carrier[v.get("carrier", "?")] += 1
            if k == "snapshot":
                by_snap[v] += 1
    out = dict(iis_dir=str(idir), build_dir=str(bdir), rebuild_identical=same, window=[win["window_start"], win["window_end_excl"]], first=win["first_snapshot"], last=win["last_snapshot"],
               iis_constraints=len(labels), iis_bound_vars=len(iis.get("iis_bound_var_labels", [])), by_constraint=dict(by_con.most_common()), by_variable_in_terms=dict(by_var.most_common()),
               by_country=dict(by_country.most_common()), by_carrier=dict(by_carrier.most_common()), by_snapshot=dict(sorted(by_snap.items())), mapping=mapping)
    (idir / "IIS_MAP.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    shutil.rmtree(scratch)   # scratch rebuild (identical to the build by SHA256); not evidence
    print(json.dumps(dict(rebuild_identical=same, iis_constraints=len(labels), by_constraint=dict(by_con.most_common(20)), by_country=dict(by_country.most_common()), by_carrier=dict(by_carrier.most_common(20)))))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--iis-dir", required=True); p.add_argument("--build-dir", required=True); p.add_argument("--scratch", required=True)
    main(p.parse_args())
