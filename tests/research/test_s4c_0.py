"""S4C-0 (decisions 85, 86, 90): fuel price scenario switch, small items, discount rate / WACC switch."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
FIN = ROOT / "research_inputs" / "finance_v5"
BUILD = ROOT / "results_project" / "s4c" / "build_s4c0"


@pytest.fixture(scope="module")
def registry():
    return pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")


def test_registry_rows(registry):
    r = registry
    assert r.loc["fuel_price_scenario_main", "value"] == "steps" and "price taker" in r.loc["fuel_price_scenario_main", "description"]
    assert r.loc["lng_upstream_emissions_out_of_scope", "status"] == "REFERENCE_ONLY"
    assert r.loc["fuel_price_lng_regasification_adder", "status"] == "REGISTERED"   # M08a A4 (decision 131): 1.26 EUR2020/MWh (former DATA_PENDING)
    assert float(r.loc["btl_capital_cost_x_efficiency", "value"]) == pytest.approx(252723.449125 * 0.45, rel=1e-9)
    for pid in ["limitation_electricity_grid_connection", "limitation_pipeline_compression", "candidate_pipeline_statuses_confirmed", "tests_gate4_activation_accepted_state",
                "download_declined_wdpa_full", "download_declined_dea_2026_xlsx", "synthetic_methane_cross_border_accounting_accepted", "acceptance_column_dual_sign_scale_confirmed",
                "discount_rate_uniform_main", "finance_wacc_mode"]:
        assert pid in r.index and ("86" in r.loc[pid, "decision_ref"] or "90" in r.loc[pid, "decision_ref"])
    assert all(r.loc[f"wacc_country_model_{c}", "status"] == "DATA_PENDING" for c in ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"])


def test_wacc_public_table():
    t = pd.read_csv(FIN / "COUNTRY_WACC_PUBLIC_SOURCES.csv", keep_default_na=False)
    solar = t[t.technology.str.startswith("solar PV 50") & (t.fid_year.astype(str) == "2024")].set_index("country")
    assert solar.loc["ID", "published_cell"] == "8.5%-11.0%" and solar.loc["VN", "published_cell"] == "8.5%-10.0%" and solar.loc["TH", "published_cell"] == "6.0%-8.0%*"
    assert (t[t.status == "REFERENCE_ONLY"].basis.str.startswith("nominal, post-tax")).all()
    model = t[t.technology.str.startswith("model")]
    assert len(model) == 11 and (model.status == "DATA_PENDING").all() and (model.wacc_real == "").all()
    use = pd.read_csv(FIN / "DISCOUNT_RATE_IN_USE.csv", keep_default_na=False)
    assert "solar-rooftop" in use.scope.iloc[1] and float(use.discount_rate.iloc[0]) == 0.07


def _tiny():
    import pypsa
    n = pypsa.Network(); n.set_snapshots(range(2))
    n.add("Bus", "a", carrier="AC"); n.buses["country"] = ["ID"]
    n.add("Generator", "pv", bus="a", carrier="solar", p_nom_extendable=True, capital_cost=100.0); n.generators["country"] = ["ID"]
    return n


def test_wacc_country_specific_refuses_pending_and_rescales(tmp_path):
    from phase4_static import config
    from s2_costs import annuity, build_research_costs
    from s4c_layers import apply_wacc_mode
    cfg = config(ROOT, "integrated"); costs, _ = build_research_costs(ROOT, cfg, REG)
    n = _tiny(); led = apply_wacc_mode(n, costs, cfg, ROOT)
    assert led["mode"] == "uniform" and n.generators.at["pv", "capital_cost"] == 100.0
    cs = copy.deepcopy(cfg); cs["research"]["finance"]["wacc_mode"] = "country_specific"
    cs["research"]["finance"]["country_wacc_table"] = "research_inputs/finance_v5/COUNTRY_WACC_PUBLIC_SOURCES.csv"   # S4C-0 table (model rows DATA_PENDING); M08a main table COUNTRY_WACC_REAL_M08A.csv
    with pytest.raises(ValueError, match="no sourced WACC"):
        apply_wacc_mode(_tiny(), costs, cs, ROOT)
    syn = tmp_path / "wacc.csv"   # SYNTHETIC_TEST_ONLY table
    pd.DataFrame([dict(country="ID", technology="model", wacc_real=0.10, status="REGISTERED")]).to_csv(syn, index=False)
    cs["research"]["finance"]["country_wacc_table"] = str(syn)
    n = _tiny(); led = apply_wacc_mode(n, costs, cs, ROOT)
    life, fom, r0 = float(costs.at["solar-utility", "lifetime"]), float(costs.at["solar-utility", "FOM"]) / 100, float(costs.at["solar-utility", "discount rate"])
    assert n.generators.at["pv", "capital_cost"] == pytest.approx(100.0 * (annuity(life, 0.10) + fom) / (annuity(life, r0) + fom), rel=1e-12) and led["changed"] == 1


def _net(sc):
    import pypsa
    p = BUILD / sc / f"{sc}_2920_3h_unsolved.nc"
    return pypsa.Network(str(p)) if p.exists() else None


@pytest.mark.skipif(not (BUILD / "integrated" / "integrated_2920_3h_unsolved.nc").exists(), reason="S4C-0 build not present")
def test_built_network_prices_and_btl(registry):
    for sc in ["integrated", "disconnected"]:
        n = _net(sc)
        if n is None:
            continue
        led = n.meta["research_fuel_prices"]
        assert led["scenario"] == "steps" and led["status"] == "PASS"
        g = n.generators
        steps_gas = float(registry.loc["fuel_price_gas_STEPS_2050_high_price", "value"])
        assert np.allclose(g.loc[g.carrier == "LNG import", "marginal_cost"], steps_gas) and np.allclose(g.loc[g.carrier == "gas production", "marginal_cost"], steps_gas)
        assert float(g.at["ASEAN oil import", "marginal_cost"]) == pytest.approx(float(registry.loc["fuel_price_oil_STEPS_2050_high_price", "value"]))
        coal = g[(g.carrier == "coal") & (g.research_role == "EXTERNAL_SUPPLY")]
        assert np.allclose(coal.marginal_cost, float(registry.loc["fuel_price_coal_STEPS_2050_high_price", "value"]))
        btl = n.links[n.links.carrier == "BtL"]
        assert np.allclose(btl.capital_cost, float(registry.loc["btl_capital_cost_x_efficiency", "value"]))
        assert n.meta["research_finance"]["mode"] == "uniform"
