"""V3 DIAG: the bunker account of a window build (no solver). Rebuilt as in con_groups.py (identical label vectors checked); writes
<build dir>/bunker_labels.json with the LP labels of: the row research_bunker_co2_limit, the Store-e / Store-p columns of 'co2 bunkers ASEAN',
the Link-p columns of every link with a port on the account (the fossil kerosene meters), and the nodal-balance rows of the account bus;
plus the port coefficients, the meters' final buses and the other feeders of those buses (the non-fossil twins). Also a JSON copy in evidence.

    python bunker_labels.py --build-dir <dir> --scratch <new dir> --out-json <evidence json>
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

BUS = "co2 bunkers ASEAN"; ROW = "research_bunker_co2_limit"


def labs(x):
    a = np.ravel(np.asarray(x.labels)); return [int(v) for v in a[a >= 0]]


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
    n, m = D.STATE["n"], D.STATE["m"]
    ports = []
    for col in [c for c in n.links.columns if c.startswith("bus") and c[3:].isdigit()]:
        for x in n.links.index[n.links[col] == BUS]:
            eff = "efficiency" if col == "bus1" else "efficiency" + col[3:]
            ports.append(dict(link=str(x), port=col, coefficient=float(n.links.at[x, eff]), bus0=str(n.links.at[x, "bus0"]), bus1=str(n.links.at[x, "bus1"]),
                              carrier=str(n.links.at[x, "carrier"]), p_nom=float(n.links.at[x, "p_nom"]), p_nom_extendable=bool(n.links.at[x, "p_nom_extendable"])))
    meters = [p["link"] for p in ports]
    finals = sorted({p["bus1"] for p in ports})
    twins = {fb: [str(x) for x in n.links.index[(n.links.bus1 == fb) & ~n.links.index.isin(meters)]] for fb in finals}
    loads = {fb: [dict(load=str(l), p_set_mean=float(n.get_switchable_as_dense("Load", "p_set")[l].mean())) for l in n.loads.index[n.loads.bus == fb]] for fb in finals}
    pvar = m.variables["Link-p"].sel(Link=meters)
    out = dict(build_dir=str(bdir), rebuild_identical=same, window=[win["window_start"], win["window_end_excl"]], ports=ports, finals=finals, twins=twins, loads=loads,
               row_label=labs(m.constraints[ROW]), store_e_labels=labs(m.variables["Store-e"].sel(Store=BUS)), store_p_labels=labs(m.variables["Store-p"].sel(Store=BUS)),
               meter_p_labels=labs(pvar), store=dict((k, str(v)) for k, v in n.stores.loc[BUS].items()),
               scaled_store=bool(any(BUS in str(k) for k in (n.meta.get("research_store_energy_scaling") or {}))))
    (bdir / "bunker_labels.json").write_text(json.dumps(out, indent=1) + "\n")
    small = {k: v for k, v in out.items() if k not in ("meter_p_labels", "store_e_labels", "store_p_labels")}
    small.update(meter_p_count=len(out["meter_p_labels"]), store_e_count=len(out["store_e_labels"]))
    Path(a.out_json).write_text(json.dumps(small, indent=1) + "\n")
    shutil.rmtree(scratch)
    print(json.dumps(dict(ports=len(ports), meter_p=len(out["meter_p_labels"]), row=out["row_label"], twins={k: len(v) for k, v in twins.items()})))


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--build-dir", required=True); p.add_argument("--scratch", required=True); p.add_argument("--out-json", required=True)
    main(p.parse_args())
