"""S4M-2 smoke summary (S4M instruction S4M-2): the three S4M smoke runs (main settings: dust_cleanup on + biomass_overflow_cap_share 0.98; 56x3h, profile A)
against the S4K-3 smoke (via the bit-identical S4K-network reference runs of the S4L-2 matrix) and the S4L-5 98 % diagnostic, under the S4L-2 standard
(objective, B16, per-country disconnected - integrated differences), plus the NZE run against the S4K-3 NZE smoke and the solid-biomass shadow prices.
Reuses s4l_2_summary.py through a reference folder that links the S4K-network runs.

    python scripts_project/s4m_2_summary.py --smoke results_project/s4m/s4m2 --s4k3 results_project/s4k/s4k3 --s4l2 results_project/s4l/s4l2 --s4l5 results_project/s4l/s4l5
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from s4l_2_summary import parse_log, run_row  # noqa: E402


def jl(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    for k in ("smoke", "s4k3", "s4l2", "s4l5"):
        ap.add_argument("--" + k, type=Path, required=True)
    a = ap.parse_args()
    ref = a.smoke / "ref"; (ref / "solves").mkdir(parents=True, exist_ok=True)
    for t in ("s4k_A_integrated", "s4k_A_disconnected"):
        lnk = ref / "solves" / t
        if not lnk.exists():
            lnk.symlink_to((a.s4l2 / "solves" / t).resolve())
    cmd = [sys.executable, str(HERE / "s4l_2_summary.py"), "--run", str(ref), "--s4k3", str(a.s4k3), "--extra", f"s4m={a.smoke / 'solves'}", "--extra", f"bio98={a.s4l5 / 'solves'}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    (a.smoke / "s4l_2_summary_stdout.txt").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr)
    mx = jl(ref / "analysis" / "S4L2_MATRIX_SUMMARY.json")
    out = a.smoke / "analysis"; out.mkdir(exist_ok=True)
    for f in (ref / "analysis").glob("*"):
        (out / f.name).write_bytes(f.read_bytes())
    nze = run_row(a.smoke / "solves" / "s4m_A_integrated_nze", "s4m_A_integrated_nze")
    nze_ref = run_row(a.s4k3 / "solves" / "integrated_nze", "s4k3_integrated_nze")
    i_m = (mx.get("runs") or {}).get("s4m_A_integrated", {}); i_k = (mx.get("runs") or {}).get("s4k_A_integrated", {})
    res = dict(standard=mx.get("standard"), runs={k: v for k, v in (mx.get("runs") or {}).items() if k.startswith(("s4k_A", "s4m_", "bio98_"))},
               nze=dict(s4m=nze, s4k3=nze_ref, objective_rel_diff=((nze["objective"] / nze_ref["objective"] - 1) if (nze.get("objective") and nze_ref.get("objective")) else None),
                        nze_minus_integrated_bn_eur=dict(s4m=((nze["objective"] - i_m["objective"]) / 1e9 if (nze.get("objective") and i_m.get("objective")) else None),
                                                         s4k3=((nze_ref["objective"] - i_k["objective"]) / 1e9 if (nze_ref.get("objective") and i_k.get("objective")) else None))),
               combinations={k: v for k, v in (mx.get("combinations") or {}).items() if k in ("s4k_A", "s4m_A", "bio98_A")},
               lp_size={sc: {q: dict(s4k=i_k.get(q) if sc == "integrated" else (mx.get("runs") or {}).get("s4k_A_disconnected", {}).get(q),
                                     s4m=(mx.get("runs") or {}).get(f"s4m_A_{sc}", {}).get(q)) for q in ("num_col", "num_row", "nnz")} for sc in ("integrated", "disconnected")},
               price_differences={k: v for k, v in (mx.get("price_differences") or {}).items() if k.startswith(("s4m_", "bio98_"))},
               solid_biomass_shadow_prices={t: {k.split("|")[1]: v for k, v in (mx.get("prices_by_country") or {}).get(t, {}).items() if k.startswith("solid biomass|")}
                                            for t in ("s4k_A_integrated", "s4m_A_integrated", "bio98_A_integrated", "s4k_A_disconnected", "s4m_A_disconnected", "bio98_A_disconnected")},
               repeat_vs_s4k3=mx.get("repeat_vs_s4k3"), status=[x for x in (a.smoke / "STATUS.txt").read_text().splitlines() if "PROJ" not in x] if (a.smoke / "STATUS.txt").exists() else [])
    (out / "S4M2_SMOKE_SUMMARY.json").write_text(json.dumps(res, indent=1, default=str))
    show = {k: {kk: v.get(kk) for kk in ("termination", "objective", "barrier_iterations", "solve_seconds", "all_passed_solver_tolerances", "failed_gates_solver_tolerance_set", "B16_relative_error", "num_row", "peak_rss_gib")} for k, v in res["runs"].items()}
    print(json.dumps(show, indent=1, default=str))
    print("NZE:", json.dumps({k: v for k, v in res["nze"].items() if k != "s4m" and k != "s4k3"}, default=str), "| s4m nze:", nze.get("termination"), nze.get("objective"), nze.get("all_passed_solver_tolerances"), "| s4k3 nze:", nze_ref.get("objective"))
    print(json.dumps({c: dict(obj=v["objective_rel_diff_vs_ref"], b16=v["b16_relative_error"], exceeding=v["countries_exceeding"], all_within=v["all_within"], B6=v["B6_bn_eur"]) for c, v in res["combinations"].items()}, indent=1, default=str))
    print(json.dumps(res["solid_biomass_shadow_prices"], indent=1, default=str))


if __name__ == "__main__":
    main()
