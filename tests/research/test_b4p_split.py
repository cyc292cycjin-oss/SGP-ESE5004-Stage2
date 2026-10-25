"""B4P (fourth-batch preparation, 2026-10-26; user supplement 2): the split-process solve - process 2 scripts_project/b4_split_solve.py and the
process 1 / 3 helpers of scripts_project/s2_solve.py (write_problem_file, assign_split_result, split_reduced_costs). No solver is called anywhere:
the Gurobi status map and status classes are checked against linopy's own tables, the label placement against a duck-typed solver model, the
result mapping against a small linopy model with synthetic arrays, the problem-file writer against linopy's writer on the same model."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
import b4_split_solve as P2   # noqa: E402
import s2_solve as S2   # noqa: E402


def test_condition_map_equals_linopy():
    """The Gurobi status code -> termination condition table is the one of linopy 0.5.5 solvers.Gurobi._solve (read from its source)."""
    import inspect
    import linopy.solvers as ls
    src = inspect.getsource(ls.Gurobi._solve)
    start = src.index("CONDITION_MAP = {"); end = src.index("}", start)
    table = eval(src[start + len("CONDITION_MAP = "):end + 1])
    assert table == P2.CONDITION_MAP


def test_status_classes_equal_linopy():
    from linopy.constants import Status, TerminationCondition
    for code, cond in P2.CONDITION_MAP.items():
        assert P2.linopy_status(cond) == Status.from_termination_condition(cond).status.value, (code, cond)
    for tc in TerminationCondition:
        assert P2.linopy_status(tc.value) == Status.from_termination_condition(tc.value).status.value
    assert P2.linopy_status("no_such_condition") == "unknown"


class _FakeModel:
    """Duck-typed gurobipy model: objects with names <prefix><label>, attribute values by name."""

    def __init__(self, names, values):
        self.names = list(names); self.values = dict(zip(names, values))

    def getAttr(self, attr, objs):
        if attr in ("VarName", "ConstrName"):
            return [o for o in objs]
        return [self.values[o][attr] for o in objs]


def test_values_by_label_places_by_label_and_marks_absent(monkeypatch):
    monkeypatch.setattr(P2, "CHUNK", 2)   # several chunks
    names = ["x5", "x0", "x12", "x3"]
    m = _FakeModel(names, [dict(X=5.5, RC=-5.0), dict(X=0.5, RC=0.0), dict(X=12.5, RC=1e-9), dict(X=3.5, RC=3.0)])
    labels = np.array([0, 3, 5, 7, 12], dtype=np.int64)   # 7 absent from the solver model
    X, absent = P2.values_by_label(names, m, "X", "x", labels, top=20)
    assert absent == 1 and np.isnan(X[3])
    assert X[0] == 0.5 and X[1] == 3.5 and X[2] == 5.5 and X[4] == 12.5
    RC, _ = P2.values_by_label(names, m, "RC", "x", labels, top=20)
    assert RC[0] == 0.0 and RC[4] == 1e-9 and np.isnan(RC[3])
    with pytest.raises(ValueError):
        P2.values_by_label(["c1", "c2"], _FakeModel(["c1", "c2"], [dict(X=1.0), dict(X=2.0)]), "X", "x", labels, top=20)


def _small_model():
    import linopy
    import pandas as pd
    m = linopy.Model()
    t = pd.RangeIndex(3, name="snapshot"); g = pd.Index(["a", "b"], name="gen")
    p = m.add_variables(lower=0, upper=10, coords=[t, g], name="Generator-p")
    cap = m.add_variables(lower=0, upper=100, coords=[g], name="Generator-p_nom")
    m.add_constraints(p.sum("gen") >= 4, name="Bus-nodal_balance")
    m.add_constraints(p - cap <= 0, name="Generator-ext-p-upper")
    m.add_objective((p * 1.0).sum() + (cap * 10.0).sum())
    return m


def test_assign_split_result_maps_arrays_onto_labels(tmp_path):
    """Synthetic solver arrays (value = label + 0.25 for X, -label for Pi) land on the right variable / constraint coordinates; absent labels NaN."""
    m = _small_model(); out = tmp_path / "run"; (out / "lp").mkdir(parents=True); sp = out / "split"; sp.mkdir()
    M = m.matrices; vl = np.asarray(M.vlabels, dtype=np.int64); cl = np.asarray(M.clabels, dtype=np.int64)
    np.save(out / "lp" / "vlabels.npy", vl); np.save(out / "lp" / "clabels.npy", cl)
    X = vl.astype(float) + 0.25; X[-1] = np.nan   # the last label "absent from the solver model"
    Pi = -cl.astype(float); RC = vl.astype(float) * 2
    np.save(sp / "X_raw.npy", X); np.save(sp / "Pi_raw.npy", Pi); np.save(sp / "RC_raw.npy", RC)
    split = dict(linopy_status="ok", termination_condition="optimal", objective=123.5)
    status, cond = S2.assign_split_result(m, split, sp)
    assert (status, cond) == ("ok", "optimal") and m.status == "ok" and m.termination_condition == "optimal" and m.objective.value == 123.5 and m.solver_model is None
    for name, var in m.variables.items():
        lab = np.asarray(var.labels.values); sol = np.asarray(var.solution.values)
        want = lab.astype(float) + 0.25; want[lab == vl[-1]] = np.nan
        assert np.array_equal(sol, want, equal_nan=True), name
    for name, con in m.constraints.items():
        lab = np.asarray(con.labels.values); assert np.array_equal(np.asarray(con.dual.values), -lab.astype(float)), name
    rc = S2.split_reduced_costs(sp)
    assert rc == {int(l): float(2 * l) for l in vl}
    # a result without a solution: status carried, nothing assigned
    m2 = _small_model()
    assert S2.assign_split_result(m2, dict(linopy_status="warning", termination_condition="time_limit", objective=None), sp) == ("warning", "time_limit")
    assert m2.status == "warning" and np.isnan(m2.objective.value)


def test_write_problem_file_is_linopy_lp_writer(tmp_path):
    """The process-1 file equals linopy's own LP writer output after the same sanitising; names are x<label> / c<label>; every variable has a bound line."""
    m = _small_model(); fn = S2.write_problem_file(m, tmp_path / "split" / "problem.lp")
    text = fn.read_text()
    assert text.strip().endswith("end") and "\\* " not in text
    m2 = _small_model(); m2.constraints.sanitize_zeros(); m2.constraints.sanitize_infinities(); ref = tmp_path / "ref.lp"
    m2.to_file(ref, io_api="lp", integer_label="general", slice_size=2_000_000, explicit_coordinate_names=False)
    assert ref.read_bytes() == fn.read_bytes()
    vl = np.asarray(m.matrices.vlabels)
    for lab in vl:
        assert f"x{int(lab)}" in text
    assert text.count("<=") >= len(vl)   # bounds section: one "lb <= x <= ub" line per variable


