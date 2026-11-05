"""V3 DIAG: constraint-container index of a window build (no solver). The build is redone as in iis_map.py (identical label vectors checked);
every row label of the LP gets the index of its linopy constraint container -> <build dir>/lp_groups.npz (names, row_group aligned with lp/clabels.npy),
plus a JSON summary (rows per container, sense counts). Used by del_probe.py for the group deletion filter.

    python con_groups.py --build-dir <dir> --scratch <new dir> --out-json <summary.json>
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diag_build as D  # noqa: E402
from iis_map import sha  # noqa: E402


def main(a):
    bdir, scratch = Path(a.build_dir), Path(a.scratch)
    win = json.loads((bdir / "DIAG_WINDOW.json").read_text())
    sargs = list(win["s2_solve_args"]); o = sargs.index("--output"); sargs[o + 1] = str(scratch)
    scratch.mkdir(parents=True, exist_ok=False)
    q = D.argparse.ArgumentParser()
    q.add_argument("--repo", type=Path, default=D.s2_solve.HERE.parent); q.add_argument("--network", type=Path, required=True); q.add_argument("--scenario", required=True); q.add_argument("--output", type=Path, required=True)
    q.add_argument("--solver-profile", default=None); q.add_argument("--scaling", choices=["on", "off"], default=None); q.add_argument("--kvl-norm", choices=["on", "off"], default=None)
    q.add_argument("--costs-table", type=Path, default=None); q.add_argument("--solver", choices=["highs", "gurobi"], default="highs"); q.add_argument("--truncate", type=int, default=0)
    q.add_argument("--label", default="SMOKE_TEST_ONLY"); q.add_argument("--authorization", required=True); q.add_argument("--time-limit", type=float, default=3600.0); q.add_argument("--highs-ipm", action="store_true")
    q.add_argument("--stop-before-solve", action="store_true"); q.add_argument("--split-stage", choices=["build", "assign"], default=None)
    sa = q.parse_args(sargs)
    D.STATE.update(target=str(sa.network), start=int(win["window_start"]), len=int(win["window_len"]))
    if D.s2_solve.main(sa) != 0:
        raise SystemExit("rebuild failed")
    same = {k: sha(scratch / "lp" / f"{k}.npy") == sha(bdir / "lp" / f"{k}.npy") for k in ("vlabels", "clabels")}
    if not all(same.values()):
        raise SystemExit(f"rebuild differs: {same}")
    m = D.STATE["m"]
    cl = np.load(bdir / "lp" / "clabels.npy"); top = int(cl.max()) + 1
    grp = np.full(top, -1, dtype=np.int32); names = []
    summary = {}
    for i, (name, con) in enumerate(m.constraints.items()):
        lab = np.ravel(np.asarray(con.labels)); lab = lab[lab >= 0]
        grp[lab] = i; names.append(str(name))
        sg = np.ravel(np.asarray(con.data["sign"])) if "sign" in con.data else np.array([])
        summary[str(name)] = dict(rows=int(len(lab)), dims=[str(d) for d in con.labels.dims], sign=sorted(set(map(str, np.unique(sg)))) if len(sg) else [])
    row_group = grp[cl]
    np.savez(bdir / "lp_groups.npz", names=np.array(names), row_group=row_group)
    json.dump(dict(build_dir=str(bdir), rebuild_identical=same, containers=len(names), rows_unassigned=int((row_group < 0).sum()), by_container=summary), open(a.out_json, "w"), indent=1)
    shutil.rmtree(scratch)
    print(json.dumps(dict(containers=len(names), rows=int(len(row_group)), unassigned=int((row_group < 0).sum()))))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--build-dir", required=True); p.add_argument("--scratch", required=True); p.add_argument("--out-json", required=True)
    main(p.parse_args())
