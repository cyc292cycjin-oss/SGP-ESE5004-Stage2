"""S4N-1 acceptance check (READ ONLY, no solver call): in-run dual export of the packaged code f50c8850 on the 56x3h integrated STEPS smoke.

Criteria (S4N instruction v1, S4N-1 point 2):
  1. termination optimal, gates passed (all_passed_solver_tolerances; the BarConvTol-basis gates are reported as the known S4K-3 state);
  2. objective vs the S4M-2 integrated smoke (648,381,181,410.4515 EUR): relative difference <= 1e-9;
  3. receipt 'duals' without export_error (source = model, i.e. written in the run);
  4. DUALS_BY_CONSTRAINT.nc, the cost breakdown and EXPORTS.json written in the run (EXPORTS.json bytes / SHA256 recomputed);
  5. Bus-nodal_balance and Bus-meshed-nodal_balance duals / snapshot_weightings.objective vs buses_t.marginal_price: max relative difference <= 1e-12;
  6. if DUALS_BY_CONSTRAINT.nc has the same structure as the S4M offline reconstruction (S4M-S2 re-run folder), every constraint is compared
     value by value: relative difference <= 1e-9.

    PYTHONHASHSEED=0 python s4n1_check.py --solve <solve dir> --out <json> [--s4m2 <S4M-2 solve dir>] [--offline <S4M-S2 re-run solve dir>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

S4M2_DEFAULT = "results_project/s4m/s4m2/solves/s4m_A_integrated"
OFFLINE_DEFAULT = "results_project/s4m/s4ms2/solves/s4m_A_integrated_rerun"
OBJ_TOL = 1e-9; BUS_TOL = 1e-12; DUAL_TOL = 1e-9
EXPORT_FILES = ["SOLVE_RECEIPT.json", "V5_GATES.json", "INTERIOR_CHECKS.json", "BUNKER_ACCOUNT.json", "GUROBI_LOG_SCRUBBED.txt", "RESOURCE.jsonl", "CO2_FLOWS.json",
                "GAP_TABLE.json", "EMISSIONS_BY_COUNTRY.json", "CAPACITY_BY_TECH_COUNTRY.json", "cross_border_flows.csv", "COUNTRY_COST_LEDGER.csv",
                "COUNTRY_COST_LEDGER_DETAIL.csv", "LEDGER_IDENTITY.json", "NODAL_PRICES.csv", "DUALS_BY_CONSTRAINT.nc", "DUALS_INDEX.csv",
                "COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "costs_active_research.csv", "EXPORTS.json"]
LICENCE_RE = re.compile(rb"license[i]d|registered\s+to|wls(secret|accessid)", re.I)   # the run_365x24h.sh pack check


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(a: np.ndarray, b: np.ndarray) -> dict:
    """a vs reference b (same shape). Two definitions: scaled |a-b| / max(1, |b|) (S4M convention) and pure |a-b| / |b| over |b| > 0."""
    a = np.asarray(a, dtype=float).ravel(); b = np.asarray(b, dtype=float).ravel()
    na, nb = np.isnan(a), np.isnan(b); both = ~na & ~nb
    d = np.abs(a[both] - b[both]); bb = np.abs(b[both])
    nz = bb > 0
    return dict(n=int(a.size), nan_mask_equal=bool((na == nb).all()), nan=int(nb.sum()), compared=int(both.sum()),
                max_abs=float(d.max()) if d.size else 0.0,
                max_rel_scaled=float((d / np.maximum(1.0, bb)).max()) if d.size else 0.0,
                max_rel_pure=float((d[nz] / bb[nz]).max()) if nz.any() else 0.0,
                ref_zero_but_value_nonzero=int(((bb == 0) & (d > 0)).sum()), identical=bool(d.size == 0 or float(d.max()) == 0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solve", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--s4m2", type=Path, default=Path(S4M2_DEFAULT)); ap.add_argument("--offline", type=Path, default=Path(OFFLINE_DEFAULT))
    a = ap.parse_args(); d = a.solve
    res: dict = dict(solve_dir=str(d), criteria={})
    C = res["criteria"]

    # 1 / 2 / 3 receipt and gates
    rec = json.loads((d / "SOLVE_RECEIPT.json").read_text())
    ref = json.loads((a.s4m2 / "SOLVE_RECEIPT.json").read_text())
    off_rec = json.loads((a.offline / "SOLVE_RECEIPT.json").read_text())
    g = json.loads((d / "V5_GATES.json").read_text())
    gates = {k: bool(v.get("passed")) for k, v in g.items() if isinstance(v, dict) and "passed" in v}
    res["receipt"] = dict(termination_condition=rec.get("termination_condition"), status=rec.get("status"), finished=("finished_epoch" in rec),
                          objective=rec.get("objective"), objective_lp=rec.get("objective_lp"), solve_seconds=rec.get("solve_seconds"),
                          gurobi_log_stats=rec.get("gurobi_log_stats"), peak_rss_bytes=rec.get("peak_rss_bytes"), lp=rec.get("lp"), solver_profile=rec.get("solver_profile"),
                          solver_parameters=rec.get("solver_parameters"), retry=rec.get("retry"), optimize_calls=rec.get("optimize_calls"),
                          duals={k: v for k, v in (rec.get("duals") or {}).items() if k != "note"},
                          cost_breakdown={k: v for k, v in (rec.get("cost_breakdown") or {}).items() if k in ("extendable", "matched", "matched_share", "by_rule", "max_abs_rel_dev", "residual_eur_max")})
    res["gates"] = dict(all_passed=g.get("all_passed"), all_passed_solver_tolerances=g.get("all_passed_solver_tolerances"), all_passed_barconvtol=g.get("all_passed_barconvtol"),
                        failed=sorted(k for k, v in gates.items() if not v), passed=sorted(k for k, v in gates.items() if v), acceptance_basis=g.get("acceptance_basis"))
    ref_g = json.loads((a.s4m2 / "V5_GATES.json").read_text())
    res["gates"]["failed_in_s4m2_reference"] = sorted(k for k, v in ref_g.items() if isinstance(v, dict) and "passed" in v and not v.get("passed"))
    C["1_optimal_and_gates"] = bool(rec.get("termination_condition") == "optimal" and g.get("all_passed_solver_tolerances") is True)
    obj, obj_ref = float(rec["objective"]), float(ref["objective"])
    res["objective_compare"] = dict(this=obj, s4m2=obj_ref, rel_diff_vs_s4m2=obj / obj_ref - 1, s4ms2_rerun=float(off_rec["objective"]), rel_diff_vs_rerun=obj / float(off_rec["objective"]) - 1,
                                    lp_this=[(rec.get("lp") or {}).get(k) for k in ("num_row", "num_col", "nnz")], lp_s4m2=[(ref.get("lp") or {}).get(k) for k in ("num_row", "num_col", "nnz")])
    C["2_objective_rel_diff_le_1e-9"] = bool(abs(obj / obj_ref - 1) <= OBJ_TOL)
    du = rec.get("duals") or {}
    C["3_no_export_error"] = bool("export_error" not in du and du.get("source") == "model" and not du.get("unassigned"))

    # 4 files written in the run + EXPORTS.json consistency
    ex = json.loads((d / "EXPORTS.json").read_text()) if (d / "EXPORTS.json").exists() else {}
    files = {}
    for f in ("DUALS_BY_CONSTRAINT.nc", "DUALS_INDEX.csv", "COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "costs_active_research.csv", "EXPORTS.json"):
        p = d / f
        files[f] = dict(exists=p.exists(), bytes=(p.stat().st_size if p.exists() else None), sha256=(sha(p) if p.exists() else None))
        if f in ex:
            files[f]["exports_json_match"] = bool(p.exists() and ex[f].get("bytes") == files[f]["bytes"] and ex[f].get("sha256") == files[f]["sha256"])
    res["files"] = files; res["exports_json"] = ex
    C["4_files_written_in_run"] = bool(all(v["exists"] for v in files.values()) and all(v.get("exports_json_match", True) for v in files.values())
                                     and set(ex) >= {"DUALS_BY_CONSTRAINT.nc", "DUALS_INDEX.csv", "COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "costs_active_research.csv"})
    # cost breakdown against the S4M-S2 files (offline re-generated at f50c8850)
    cb = {}
    for f in ("COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json", "costs_active_research.csv"):
        po = a.offline / f
        cb[f] = dict(sha_this=files[f]["sha256"], sha_s4ms2=(sha(po) if po.exists() else None), identical=bool(po.exists() and sha(po) == files[f]["sha256"]))
    T1 = pd.read_csv(d / "COMPONENT_COST_BREAKDOWN.csv"); T0 = pd.read_csv(a.offline / "COMPONENT_COST_BREAKDOWN.csv")
    cb["rows_this_vs_s4ms2"] = [int(len(T1)), int(len(T0))]
    if T1.shape == T0.shape and list(T1.columns) == list(T0.columns):
        num = [c for c in T1.columns if pd.api.types.is_numeric_dtype(T1[c]) and pd.api.types.is_numeric_dtype(T0[c])]
        cb["numeric_columns_max_rel_scaled"] = max((rel(T1[c].to_numpy(), T0[c].to_numpy())["max_rel_scaled"] for c in num), default=0.0)
        cb["text_columns_equal"] = bool(all((T1[c].fillna("").astype(str) == T0[c].fillna("").astype(str)).all() for c in T1.columns if c not in num))
    res["cost_breakdown_vs_s4ms2"] = cb

    # 5 bus balance duals vs marginal_price
    import pypsa
    solved = next(iter(d.glob("*_solved.nc")))
    ns = pypsa.Network(str(solved)); mp = ns.buses_t.marginal_price; w = ns.snapshot_weightings.objective
    D1 = xr.open_dataset(d / "DUALS_BY_CONSTRAINT.nc")
    bus = {}
    for name in ("Bus-nodal_balance", "Bus-meshed-nodal_balance"):
        if name not in D1:
            bus[name] = dict(present=False); continue
        da = D1[name]; sd = [x for x in da.dims if x.endswith("|snapshot")][0]; bd = [x for x in da.dims if not x.endswith("|snapshot")][0]
        df = da.transpose(sd, bd).to_pandas(); common = [b for b in df.columns if b in mp.columns]
        scaled = df[common].div(w.to_numpy(), axis=0)
        r = rel(scaled.to_numpy(), mp[common].to_numpy())
        bus[name] = dict(present=True, buses=int(df.shape[1]), buses_compared=len(common), snapshots=int(df.shape[0]), weight=float(w.iloc[0]), **r)
    res["bus_dual_cross_check"] = bus
    C["5_bus_duals_vs_marginal_price_le_1e-12"] = bool(all(v.get("present") and v["buses_compared"] == v["buses"] and v["nan_mask_equal"] and v["max_rel_scaled"] <= BUS_TOL and v["max_rel_pure"] <= BUS_TOL for v in bus.values()))

    # 6 structure + value comparison with the S4M offline reconstruction
    D0 = xr.open_dataset(a.offline / "DUALS_BY_CONSTRAINT.nc")
    v1, v0 = set(D1.data_vars), set(D0.data_vars)
    struct = dict(constraints_this=len(v1), constraints_offline=len(v0), only_this=sorted(v1 - v0)[:20], only_offline=sorted(v0 - v1)[:20])
    dims_diff, coord_diff = [], []
    for k in sorted(v1 & v0):
        if D1[k].dims != D0[k].dims or D1[k].shape != D0[k].shape:
            dims_diff.append(k); continue
        for dim in D1[k].dims:
            c1 = D1[k].coords[dim].values if dim in D1[k].coords else np.arange(D1[k].sizes[dim])
            c0 = D0[k].coords[dim].values if dim in D0[k].coords else np.arange(D0[k].sizes[dim])
            if not np.array_equal(np.asarray(c1).astype(str), np.asarray(c0).astype(str)):
                coord_diff.append(f"{k}:{dim}"); break
    struct.update(dims_or_shape_differ=dims_diff[:20], n_dims_or_shape_differ=len(dims_diff), coords_differ=coord_diff[:20], n_coords_differ=len(coord_diff))
    same = bool(v1 == v0 and not dims_diff and not coord_diff)
    struct["same_structure"] = same
    per = {}
    if same:
        for k in sorted(v1):
            per[k] = rel(D1[k].values, D0[k].values)
        worst_scaled = sorted(per.items(), key=lambda kv: -kv[1]["max_rel_scaled"])[:5]
        worst_pure = sorted(per.items(), key=lambda kv: -kv[1]["max_rel_pure"])[:5]
        struct.update(values=int(sum(v["n"] for v in per.values())), nan=int(sum(v["nan"] for v in per.values())), nan_masks_equal=bool(all(v["nan_mask_equal"] for v in per.values())),
                      identical_constraints=int(sum(v["identical"] for v in per.values())),
                      max_rel_scaled=max(v["max_rel_scaled"] for v in per.values()), max_rel_pure=max(v["max_rel_pure"] for v in per.values()),
                      max_abs=max(v["max_abs"] for v in per.values()), ref_zero_but_value_nonzero=int(sum(v["ref_zero_but_value_nonzero"] for v in per.values())),
                      worst_scaled=[(k, v["max_rel_scaled"], v["max_abs"]) for k, v in worst_scaled], worst_pure=[(k, v["max_rel_pure"], v["max_abs"]) for k, v in worst_pure])
        C["6_offline_file_values_le_1e-9"] = bool(struct["nan_masks_equal"] and struct["max_rel_scaled"] <= DUAL_TOL and struct["max_rel_pure"] <= DUAL_TOL)
    else:
        C["6_offline_file_values_le_1e-9"] = "not_applicable_structure_differs"
    I1 = pd.read_csv(d / "DUALS_INDEX.csv"); I0 = pd.read_csv(a.offline / "DUALS_INDEX.csv")
    struct["index_equal_on_constraint_dims_size_nan"] = bool(I1.shape[0] == I0.shape[0] and (I1[["constraint", "size", "nan"]].reset_index(drop=True) == I0[["constraint", "size", "nan"]].reset_index(drop=True)).all().all())
    struct["index_dims_column_equal"] = bool(I1.shape[0] == I0.shape[0] and (I1["dims"].astype(str).str.replace("|", "", regex=False).reset_index(drop=True) == I0["dims"].astype(str).str.replace("|", "", regex=False).reset_index(drop=True)).all())
    res["offline_comparison"] = struct
    res["offline_per_constraint"] = per

    # licence scan of the files the cloud script would export
    hits = [f for f in EXPORT_FILES if (d / f).exists() and LICENCE_RE.search((d / f).read_bytes())]
    res["licence_scan_export_files"] = dict(files_scanned=int(sum((d / f).exists() for f in EXPORT_FILES)), hits=hits)
    res["accepted"] = bool(all(v is True for k, v in C.items() if v != "not_applicable_structure_differs"))
    a.out.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(dict(criteria=C, accepted=res["accepted"], objective=res["objective_compare"], gates=dict((k, res["gates"][k]) for k in ("all_passed_solver_tolerances", "failed")),
                          duals=res["receipt"]["duals"], bus=dict((k, dict((kk, v.get(kk)) for kk in ("buses_compared", "max_rel_scaled", "max_rel_pure"))) for k, v in bus.items()),
                          offline=dict((k, struct.get(k)) for k in ("same_structure", "constraints_this", "constraints_offline", "max_rel_scaled", "max_rel_pure", "max_abs", "identical_constraints", "nan_masks_equal")),
                          files=dict((k, (v["bytes"], v.get("exports_json_match"))) for k, v in files.items()), cost_breakdown=dict((k, v.get("identical")) for k, v in cb.items() if isinstance(v, dict)),
                          licence_hits=hits), indent=1, default=str))


if __name__ == "__main__":
    main()
