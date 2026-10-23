"""M10R B3.3 (RUN_PLAN.md 11.4): the post-processing drill of every network type - the record DRILL_POSTPROC.json written by
research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh (local 56x3h results; skipped when the drill has not run here) and the
synthetic-solution script on a toy-sized check of its receipt contract."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
DRILL = Path(os.environ.get("M10R_DRILL_JSON", ROOT / "results_project/m10r/drill/DRILL_POSTPROC.json"))
TYPES = ["integrated", "disconnected", "minusVN", "minusTH", "minusLA", "keepstock", "wacc_disconnected", "b1_disconnected", "wacc_integrated"]


def test_drill_script_covers_every_network_type_and_requires_the_batch_reference():
    src = (ROOT / "research/06_scope_redesign/p1_m10r_20261024/scripts/drill_postproc.sh").read_text()
    for t in TYPES:
        assert f" {t} " in src or f"minus$c" in src, t
    assert "s4d_ledger_redo.py" in src and "l23_violation_analysis.py" in src and "s4o_c1_precision.py" in src and "m12_allocation.py" in src and "m12_rhs_audit.py" in src and "gates_v6.py" in src
    assert "m10r_synthetic_solution.py" in src and "env -u GRB_LICENSE_FILE" in src and "DRILL_POSTPROC.json" in src
    mp = (ROOT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package/make_package.sh").read_text()
    assert "DRILL_JSON" in mp and "all_types_ran" in mp            # the package build requires the drill of its commit


@pytest.mark.skipif(not DRILL.exists(), reason="M10R drill not run locally (DRILL_POSTPROC.json missing)")
def test_drill_record_every_type_ran_through_and_the_identity_is_computable():
    d = json.loads(DRILL.read_text())
    assert d["expected_types"] == TYPES and set(d["types"]) >= set(TYPES) and d["all_types_ran"] and d["solver_runs"] == 0
    for t in TYPES:
        v = d["types"][t]
        assert v["all_steps_ran"], (t, v["steps"])
        assert v["b16"]["computable"] and v["b16"]["relative_error"] is not None, t
        assert v["source"] in ("real", "synthetic") and v["label"] in ("ACCEPTED_LAYER2", "ACCEPTED_LAYER1", "NOT_ACCEPTED")
        if v["source"] == "real":
            assert v["b16"]["relative_error"] <= 1e-6 and v["c1"]["a"] and v["m12_identity_passed"], t
        else:
            assert v["termination"] == "synthetic" and abs(v["b16"]["difference_eur"]) <= 0.01e9, t
    assert "keepstock" in d["real_types"] and d["types"]["keepstock"]["label"] == "ACCEPTED_LAYER2" and d["types"]["keepstock"]["c1"]["c"] is True
    assert d["types"]["keepstock"]["b16"]["fom_meta"]["absent_zero"] == 50
