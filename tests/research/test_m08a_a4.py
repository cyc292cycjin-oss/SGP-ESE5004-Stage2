"""M08a A4 / M08-3 (decision 131): LNG terminals without cap at a sourced capex, regasification adder, H2 terminal = LNG x 1.2
(toy network from the GEM table; no build, no solve)."""
from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pandas as pd
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
from s3_layers import add_lng_terminals, h2_terminal_capex, LNG_EXPANSION_MODES   # noqa: E402

REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
ULVESTAD = 8020.43343542


@pytest.fixture(scope="module")
def cfg():
    from phase4_static import config
    return config(ROOT, "integrated")


def toy(cfg):
    G = cfg["research"]["s3"]["gas"]
    t = pd.read_csv(ROOT / G["lng_terminals"], keep_default_na=False)
    n = pypsa.Network(); n.set_snapshots(range(2))
    for node, g in t[t.node != ""].groupby("node"):
        n.add("Bus", node, carrier="AC"); n.buses.loc[node, "country"] = str(g.country.iloc[0])
        n.add("Bus", f"{node} gas", carrier="gas"); n.buses.loc[f"{node} gas", "country"] = str(g.country.iloc[0])
    return n


def lng_gens(n):
    return n.generators[n.generators.carrier == "LNG import"]


def test_config_main_values(cfg):
    G = cfg["research"]["s3"]["gas"]
    assert G["lng_expansion"] == "capex_only" and "capex_only" in LNG_EXPANSION_MODES
    assert G["lng_expansion_capital_cost_eur_per_mw_a"] == ULVESTAD and G["lng_regasification_adder_eur_per_mwh"] == 1.26
    assert G["lng_terminals"].endswith("LNG_IMPORT_TERMINALS_GEM_2025.csv")   # GEM GGIT 2025-09 table unchanged


def test_capex_only_uncapped_with_cost_and_adder(cfg):
    n = toy(cfg); led = {}
    lng = add_lng_terminals(n, cfg, ROOT, 27.07, 1.26, led)
    g = lng_gens(n)
    assert len(g) == 16 and (g.p_nom_max == math.inf).all()                      # 9 existing + 7 proposed-only sites, p_nom_max = inf
    assert (g.capital_cost == ULVESTAD).all() and (g.marginal_cost == 27.07 + 1.26).all()
    assert (g.p_nom == g.p_nom_min).all() and int((g.p_nom > 0).sum()) == 9 and g.p_nom_extendable.all()
    assert lng["expansion"] == "capex_only" and "Ulvestad" in lng["expansion_cost_source"] and "1.26" in lng["adder_status"]
    assert all(t.get("h2_import_cap_mw", 0) >= 0 for t in lng["terminals"].values())
    from v5_gates import gate_b14_terminal_caps
    n.meta["research_gas_network"] = led
    assert gate_b14_terminal_caps(n)["passed"] is True


def test_former_cap_and_cost_sensitivity(cfg):
    c = copy.deepcopy(cfg); G = c["research"]["s3"]["gas"]
    G["lng_expansion"] = "cap_factor_cost"
    n = toy(c); led = {}; add_lng_terminals(n, c, ROOT, 27.07, 1.26, led)
    g = lng_gens(n); ex = g[g.p_nom > 0]
    assert ((ex.p_nom_max / ex.p_nom - 2.5).abs() < 1e-9).all() and (g.capital_cost == ULVESTAD).all()
    G["lng_expansion"] = "capex_only"; G["lng_expansion_cost_sensitivity"] = 0.5
    n = toy(c); add_lng_terminals(n, c, ROOT, 27.07, 1.26, {})
    import numpy as np
    assert np.allclose(lng_gens(n).capital_cost, ULVESTAD * 1.5, rtol=1e-12)
    assert h2_terminal_capex(c)[0] == pytest.approx(ULVESTAD * 1.5 * 1.2)


def test_h2_terminal_is_lng_times_1_2(cfg):
    v, rule = h2_terminal_capex(cfg)
    assert v == pytest.approx(ULVESTAD * 1.2, rel=1e-12) and "x 1.2" in rule
    c = copy.deepcopy(cfg); c["research"]["s3"]["imports"]["h2_terminal_capital_cost_rule"] = "fixed"
    assert h2_terminal_capex(c)[0] == 8421.6


def test_registry_rows():
    r = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["lng_terminal_cap_rule", "value"] == "capex_only" and r.loc["lng_terminal_capacity_source", "value"] == "gem_ggit_2025_09"
    assert float(r.loc["lng_terminal_expansion_capex_main", "value"]) == pytest.approx(ULVESTAD) and r.loc["lng_terminal_expansion_capex_main", "status"] == "REGISTERED"
    assert float(r.loc["fuel_price_lng_regasification_adder", "value"]) == 1.26 and r.loc["fuel_price_lng_regasification_adder", "status"] == "REGISTERED"
    for pid in ("lng_terminal_expansion_mode_s4b", "lng_import_cap_rule_built", "lng_import_cap_factor", "lng_import_cap_built_VN"):
        assert r.loc[pid, "status"] == "REFERENCE_ONLY" and "历史：已被 lng_terminal_cap_rule 替代" in r.loc[pid, "description"]
    assert float(r.loc["h2_terminal_capex_rule", "value"]) == pytest.approx(ULVESTAD * 1.2)