def test_parse_kv_and_names():
    assert P2.parse_kv(["SoftMemLimit=6", "BarIterLimit=0", "X=1.5"]) == {"SoftMemLimit": 6, "BarIterLimit": 0, "X": 1.5}
    assert P2.GUROBI_STATUS_NAME[17] == "MEM_LIMIT" and P2.CONDITION_MAP[17] == "internal_solver_error"


def test_post_solve_writes_status_first_and_records_step_failures():
    """A3.1 (static): in s2_solve.post_solve the receipt with the termination status is saved before any post-solve step; the solution arrays are
    saved before the duals / gates / ledger; every later step is guarded (post_solve_errors) and the exit code is 4 with errors, never a raise."""
    src = (ROOT / "scripts_project/s2_solve.py").read_text(); body = src[src.index("def post_solve("):src.index('if __name__ == "__main__":')]
    i_status = body.index("run.update(status=status, termination_condition=condition"); i_save = body.index('save(out / "SOLVE_RECEIPT.json", run)   # A3.1: on disk before any post-solve step')
    i_arrays = body.index('guard("solution_arrays", _arrays)'); i_duals = body.index("from s4m_duals import write_duals"); i_ledger = body.index("from s4d_ledger import")
    assert i_status < i_save < i_arrays < i_duals < i_ledger
    assert "return 0 if not errors else 4" in body and 'run["post_solve_errors"] = errors' in body and "post_solve_complete" in body
    main_body = src[src.index("def main("):src.index("def post_solve(")]
    assert "post-solve failures never reach here" in main_body


NET56 = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/builds_s01/integrated/integrated_2920_3h_unsolved.nc")


