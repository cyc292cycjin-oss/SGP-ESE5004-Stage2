"""S4F-1 (decision 96): PyPSA-Eur individual line / DC-link extension limit, apg_plans sensitivity."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4f_1_data import CONF, PSN, check_line, plan_caps, upper  # noqa: E402
from s4f_layers import APG_CAP_HOOK, apg_plan_groups, apply_max_extension, install_apg_corridor_cap, max_extension_mode  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4f/s4f1/builds"


def test_pypsa_eur_source_lines():
    assert "max_extension: 20000" in check_line(CONF, 324, "max_extension") and "max_extension: 30000" in check_line(CONF, 340, "max_extension")
    check_line(PSN, 6415, 'snakemake.params["lines"]["max_extension"]')
    check_line(PSN, 5575, 'n.lines["s_nom_max"] = n.lines["s_nom"] + maxext')
    check_line(PSN, 5577, 'n.links.loc[hvdc, "p_nom_max"] = n.links.loc[hvdc, "p_nom"] + maxext')
    assert 'params["links"]["max_extension"]' not in PSN.read_text()   # links.max_extension unused by the sector workflow
    assert float(REG.at["pypsa_eur_lines_max_extension", "value"]) == 20000.0 and REG.at["pypsa_eur_lines_max_extension", "status"] == "REGISTERED"
    assert float(REG.at["pypsa_eur_links_max_extension", "value"]) == 30000.0 and REG.at["pypsa_eur_links_max_extension", "status"] == "REFERENCE_ONLY"


def test_switch():
    assert max_extension_mode(CFG) == "pypsa_eur"
    c = copy.deepcopy(CFG); del c["research"]["network"]["max_extension"]
    assert max_extension_mode(c) == "none"
    c["research"]["network"]["max_extension"] = "half"
    with pytest.raises(ValueError):
        max_extension_mode(c)


def toy():
    import pypsa
    n = pypsa.Network(); n.set_snapshots(range(2))
    for b, x in [("TH2 0", 100), ("TH2 1", 101), ("LA2 0", 102), ("VN2 0", 106), ("SG2 0", 104), ("ID_Sumatra3 3", 101.5)]:
        n.add("Bus", b, x=x, y=10, carrier="AC", country=b[:2])
    n.add("Line", "l_thla", bus0="TH2 0", bus1="LA2 0", x=0.1, s_nom=955.0, s_nom_min=955.0, s_nom_extendable=True, capital_cost=1.0)
    n.add("Line", "l_th", bus0="TH2 0", bus1="TH2 1", x=0.1, s_nom=100.0, s_nom_min=100.0, s_nom_extendable=True, capital_cost=1.0)
    n.add("Link", "dc_sgid", bus0="SG2 0", bus1="ID_Sumatra3 3", carrier="DC", p_nom=0.0, p_nom_extendable=True, p_min_pu=-1, capital_cost=1.0)
    n.add("Link", "b2b", bus0="LA2 0", bus1="VN2 0", carrier="B2B", p_nom=50.0, p_nom_extendable=True, capital_cost=1.0)
    n.add("Link", "pipe", bus0="LA2 0", bus1="VN2 0", carrier="H2 pipeline", p_nom=0.0, p_nom_extendable=True, capital_cost=1.0)
    return n


def test_apply_pypsa_eur_and_none():
    n = toy(); led = apply_max_extension(n, CFG, REG)
    assert led["mode"] == "pypsa_eur" and led["max_extension_mw"] == 20000.0
    np.testing.assert_allclose(n.lines.s_nom_max, n.lines.s_nom + 20000.0)
    assert n.links.at["dc_sgid", "p_nom_max"] == 20000.0
    assert np.isinf(n.links.at["b2b", "p_nom_max"]) and np.isinf(n.links.at["pipe", "p_nom_max"])   # B2B and pipelines not capped (PyPSA-Eur)
    c = copy.deepcopy(CFG); c["research"]["network"]["max_extension"] = "none"; m = toy(); apply_max_extension(m, c, REG)
    assert np.isinf(m.lines.s_nom_max).all() and np.isinf(m.links.p_nom_max).all()


def test_apg_plans_groups_and_hook():
    table = plan_caps()
    row = table.set_index("apg_no")
    assert row.at["9", "plan_cap_mw"] == 955.0 and row.at["16", "plan_cap_mw"] == 3400.0 and row.at["18b", "plan_cap_mw"] == 10000.0
    assert "8a" not in row.index and upper("130-630") == 630 and upper("600/TBC") == 600 and upper("TBC") is None
    n = toy(); g = apg_plan_groups(n, table)
    assert g["9"]["lines"] == ["l_thla"] and g["9"]["cap_mw"] == 955.0 and g["16"]["links"] == ["dc_sgid"] and g["16"]["cap_mw"] == 3400.0
    assert "l_th" not in sum((v["lines"] for v in g.values()), [])
    c = copy.deepcopy(CFG); c["research"]["network"]["max_extension"] = "apg_plans"
    n = toy(); led = apply_max_extension(n, c, REG, ROOT)
    assert APG_CAP_HOOK in n.meta["required_constraint_hooks"] and led["apg_groups"] == 2
    n.add("Load", "d", bus="LA2 0", p_set=10.0); n.add("Generator", "g", bus="TH2 0", p_nom=100.0, marginal_cost=1.0)
    n.optimize.create_model(); assert install_apg_corridor_cap(n) == 2
    assert f"{APG_CAP_HOOK}-9" in n.model.constraints and f"{APG_CAP_HOOK}-16" in n.model.constraints


present = all((B / t).exists() for t in ("integrated", "disconnected", "integrated_none", "integrated_apg"))


@pytest.mark.skipif(not present, reason="S4F-1 builds not present")
def test_builds():
    import pypsa
    n = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    dc = n.links[n.links.carrier == "DC"]
    np.testing.assert_allclose(n.lines.s_nom_max, n.lines.s_nom + 20000.0); np.testing.assert_allclose(dc.p_nom_max, dc.p_nom + 20000.0)
    assert np.isinf(n.links[n.links.carrier.str.contains("pipeline")].p_nom_max).all()
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    np.testing.assert_allclose(d.lines.s_nom_max, d.lines.s_nom + 20000.0)
    o = pypsa.Network(str(B / "integrated_none" / "integrated_2920_3h_unsolved.nc"))
    assert np.isinf(o.lines.s_nom_max).all() and o.meta["research_max_extension"]["mode"] == "none"
    a = pypsa.Network(str(B / "integrated_apg" / "integrated_2920_3h_unsolved.nc"))
    assert APG_CAP_HOOK in a.meta["required_constraint_hooks"] and len(a.meta["research_apg_corridor_caps"]) >= 15
