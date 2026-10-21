"""M08a A3 (decision 131): existing stock priced with technology-data v0.15.0 of its commissioning year (toy networks; no build, no solve)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from m08a_layers import apply_existing_vintage_costs, vintage_tables, vintage_year   # noqa: E402

EVIDENCE = ROOT / "research/06_scope_redesign/p1_m08a_20261021/evidence/M08A_A3_EXISTING_VINTAGE.json"


@pytest.fixture(scope="module")
def cfgs():
    from phase4_static import config
    return config(ROOT, "integrated"), config(ROOT, "disconnected")


def toy():
    n = pypsa.Network(); n.set_snapshots(range(2))
    n.add("Bus", "X", carrier="AC"); n.add("Bus", "X gas", carrier="gas"); n.add("Bus", "co2 atmosphere XX", carrier="co2")
    n.add("Link", "ccgt", bus0="X gas", bus1="X", bus2="co2 atmosphere XX", carrier="CCGT existing", p_nom=400 / 0.57, efficiency=0.57, efficiency2=0.2,
          marginal_cost=4.0 * 0.57, capital_cost=0.0)
    n.add("Generator", "geo", bus="X", carrier="geothermal existing", p_nom=50.0, marginal_cost=0.26, capital_cost=0.0)
    n.add("StorageUnit", "hyd", bus="X", carrier="hydro existing", p_nom=80.0, efficiency_dispatch=0.9, marginal_cost=0.5, capital_cost=0.0)
    for typ, name, fom, mw in [("Link", "ccgt", 20000.0, 400.0), ("Generator", "geo", 17000.0, 50.0), ("StorageUnit", "hyd", 30000.0, 80.0)]:
        df = n.df(typ)
        df.loc[name, ["asset_role", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur"]] = ["existing_survivor", fom, fom * mw]
    n.meta["existing_unit_components"] = {
        "u1": dict(component_type="Link", component="ccgt", capacity_mw=100.0, commissioning_year=2015),
        "u2": dict(component_type="Link", component="ccgt", capacity_mw=300.0, commissioning_year=2024),
        "g1": dict(component_type="Generator", component="geo", capacity_mw=50.0, commissioning_year=2021),
        "h1": dict(component_type="StorageUnit", component="hyd", capacity_mw=80.0, commissioning_year=1965)}
    n.meta["existing_annual_fixed_om_eur"] = 20000.0 * 400 + 17000.0 * 50 + 30000.0 * 80
    return n


def test_year_rule():
    assert [vintage_year(y) for y in (1953, 2006, 2019, 2020, 2022, 2023, 2027, 2028, 2032, 2033, 2047, 2048, 2060)] == \
        [2020, 2020, 2020, 2020, 2020, 2025, 2025, 2030, 2030, 2035, 2045, 2050, 2050]
    with pytest.raises(ValueError):
        vintage_year(2024, dict(rounding="floor"))


def test_tables_ccgt_efficiency(cfgs):
    t, files = vintage_tables(cfgs[0], ROOT)
    assert sorted(t) == [2020, 2025, 2030, 2035, 2040, 2045, 2050]
    assert [round(float(t[y].at["CCGT", "efficiency"]), 4) for y in (2020, 2025, 2030, 2050)] == [0.56, 0.57, 0.58, 0.6]   # expected 0.56 / 0.57 (instruction A3)
    main = pd.read_csv(ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv", index_col=0)
    assert float(t[2050].at["CCGT", "investment"]) == float(main.at["CCGT", "investment"])


def test_rule_on_toy_network(cfgs):
    cfg = cfgs[0]
    t, _ = vintage_tables(cfg, ROOT)
    n = toy(); led = apply_existing_vintage_costs(n, cfg, ROOT)
    c20, c25 = t[2020].loc["CCGT"], t[2025].loc["CCGT"]
    eff = 400 / (100 / c20.efficiency + 300 / c25.efficiency)
    fom = (100 * c20.FOM / 100 * c20.investment + 300 * c25.FOM / 100 * c25.investment) / 400
    vom = (100 * c20.VOM + 300 * c25.VOM) / 400
    z = n.links.loc["ccgt"]
    assert z.efficiency == pytest.approx(eff, rel=1e-12) and z.p_nom * z.efficiency == pytest.approx(400, rel=1e-12)
    assert z.marginal_cost == pytest.approx(vom * eff, rel=1e-12) and z.existing_fixed_om_eur_per_mw_year == pytest.approx(fom, rel=1e-12)
    assert z.existing_annual_fixed_om_eur == pytest.approx(fom * 400, rel=1e-12) and z.efficiency2 == 0.2 and z.capital_cost == 0
    h, h20 = n.storage_units.loc["hyd"], t[2020].loc["hydro"]
    assert h.efficiency_dispatch == 0.9 and h.marginal_cost == pytest.approx(float(h20.VOM)) and h.existing_fixed_om_eur_per_mw_year == pytest.approx(h20.FOM / 100 * h20.investment)
    g = n.generators.loc["geo"]
    assert (g.marginal_cost, g.existing_fixed_om_eur_per_mw_year) == (0.26, 17000.0)   # AEO8 exception
    total = n.links.at["ccgt", "existing_annual_fixed_om_eur"] + 17000.0 * 50 + n.storage_units.at["hyd", "existing_annual_fixed_om_eur"]
    assert n.meta["existing_annual_fixed_om_eur"] == pytest.approx(total, rel=1e-12) and led["fom_after_eur"] == pytest.approx(total, rel=1e-12)
    assert led["components"] == 2 and led["by_carrier"]["CCGT existing"]["table_years"] == [2020, 2025]


def test_same_existing_fom_in_both_scenarios_and_former_mode(cfgs):
    a, b = toy(), toy()
    la = apply_existing_vintage_costs(a, cfgs[0], ROOT); lb = apply_existing_vintage_costs(b, cfgs[1], ROOT)
    assert la["fom_after_eur"] == lb["fom_after_eur"]
    pd.testing.assert_frame_equal(a.links, b.links); pd.testing.assert_frame_equal(a.storage_units, b.storage_units)
    old = copy.deepcopy(cfgs[0]); old["research"]["fleet"]["existing_cost_basis"] = "author_v0_13_2"
    c = toy(); lc = apply_existing_vintage_costs(c, old, ROOT)
    assert lc["fom_after_eur"] == lc["fom_before_eur"] and c.links.at["ccgt", "efficiency"] == 0.57
    bad = toy(); bad.links.loc["ccgt", "carrier"] = "gas CHP existing"
    with pytest.raises(ValueError):
        apply_existing_vintage_costs(bad, cfgs[0], ROOT)


@pytest.mark.skipif(not EVIDENCE.exists(), reason="A3 evidence not generated")
def test_evidence_on_built_networks():
    e = json.loads(EVIDENCE.read_text())
    assert e["solver_runs"] == 0 and e["network_files_changed"] == 0 and e["fom_identical_between_scenarios"] is True
    i = e["by_scenario"]["integrated"]
    assert i["fom_after_eur"] == e["by_scenario"]["disconnected"]["fom_after_eur"]
    vals = i["by_carrier"]["CCGT existing"]["efficiency_after_values"]
    assert min(vals) == 0.56 and 0.57 in vals