@pytest.mark.skipif(not NET56.exists(), reason="M08b supplement-01 integrated 2920x3h build not present")
def test_post_solve_exception_keeps_termination_status_and_solution_real_network(tmp_path, monkeypatch):
    """A3.1 stand-in drill on the real network (56 snapshots, split assign stage with SYNTHETIC zero arrays, no solver): a post-solve step that
    raises (co2_flows injected) leaves the termination status, the objective and solution/X.npy in place, records post_solve_errors, exits 4;
    b4_batch4.stop_class then does not classify the run as nosol (the label itself is not the point: a zero solution fails C1 / gates)."""
    import subprocess
    out = tmp_path / "F1"; monkeypatch.setenv("PYTHONHASHSEED", "0")
    args = [sys.executable, str(ROOT / "scripts_project/s2_solve.py"), "--repo", str(ROOT), "--network", str(NET56), "--scenario", "integrated", "--output", str(out), "--label", "SMOKE_TEST_ONLY",
            "--authorization", "B4P A3.1 stand-in test (no solver call)", "--solver", "gurobi", "--solver-profile", "formal_barrier_1e6_t16", "--scaling", "on", "--time-limit", "100", "--truncate", "56"]
    env = {k: v for k, v in os.environ.items() if k != "GRB_LICENSE_FILE"}; env["PYTHONHASHSEED"] = "0"
    p = subprocess.run(args + ["--split-stage", "build"], env=env, capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stderr[-2000:]
    rec = json.loads((out / "SOLVE_RECEIPT.json").read_text()); sp = out / "split"
    assert rec["split"]["stage"] == "build" and rec["optimize_calls"] == 0 and (sp / "problem.lp").exists() and "termination_condition" not in rec
    vl = np.load(out / "lp" / "vlabels.npy"); cl = np.load(out / "lp" / "clabels.npy")
    np.save(sp / "X_raw.npy", np.zeros(len(vl))); np.save(sp / "Pi_raw.npy", np.zeros(len(cl))); np.save(sp / "RC_raw.npy", np.zeros(len(vl)))
    (sp / "SPLIT_SOLVE.json").write_text(json.dumps(dict(solver_parameters=rec["solver_parameters"], gurobi_status_code=2, gurobi_status_name="OPTIMAL", termination_condition="optimal", linopy_status="ok",
                                                         objective=0.0, bar_iter_count=0, runtime_s=1.0, work_units=1.0, max_mem_used_gb=0.1, mem_used_gb=0.1, fingerprint="0x0", sol_count=1,
                                                         solve_seconds=1.0, peak_rss_bytes=1, solution_available=True, protect_parameters={}, problem_sha256_build=rec["split"]["problem_sha256"])))
    # the assign stage through a driver that imports s2_solve, injects the failure into co2_flows and calls main() with the same arguments
    driver = tmp_path / "assign_with_failure.py"
    driver.write_text("import argparse, sys\nsys.path.insert(0, %r)\nimport s2_solve\n\ndef _boom(n):\n    raise RuntimeError('injected post-solve failure (B4P A3.1 drill)')\n\ns2_solve.co2_flows = _boom\n"
                      "a = argparse.Namespace(repo=%r, network=%r, scenario='integrated', output=%r, solver_profile='formal_barrier_1e6_t16', scaling='on', kvl_norm=None, costs_table=None, solver='gurobi',\n"
                      "                       truncate=56, label='SMOKE_TEST_ONLY', authorization='B4P A3.1 stand-in test (no solver call)', time_limit=100.0, highs_ipm=False, stop_before_solve=False, split_stage='assign')\n"
                      "from pathlib import Path\na.repo = Path(a.repo); a.network = Path(a.network); a.output = Path(a.output)\nsys.exit(s2_solve.main(a))\n" % (str(ROOT / "scripts_project"), str(ROOT), str(NET56), str(out)))
    p = subprocess.run([sys.executable, str(driver)], env=env, capture_output=True, text=True, timeout=1800)
    assert p.returncode == 4, (p.stdout[-500:], p.stderr[-2000:])
    rec = json.loads((out / "SOLVE_RECEIPT.json").read_text())
    assert rec["termination_condition"] == "optimal" and rec["status"] == "ok" and rec["objective"] is not None and rec["optimize_calls"] == 1
    assert [e["step"] for e in rec["post_solve_errors"]] == ["co2_flows"] and rec["post_solve_complete"] is False and "failure" not in rec
    assert (out / "solution" / "X.npy").exists() and rec["solution"]["X"]["count"] == len(vl) and (out / "V5_GATES.json").exists() and (out / "EXPORTS.json").exists()
    assert not (out / "CO2_FLOWS.json").exists() and (out / "EMISSIONS_BY_COUNTRY.json").exists()   # the failed step's output is missing, the next steps ran
    import b4_batch4 as B
    (out / "RUN.json").write_text(json.dumps(dict(rid="F1", network_sha256=rec["input_network"]["sha256"], registered_sha256=rec["input_network"]["sha256"])))
    (out / "V6_ACCEPTANCE.json").write_text(json.dumps(dict(label="NOT_ACCEPTED", G1=dict(a=False), G2=dict(G2_1=dict(passed=True, sha256_equal=True), G2_2=dict(passed=True), G2_3=dict(passed=True)))))
    cls = B.stop_class(out)
    assert cls["solution_returned"] is True and cls["cls"] != "nosol" and cls["post_solve_errors"] == ["co2_flows"]
