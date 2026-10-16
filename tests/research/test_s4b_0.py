"""S4B-0 (decisions 70-73): PyPSA-Eur sector switches, solver-tolerance acceptance, LNG expansion at cost, gas slack in the gap diagnostic,
other-bucket value asean_own_2019."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5"
PE_CFG = REG / "sources" / "pypsa_eur_v2025.07.0_config.default.yaml"
NET = ROOT / "results_project/s4b/s4b0/builds/integrated/integrated_2920_3h_unsolved.nc"
GAP = ROOT / "results_project/s4b/s4b0/builds/disconnected_gap/disconnected_gap_diagnostic_2920_3h_unsolved.nc"


def test_config_defaults():
    from phase4_static import config
    R = config(ROOT, "integrated")["research"]
    S = R["sector"]
    assert S["methanation"] is True and S["electrobiofuels"] is True and S["min_part_load_fischer_tropsch"] == 0.5 and S["min_part_load_methanation"] == 0.3
    assert all(S[k] is True for k in ["hydrogen_fuel_cell", "SMR", "SMR_cc", "biomass_to_liquid"])
    assert R["s2"]["co2"]["vent"] is False and R["hydrogen"]["h2_turbine"] is True
    G = R["s3"]["gas"]
    assert G["lng_expansion"] == "cap_factor_cost" and G["lng_expansion_capital_cost_eur_per_mw_a"] == 7018.0 and G["lng_expansion_cost_sensitivity"] == 0.0
    I = R["solver"]["interior"]
    assert I["acceptance_basis"] == "solver_tolerances" and I["feasibility_tol"] == 1e-6 and I["optimality_tol"] == 1e-6 and I["solver_tol_factor"] == 10 and I["gap_factor"] == 10
    gd = R["s2"]["gap_diagnostic"]
    assert "gas" in gd["slacks"] and gd["penalty_eur_per_mwh_gas"] == gd["penalty_eur_per_mwh"] == 10000


def test_switch_table_cites_pypsa_eur_lines():
    t = pd.read_csv(ROOT / "research_inputs/sector_v5/SECTOR_SWITCHES_VS_PYPSA_EUR.csv", keep_default_na=False)
    assert set(t.status) <= {"aligned", "deviation_confirmed", "not_applicable", "USER_DECISION"}
    assert (t[t.status != "aligned"].reason != "").all()           # every deviation / n.a. / open item carries a reason
    lines = PE_CFG.read_text().splitlines()
    for key, line, val in [("methanation", 676, "true"), ("co2_vent", 679, "false"), ("hydrogen_turbine", 687, "true"), ("SMR", 688, "true"), ("SMR_cc", 689, "true"),
                           ("min_part_load_fischer_tropsch", 735, "0.5"), ("min_part_load_methanation", 737, "0.3"), ("biomass_to_liquid", 777, "true"), ("electrobiofuels", 779, "true")]:
        assert lines[line - 1].strip() == f"{key}: {val}", (key, lines[line - 1])
        assert key in set(t.pypsa_eur_key)
    r = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["lng_terminal_expansion_capex_main", "value"] == "7018" and r.loc["lng_terminal_expansion_capex_main", "sensitivity_low"] == "3509"
    assert r.loc["acceptance_tolerance_basis", "value"] == "solver_tolerances" and r.loc["industry_other_bucket_asean_own_2019", "status"] == "SENSITIVITY"


def test_asean_own_other_bucket_tables():
    D = ROOT / "research_inputs/demand_v5"
    for mode in ["aeo8_ats_relative", "gdp", "population", "aeo8_ats_relative_level"]:
        main = pd.read_csv(D / f"INDUSTRY_2050_SUMMARY_{mode}.csv").set_index("country")
        own = pd.read_csv(D / f"INDUSTRY_2050_SUMMARY_{mode}_OTHER_ASEAN_OWN_2019.csv").set_index("country")
        assert list(main.index) == list(own.index) and (own.other_bucket == "asean_own_2019").all()
        assert np.allclose(main.crude_steel_2050_t, own.crude_steel_2050_t) and np.allclose(main.cement_2050_t, own.cement_2050_t)
    import inspect
    import s2_layers
    assert "_OTHER_ASEAN_OWN_2019.csv" in inspect.getsource(s2_layers.add_demand_layer)


def test_acceptance_budgets_and_gross_flow():
    from s4b_acceptance import budgets, gate_b3_solver_tol
    B = budgets(dict(solver_tol_factor=10, feasibility_tol=1e-6, optimality_tol=1e-6, gap_factor=10), 1e-8)
    assert B["primal_relative"] == pytest.approx(1e-5) and B["dual_normalized"] == pytest.approx(1e-5) and B["gap"] == pytest.approx(1e-7)
    import pypsa
    n = pypsa.Network(); n.set_snapshots(range(3)); n.add("Bus", "b")
    n.add("Store", "pool", bus="b", e_nom=1e8, e_initial=1e8, e_cyclic=False); n.stores["research_role"] = "FINITE_RESOURCE"; n.stores["country"] = "ID"
    n.stores_t.e = pd.DataFrame({"pool": [5e7, 1e6, -0.0027]}, index=n.snapshots); n.stores_t.p = pd.DataFrame({"pool": [1.0, 1.0, 1.0]}, index=n.snapshots)
    assert gate_b3_solver_tol(n, B)["passed"]                     # -0.0027 MWh on a 1e8 MWh pool: within 1e-3 + 1e-5 x 1e8


@pytest.mark.skipif(not NET.exists(), reason="S4B-0 build not present")
def test_built_network_sector_and_lng():
    import pypsa
    n = pypsa.Network(str(NET)); L = n.links
    sab = L[L.carrier == "Sabatier"]; ebf = L[L.carrier == "electrobiofuels"]
    assert len(sab) == 97 and (sab.p_min_pu == 0.3).all() and sab.bus2.str.endswith(" co2 stored").all() and (sab.bus3.fillna("") == "").all()   # no synthesis port (decision 64)
    assert len(ebf) == 97 and ebf.bus1.str.endswith(" oil non-fossil").all() and (ebf.bus3.fillna("") == "").all()   # origin_neutral: like BtL
    assert ((L.carrier == "Fischer-Tropsch") & (L.p_min_pu == 0.5)).sum() == (L.carrier == "Fischer-Tropsch").sum() > 0
    assert (L.carrier == "co2 vent").sum() == 0
    lng = n.generators[n.generators.carrier == "LNG import"]
    assert (lng.capital_cost == 7018.0).all() and len(lng) == 16 and (lng.p_nom_max >= lng.p_nom).all()
    from v5.v5_gates import gate_b14_terminal_caps
    assert gate_b14_terminal_caps(n)["passed"]


@pytest.mark.skipif(not GAP.exists(), reason="S4B-0 gap build not present")
def test_gap_network_gas_slack():
    import pypsa
    n = pypsa.Network(str(GAP)); g = n.generators[n.generators.carrier == "gap slack gas"]
    from sector_adapter import spatial_nodes
    nodes = spatial_nodes(n); gas = [b for b in n.buses.index if b.endswith(" gas")]
    assert set(g.bus) == {f"{x} gas" for x in nodes if f"{x} gas" in n.buses.index} and (g.marginal_cost == 10000).all()
    b2b = n.links[n.links.carrier == "B2B"]; coupled = set(b2b.bus0) | set(b2b.bus1)
    rest = set(gas) - set(g.bus)   # gas buses of the B2B-coupled DC converter nodes (outside the spatial node list) carry no fixed gas load
    assert all(b[:-4] in coupled for b in rest) and not n.loads.bus.isin(rest).any()
    assert n.meta["gap_diagnostic"]["slacks"] == ["electricity", "co2", "biomass", "gas"]
