"""S3B R4 (decision 69): solver profiles, LP scaling round trip and the equivalence evidence (solver-free checks on stored receipts)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
R4 = ROOT / "results_project" / "s3b" / "r4"


def test_config_profiles():
    from phase4_static import config
    S = config(ROOT, "integrated")["research"]["solver"]
    fb, cd = S["profiles"]["formal_barrier"], S["profiles"]["crossover_diagnostic"]
    assert fb["Method"] == 2 and fb["Crossover"] == 0 and fb["BarConvTol"] == 1e-8 and fb["BarHomogeneous"] == 1 and fb["Threads"] == 8 and fb["Seed"] == 123
    assert {k: v for k, v in cd.items() if k != "Crossover"} == {k: v for k, v in fb.items() if k != "Crossover"} and cd["Crossover"] == 1
    assert S["scaling"]["store_energy_factor"] == 1000.0 and set(S["scaling"]["store_groups"]) == {"biomass_pools", "sequestration", "capture_buffers"}


def test_scaling_round_trip_small_model():
    """Column/row scaling of a tiny linopy model gives the same optimum and the unscaled solution/duals (HiGHS, no licence needed)."""
    import pypsa
    import pandas as pd
    from s3b_scaling import scale_store_energy, unscale_solution
    def build():
        n = pypsa.Network(); n.set_snapshots(pd.RangeIndex(3)); n.add("Bus", "b"); n.add("Bus", "s")
        n.add("Generator", "g", bus="b", p_nom=10, marginal_cost=[1.0, 5.0, 1.0])
        n.add("Load", "l", bus="b", p_set=[4.0, 6.0, 4.0])
        n.add("Link", "ch", bus0="b", bus1="s", p_nom=10, efficiency=1.0, p_min_pu=-1)
        n.add("Store", "st", bus="s", e_nom_extendable=True, e_cyclic=True, capital_cost=0.5)
        n.snapshot_weightings.loc[:, :] = 2.0
        return n
    a = build(); a.optimize(solver_name="highs")
    b = build(); m = b.optimize.create_model(); led = scale_store_energy(m, ["st"], 1000.0)
    st, cond = m.solve(solver_name="highs")
    assert st == "ok"
    unscale_solution(m, led); b.optimize.assign_solution(); b.optimize.assign_duals()
    assert b.objective == pytest.approx(a.objective, rel=1e-9)
    assert b.stores.e_nom_opt["st"] == pytest.approx(a.stores.e_nom_opt["st"], rel=1e-6, abs=1e-9)
    assert (b.stores_t.e["st"] - a.stores_t.e["st"]).abs().max() < 1e-6


@pytest.mark.skipif(not (R4 / "B_scaled" / "SOLVE_RECEIPT.json").exists(), reason="R4 runs not available")
def test_r4_equivalence_receipts():
    ra = json.loads((R4 / "A_unscaled" / "SOLVE_RECEIPT.json").read_text()); rb = json.loads((R4 / "B_scaled" / "SOLVE_RECEIPT.json").read_text())
    ref = 6.98803335e11
    assert ra["termination_condition"] == rb["termination_condition"] == "optimal"
    assert abs(ra["objective"] - ref) / ref <= 1e-6 and abs(rb["objective"] - ref) / ref <= 1e-6 and abs(ra["objective"] - rb["objective"]) / ra["objective"] <= 1e-6
    assert rb["scaling"]["objective_constants"]["total_eur"] == pytest.approx(2528892792.8351293, rel=1e-9)
    assert rb["objective"] == pytest.approx(rb["objective_lp"] + rb["scaling"]["objective_constants"]["total_eur"], rel=1e-12)
    cs = rb["gurobi_log_stats"]["coefficient_statistics"]
    assert cs["objective"]["max"] <= 1e7 and cs["bounds"]["max"] <= 1e5 and not rb["gurobi_log_stats"]["lines"].get("warning")
