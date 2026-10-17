"""S4C-6 smoke summary (S4C instruction section S4C-6 item 2): run table, gates under the BarConvTol (S3B) and solver-tolerance (decision 71)
acceptance, capacity / generation by country (incl. SMR, hydro, geothermal, onshore / offshore wind, solar, gas power) against the S4B-5 smoke,
LNG imports and terminal caps, bunker account (S4C-3), extra-ASEAN CO2 storage (S4C-4), cross-border exports, B5 / B6 trial (B6 with the real
disconnected cost once the disconnected main is optimal). SMOKE_TEST_ONLY: 56 snapshots (2013-01-01..01-07) re-weighted to 8760 h - the wind /
solar scale cannot be judged from it (decision 47).

    python scripts_project/s4c_6_summary.py --run results_project/s4c/s4c6 --s4b5 results_project/s4b/s4b5 [--set main] [--set control]
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from s4b_5_summary import status_lines, run_row, gate_row, new_builds, net_exports, slack_penalty_cost  # noqa: E402

RUNS = ["integrated", "disconnected", "integrated_nze", "disconnected_gap"]


def solved_in(d):
    fs = sorted(Path(d).glob("*_solved.nc"))
    return fs[0] if fs else None


def lng_binding(items):
    out = {}
    for k, v in (items.get("lng_terminals") or {}).items():
        mx = v.get("max_gw")
        out[k] = dict(optimal_gw=v["optimal_gw"], existing_gw=v["existing_gw"], max_gw=mx, binding=bool(mx is not None and np.isfinite(mx) and v["optimal_gw"] >= mx * (1 - 1e-6) - 1e-6))
    return dict(terminals=out, binding_count=sum(1 for v in out.values() if v["binding"]), expansion_gw=items.get("lng_expansion_gw"), import_twh=items.get("lng_import_twh"))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", type=Path, required=True); ap.add_argument("--s4b5", type=Path, required=True)
    ap.add_argument("--set", action="append", default=None, help="solve sub-folders (solves_<set>); default 'main'")
    a = ap.parse_args(); out_dir = a.run / "analysis"; out_dir.mkdir(parents=True, exist_ok=True)
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from s4a_4_smoke_compare import tables
    from s4b_smoke_summary import system_items
    from v5.v5_gates import gate_b5_single_switch, gate_b6_cost
    from phase4_static import config
    sets = a.set or ["main"]
    res = dict(label="SMOKE_TEST_ONLY (56x3h 2013-01-01..01-07, representative weights 8760/56; decision 47) - wind / solar scale cannot be judged from 56 snapshots",
               builds={k: v for k, v in status_lines(a.run).items() if k.startswith("BUILD_")}, sets={})
    ref = solved_in(a.s4b5 / "solves" / "integrated"); nref = pypsa.Network(str(ref)) if ref else None; tref = tables(nref) if nref is not None else None
    if tref is not None:
        tref.to_csv(out_dir / "CAP_GEN_BY_COUNTRY_S4B5.csv", index=False)
    for s in sets:
        root = a.run / f"solves_{s}"; R = dict(runs=[], gates={})
        for t in RUNS:
            if (root / t / "SOLVE_RECEIPT.json").exists():
                R["runs"].append(run_row(a.run, t, s) | run_row_dir(root / t))
                g = gate_row_dir(root, t)
                if g:
                    R["gates"][t] = g
        nets = {}
        for t in RUNS:
            p = solved_in(root / t)
            if p:
                nets[t] = pypsa.Network(str(p))
        for t, n in nets.items():
            tn = tables(n); tn.to_csv(out_dir / f"CAP_GEN_BY_COUNTRY_{s}_{t}.csv", index=False)
            it = system_items(n)
            R[f"items_{t}"] = it; R[f"lng_{t}"] = lng_binding(it)
            R[f"asean_{t}"] = tn.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index")
            R[f"new_builds_{t}"] = new_builds(n).to_dict("records")
            fl = root / t / "cross_border_flows.csv"   # empty file in the disconnected scenario (no cross-border components)
            R[f"net_exports_twh_{t}"] = net_exports(fl) if fl.exists() and fl.stat().st_size > 1 else {}
            for f, key in [("BUNKER_ACCOUNT.json", "bunker_account"), ("CO2_FLOWS.json", "co2_flows"), ("EMISSIONS_BY_COUNTRY.json", "emissions")]:
                p = root / t / f
                if p.exists():
                    d = json.loads(p.read_text())
                    R[f"{key}_{t}"] = ({k: d.get(k) for k in ["by_country", "store_final_level", "asean_total", "every_tonne_booked_once"]} if key == "emissions" else
                                       ({k: d.get(k) for k in ["extra_asean_by_country", "sequestered_by_country", "cross_border_pipeline", "dac_by_country"]} if key == "co2_flows" else d))
            if tref is not None:
                m = tn.merge(tref, on=["group", "country"], how="outer", suffixes=("_S4C6", "_S4B5")).fillna(0.0)
                m["d_gw"] = m["gw_S4C6"] - m["gw_S4B5"]; m["d_twh"] = m["twh_S4C6"] - m["twh_S4B5"]
                m.to_csv(out_dir / f"CAP_GEN_BY_COUNTRY_{s}_{t}_VS_S4B5.csv", index=False)
        if nref is not None:
            R["items_S4B5_integrated"] = system_items(nref); R["asean_S4B5_integrated"] = tref.groupby("group")[["gw", "twh"]].sum().round(3).to_dict("index")
        if "integrated" in nets and "disconnected" in nets:
            ni, nd = nets["integrated"], nets["disconnected"]
            b5 = gate_b5_single_switch(config(HERE.parent, "integrated"), config(HERE.parent, "disconnected"), n_dis_solved=nd, n_int_solved=ni)
            R["B5_trial"] = b5
            R["B6_trial"] = dict(real=gate_b6_cost(float(ni.objective), float(nd.objective), "integrated", "disconnected"),
                                 note="trial on the 56-snapshot smoke: the disconnected main is solved (extra-ASEAN CO2 storage on), so B6 uses the real disconnected cost")
        if "integrated" in nets and "disconnected_gap" in nets:
            ng = nets["disconnected_gap"]; gt = json.loads((root / "disconnected_gap" / "GAP_TABLE.json").read_text()) if (root / "disconnected_gap" / "GAP_TABLE.json").exists() else {}
            R["gap_table_disconnected_gap"] = gt; R["slack_cost_disconnected_gap"] = slack_penalty_cost(ng, gt)
        res["sets"][s] = R
    (out_dir / "S4C6_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    for s, R in res["sets"].items():
        if R["runs"]:
            print(s); print(pd.DataFrame(R["runs"])[["run", "termination", "objective_eur", "num_col", "nnz", "barrier_iterations", "barrier_seconds", "solve_seconds", "peak_rss_gib_receipt"]].to_string())
        for t, g in R["gates"].items():
            print(s, t, {k: g.get(k) for k in ["all_passed_barconvtol", "all_passed_solver_tolerances"]})
        print(s, "B6", json.dumps(R.get("B6_trial", {}).get("real"), default=str)[:400])


def run_row_dir(d):
    """run_row for a solve folder outside <run>/solves (fields from the receipt only)."""
    import re
    rec = Path(d) / "SOLVE_RECEIPT.json"
    if not rec.exists():
        return {}
    r = json.loads(rec.read_text()); lp = r.get("lp") or {}; gl = r.get("gurobi_log_stats") or {}
    bar = " ".join((gl.get("lines") or {}).get("barrier", [])); m = re.search(r"in (\d+) iterations and ([\d.]+) seconds", bar)
    cs = (gl.get("coefficient_statistics") or {}).get("matrix") or {}
    return dict(termination=r.get("termination_condition"), objective_eur=r.get("objective"), num_col=lp.get("num_col"), num_row=lp.get("num_row"), nnz=lp.get("nnz"),
                barrier_iterations=(int(m.group(1)) if m else None), barrier_seconds=(float(m.group(2)) if m else None), solve_seconds=r.get("solve_seconds"),
                peak_rss_gib_receipt=(r.get("peak_rss_bytes") or 0) / 2**30, matrix_min=cs.get("min"), matrix_max=cs.get("max"), solver_profile=r.get("solver_profile"),
                kvl=(r.get("scaling") or {}).get("kirchhoff_row_normalisation", {}).get("applied"))


def gate_row_dir(root, t):
    import s4b_5_summary as S
    return S.gate_row(root.parent if root.name == "solves" else _Shim(root), t)


class _Shim:
    """gate_row expects <run>/solves/<tag>; map it onto <run>/solves_<set>/<tag>."""
    def __init__(self, root):
        self.root = root

    def __truediv__(self, other):
        return self.root if other == "solves" else self.root / other


if __name__ == "__main__":
    main()
