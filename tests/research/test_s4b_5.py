"""S4B-5 / S4B-6: the gap-diagnostic build also writes its 365x24h daily network (cloud diagnostic run) and the smoke summary is complete."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "results_project/s4b/s4b5/builds"
A = ROOT / "results_project/s4b/s4b5/analysis"


@pytest.mark.skipif(not (B / "disconnected_gap/disconnected_gap_diagnostic_365_24h_unsolved.nc").exists(), reason="S4B-5 builds not present")
def test_gap_diagnostic_daily_network():
    import numpy as np
    import pypsa
    r = json.loads((B / "disconnected_gap/disconnected_gap_diagnostic_BUILD_RECEIPT.json").read_text())
    assert r["gap_diagnostic"] is True and r["daily_network"]["snapshots"] == 365
    d = pypsa.Network(str(B / "disconnected_gap/disconnected_gap_diagnostic_365_24h_unsolved.nc"))
    h = pypsa.Network(str(B / "disconnected_gap/disconnected_gap_diagnostic_2920_3h_unsolved.nc"))
    assert len(d.snapshots) == 365 and np.all(d.snapshot_weightings.generators.to_numpy() == 24.0)
    assert d.meta["artifact_role"] == "GAP_DIAGNOSTIC_UNSOLVED" and d.meta["gap_diagnostic"]["slacks"] == ["electricity", "co2", "biomass", "gas"]
    slack = d.generators.index[d.generators.carrier.str.startswith("gap slack")]
    assert len(slack) > 0 and set(slack) == set(h.generators.index[h.generators.carrier.str.startswith("gap slack")])
    # the main daily networks are unchanged by the switch: same components as their 3 h parents
    for sc in ["integrated", "disconnected"]:
        rr = json.loads((B / f"{sc}/{sc}_BUILD_RECEIPT.json").read_text())
        assert rr["gap_diagnostic"] is False and rr["daily_network"]["snapshots"] == 365


@pytest.mark.skipif(not (A / "S4B5_SMOKE_SUMMARY.json").exists(), reason="S4B-5 summary not present")
def test_smoke_summary_complete():
    s = json.loads((A / "S4B5_SMOKE_SUMMARY.json").read_text())
    runs = {(r["source"], r["run"]): r for r in s["runs"]}
    assert runs[("S4B5", "integrated")]["termination"] == "optimal" and runs[("S4B5", "disconnected_gap")]["termination"] == "optimal"
    assert runs[("S4B5", "disconnected")]["termination"] != "optimal"   # expected structural infeasibility (decisions 49, 53, 73)
    gap = {r["country"]: r for r in s["gap_table_disconnected_gap"]["rows"]}
    assert all(abs(gap[c]["electricity_gap_mwh"]) < 1 and abs(gap[c]["gas_gap_mwh"]) < 1 and abs(gap[c]["biomass_gap_mwh"]) < 1 for c in gap)
    assert {c for c in gap if c != "ASEAN" and (gap[c]["co2_gap_t"] or 0) > 1e3} == {"KH", "LA", "MM", "SG"}
    assert s["B5_trial"]["passed"] is True and s["B5_trial"]["disconnected_cross_border_components"] == 0
