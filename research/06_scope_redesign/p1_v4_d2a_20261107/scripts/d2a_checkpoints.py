"""V4 D2a section 2 / 5 (copy of D1 scripts/d1_checkpoints.py with the F-02 fields): repository checkpoints (scripts_project/v4_industry.py --checkpoints)
against the corrected reference engine (scripts/ref, d2a_ref_run.py).

    python scripts/d2a_checkpoints.py <repo checkpoint folder> <reference results folder> <run label> [--steps S0,S1,S2]

Appends / replaces the rows of <run label> in CHECKPOINTS.csv (delivery folder): per step x country T_v2 (reference, repository, difference), 'other' and
the largest carrier difference (T and 'other'), the overflow after the conservation layer (F-02; both engines), the s3_0 overflow kept for the record,
the agriculture overflow and the cap; tolerance 1e-6 TWh (A1) on T / other / carriers / overflow / cap. Exit 1 if any difference exceeds it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
TOL_TWH = 1e-6


def main():
    rep, ref, run = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    steps = sys.argv[sys.argv.index("--steps") + 1].split(",") if "--steps" in sys.argv else sorted(p.stem[5:] for p in rep.glob("step_*.json"))
    rows = []
    for s in steps:
        a = json.loads((rep / f"step_{s}.json").read_text()); b = json.loads((ref / f"step_{s}.json").read_text())
        for c in sorted(b["countries"]):
            x, y = a["countries"][c], b["countries"][c]
            dT = (x["T"] - y["T"]) / 1e6; dO = (x["other"] - y["other"]) / 1e6
            dcar = max(abs(x["T_car"].get(k, 0.0) - v) for k, v in y["T_car"].items()) / 1e6
            dcar_o = max(abs(x["other_car"].get(k, 0.0) - v) for k, v in y["other_car"].items()) / 1e6
            d_ov = (x["overflow"] - y["overflow"]) / 1e6; d_ova = (x.get("overflow_agriculture", 0.0) - y.get("overflow_agriculture", 0.0)) / 1e6
            d_cap = (x["pot"] - y["pot"]) / 1e6
            rows.append(dict(run=run, step=s, country=c, T_v2_ref_TWh=y["T"] / 1e6, T_v2_repo_TWh=x["T"] / 1e6, diff_T_TWh=dT, other_ref_TWh=y["other"] / 1e6,
                             other_repo_TWh=x["other"] / 1e6, diff_other_TWh=dO, max_carrier_diff_T_TWh=dcar, max_carrier_diff_other_TWh=dcar_o,
                             overflow_ref_TWh=y["overflow"] / 1e6, overflow_repo_TWh=x["overflow"] / 1e6, diff_overflow_TWh=d_ov,
                             overflow_s30_ref_TWh=y.get("overflow_s30", float("nan")) / 1e6, overflow_s30_repo_TWh=x.get("overflow_s30", float("nan")) / 1e6,
                             diff_overflow_agriculture_TWh=d_ova, cap_ref_TWh=y["pot"] / 1e6, diff_cap_TWh=d_cap,
                             within_1e6=bool(max(abs(dT), abs(dO), dcar, dcar_o, abs(d_ov), abs(d_ova), abs(d_cap)) <= TOL_TWH)))
        ta = sum(v["T"] for v in a["countries"].values()) / 1e6; tb = sum(v["T"] for v in b["countries"].values()) / 1e6
        rows.append(dict(run=run, step=s, country="ASEAN11", T_v2_ref_TWh=tb, T_v2_repo_TWh=ta, diff_T_TWh=ta - tb, within_1e6=bool(abs(ta - tb) <= TOL_TWH * 11)))
    new = pd.DataFrame(rows)
    p = W / "CHECKPOINTS.csv"
    if p.exists():
        old = pd.read_csv(p)
        old = old[~((old.run == run) & old.step.isin(steps))]
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(p, index=False, float_format="%.9g", lineterminator="\n")
    cur = new[(new.run == run) & new.step.isin(steps)]
    print(cur[cur.country == "ASEAN11"][["step", "T_v2_ref_TWh", "T_v2_repo_TWh", "diff_T_TWh"]].to_string())
    z = cur[cur.country != "ASEAN11"]
    print("max |diff T| TWh", float(z.diff_T_TWh.abs().max()), "max |diff other|", float(z.diff_other_TWh.abs().max()),
          "max carrier", float(z[["max_carrier_diff_T_TWh", "max_carrier_diff_other_TWh"]].max().max()), "max |diff overflow|", float(z.diff_overflow_TWh.abs().max()),
          "max |diff cap|", float(z.diff_cap_TWh.abs().max()), "all within 1e-6:", bool(cur.within_1e6.all()))
    s7 = z[z.step == steps[-1]]
    print("S7 overflow (TWh) ref / s3_0 ref:", {r.country: (round(r.overflow_ref_TWh, 4), round(r.overflow_s30_ref_TWh, 4)) for r in s7.itertuples() if r.overflow_ref_TWh > 0})
    sys.exit(0 if cur.within_1e6.all() else 1)


if __name__ == "__main__":
    main()
