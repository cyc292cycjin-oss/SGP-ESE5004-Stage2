"""M10R (third-batch close-out; post-hoc fix of the keep-stock ledger defect): recompute the country cost ledger exports of a SOLVED run from its
solved network - no solver call, the solve results are not changed. The same files and the same code path as the S4D-3 block of
scripts_project/s2_solve.py: COUNTRY_COST_LEDGER.csv, COUNTRY_COST_LEDGER_USD2020.csv, COUNTRY_COST_LEDGER_DETAIL.csv, NODAL_PRICES.csv,
LEDGER_IDENTITY.json and the B16_LEDGER entry of V5_GATES.json (the all_passed flags recomputed with s4b_acceptance.all_passed on the recorded
acceptance basis). Everything is written into --into (a new folder; --into equal to the run folder is refused); LEDGER_REDO.json records the
inputs (solved network SHA256, receipt objective), the B16 entry before and after and the SHA256 of this code.

    python scripts_project/s4d_ledger_redo.py --solve-dir <run dir> --into <new dir> [--solved <solved nc>] [--repo <code>]

The gap-diagnostic runs (research.gap_diagnostic enabled, extra objective terms) are not supported here (not part of the batches)."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
SCRIPT = "scripts_project/s4d_ledger_redo.py"
FILES = ("COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_USD2020.csv", "COUNTRY_COST_LEDGER_DETAIL.csv", "NODAL_PRICES.csv", "LEDGER_IDENTITY.json", "V5_GATES.json")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def jl(p: Path):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def find_solved(solve_dir: Path, solved: Path | None) -> Path | None:
    if solved is not None:
        return Path(solved)
    cands = sorted(solve_dir.glob("*_solved.nc"))
    if not cands:
        exp = solve_dir.parent / "export" / solve_dir.name
        cands = sorted(exp.glob("*_solved.nc")) if exp.is_dir() else []
    return cands[0] if cands else None


def redo(solve_dir: Path, into: Path, solved: Path | None = None) -> dict:
    from s4b_acceptance import all_passed
    from s4d_ledger import country_cost_ledger, ledger_detail_usd, ledger_gate, ledger_table, ledger_table_usd, load_length_shares, nodal_prices, report_currency
    import pypsa
    logging.disable(logging.WARNING)
    solve_dir, into = Path(solve_dir).resolve(), Path(into).resolve()
    if into == solve_dir:
        raise SystemExit("--into must be a new folder, not the run folder (the original run is read only)")
    nc = find_solved(solve_dir, solved)
    if nc is None or not nc.exists():
        raise SystemExit(f"no solved network (*_solved.nc) in {solve_dir} / its export folder; pass --solved")
    rec = jl(solve_dir / "SOLVE_RECEIPT.json") or {}
    gates_old = jl(solve_dir / "V5_GATES.json") or {}
    into.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    n = pypsa.Network(str(nc))
    if (n.meta.get("gap_diagnostic") or {}).get("enabled"):
        raise SystemExit("gap-diagnostic run (extra objective terms): not supported by the ledger redo")
    obj_net, obj_rec = float(n.objective), rec.get("objective")
    obj_equal = (obj_rec is not None) and abs(obj_net - float(obj_rec)) <= 1e-9 * max(1.0, abs(float(obj_rec)))
    if obj_rec is not None and not obj_equal:
        raise SystemExit(f"objective of the solved network ({obj_net!r}) differs from the receipt ({obj_rec!r}): wrong network for this run")
    cfg = dict(research=n.meta.get("research_config") or {})
    led_rows, led_id, led_diag = country_cost_ledger(n, load_length_shares())
    rep = report_currency(cfg)
    T = ledger_table(led_rows); T.to_csv(into / "COUNTRY_COST_LEDGER.csv", float_format="%.6f")
    ledger_table_usd(T, rep["fx_per_eur2020"]).to_csv(into / "COUNTRY_COST_LEDGER_USD2020.csv", float_format="%.6f")
    ledger_detail_usd(led_rows, rep["fx_per_eur2020"]).to_csv(into / "COUNTRY_COST_LEDGER_DETAIL.csv", index=False, float_format="%.6f")
    nodal_prices(n).to_csv(into / "NODAL_PRICES.csv", float_format="%.6g")
    (into / "LEDGER_IDENTITY.json").write_text(json.dumps(dict(identity=led_id, diagnostics=led_diag, report_currency=rep), indent=1, default=str))
    b16 = ledger_gate(led_id)
    gates = dict(gates_old); gates["B16_LEDGER"] = b16
    basis = str(gates.get("acceptance_basis", "barconvtol"))
    if "all_passed_barconvtol" in gates:
        gates["all_passed_barconvtol"] = all_passed(gates, "barconvtol")
    if "all_passed_solver_tolerances" in gates:
        gates["all_passed_solver_tolerances"] = all_passed(gates, "solver_tolerances")
    if "all_passed" in gates:
        gates["all_passed"] = (gates.get("all_passed_" + basis) if basis in ("barconvtol", "solver_tolerances")
                               else all(v["passed"] for k, v in gates.items() if isinstance(v, dict) and "passed" in v))
    (into / "V5_GATES.json").write_text(json.dumps(gates, indent=1, default=str))
    old = gates_old.get("B16_LEDGER") or {}
    res = dict(script=SCRIPT, solve_dir=str(solve_dir), into=str(into), solved_network=dict(path=str(nc), sha256=sha(nc)),
               objective=dict(network=obj_net, receipt=obj_rec, equal=bool(obj_equal)),
               b16_before=dict(passed=old.get("passed"), relative_error=old.get("relative_error"), error=(old.get("error") or None)),
               b16_after=dict(passed=b16["passed"], relative_error=b16["relative_error"], difference=b16["difference"]),
               identity=led_id, v5_gates_source=("V5_GATES.json of the run" if gates_old else "none (new file holds B16_LEDGER only)"),
               files={f: dict(bytes=(into / f).stat().st_size, sha256=sha(into / f)) for f in FILES},
               code=dict(s4d_ledger_sha256=sha(HERE / "s4d_ledger.py"), s4d_ledger_redo_sha256=sha(Path(__file__).resolve())),
               seconds=round(time.time() - t0, 1), written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), solver_runs=0)
    (into / "LEDGER_REDO.json").write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solve-dir", type=Path, required=True); ap.add_argument("--into", type=Path, required=True)
    ap.add_argument("--solved", type=Path, default=None); ap.add_argument("--repo", type=Path, default=HERE.parent)
    a = ap.parse_args()
    r = redo(a.solve_dir, a.into, a.solved)
    print(json.dumps(dict(b16_before=r["b16_before"], b16_after=r["b16_after"], objective_equal=r["objective"]["equal"], seconds=r["seconds"]), default=str))


if __name__ == "__main__":
    main()
