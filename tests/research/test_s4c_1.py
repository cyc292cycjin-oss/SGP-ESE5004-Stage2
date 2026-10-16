"""S4C-1 (decision 82) and supplement 01 (decision 16): cost-layer pricing of the electric-base candidates, offshore connection cost,
corridor subsea shares (user decisions 2026-10-16: landmass_nonland main, not-land share, PyPSA-Eur distance formula), full audit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
SUB = ROOT / "research_inputs/corridors/SUBSEA_SHARE_S4C1.csv"
DIST = ROOT / "research_inputs/renewable_v5/OFFWIND_CONNECTION_DISTANCE_S4C1.csv"
BUILD = ROOT / "results_project/s4c/build_s4c1"
LAYER = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv"


@pytest.fixture(scope="module")
def sub():
    return pd.read_csv(SUB)


def pair(t, a, b):
    k = tuple(sorted((a, b)))
    return t[(t.loc0 == k[0]) & (t.loc1 == k[1])].iloc[0]


def test_subsea_decision_table(sub):
    for col in ["landmass0", "landmass1", "same_landmass", "subsea_share_eez", "subsea_share_not_land", "share_zero", "share_geometric_all", "share_landmass_nonland"]:
        assert col in sub
    assert (sub.share_zero == 0).all() and np.allclose(sub.share_geometric_all, sub.subsea_share_not_land)
    assert (sub.loc[sub.same_landmass, "share_landmass_nonland"] == 0).all()
    assert np.allclose(sub.loc[~sub.same_landmass, "share_landmass_nonland"], sub.loc[~sub.same_landmass, "subsea_share_not_land"])
    # supplement item 4 common-sense checks
    assert pair(sub, "KH2 0", "VN2 0").share_landmass_nonland == 0 and pair(sub, "LA2 0", "TH2 1").share_landmass_nonland == 0
    assert pair(sub, "MY_Peninsular22 0", "TH21 0").share_landmass_nonland == 0
    assert pair(sub, "SG2 0", "ID_Sumatra2 0").share_landmass_nonland > 0.4
    assert pair(sub, "MY_Peninsular2 1", "MY_Sabah4 0").share_geometric_all > 0.8
    # the stop-report cases: overland lines on one landmass are 0 in the main rule
    for a, b in [("TH2 3", "TH2 5"), ("VN2 2", "VN2 3"), ("ID_Kalimantan4 8", "MY_Sarawak4 1"), ("ID_Sulawesi0 0", "ID_Sulawesi0 1")]:
        r = pair(sub, a, b)
        assert r.same_landmass and r.share_landmass_nonland == 0 and r.share_geometric_all > 0.1
    # inter-island DC links keep their geometric share
    assert pair(sub, "PH_Visayas10 0", "PH_Visayas7 0").share_landmass_nonland > 0.8


def test_offwind_distance_table():
    d = pd.read_csv(DIST)
    lay = d[d.basis == "LAYOUT"]
    assert set(d.tech) == {"offwind-ac", "offwind-dc"} and (d.landfall_km == d.tech.map({"offwind-ac": 20.0, "offwind-dc": 30.0})).all() and (d.line_length_factor == 1.25).all()
    assert np.allclose(lay.potential_mw, lay.potential_mw_s4a, rtol=1e-9)
    assert (d.average_distance_km > 0).all() and len(d[d.basis != "LAYOUT"]) == 10


def test_class_of():
    from s4c_layers import _class_of
    assert _class_of("VN2 7 offwind-dc-2025") == 0 and _class_of("VN2 7 offwind-dc-2025 c2") == 2 and _class_of("X c") == 0


@pytest.mark.skipif(not (BUILD / "integrated" / "integrated_2920_3h_unsolved.nc").exists(), reason="S4C-1 build not present")
def test_built_network_cost_layer():
    import pypsa
    c = pd.read_csv(BUILD / "integrated" / "costs_active_research.csv", index_col=0)
    n = pypsa.Network(str(BUILD / "integrated" / "integrated_2920_3h_unsolved.nc"))
    g = n.generators; ext = g.p_nom_extendable
    assert np.allclose(g.loc[ext & (g.carrier == "onwind"), "capital_cost"], c.at["onwind", "fixed"])
    assert np.allclose(g.loc[ext & (g.carrier == "solar"), "capital_cost"], c.at["solar-utility", "fixed"])
    assert np.allclose(g.loc[ext & (g.carrier == "solar rooftop"), "capital_cost"], c.at["solar-rooftop", "fixed"])
    off = g[ext & g.carrier.str.startswith("offwind")]
    assert (off.capital_cost > c.at["offwind", "fixed"]).all()
    L = n.lines
    assert np.allclose(L.capital_cost, L.length * ((1 - L.underwater_fraction) * c.at["HVAC overhead", "fixed"] + L.underwater_fraction * c.at["HVAC submarine", "fixed"]))
    th = L[((L.bus0 == "TH2 3") & (L.bus1 == "TH2 5")) | ((L.bus0 == "TH2 5") & (L.bus1 == "TH2 3"))]
    assert len(th) and (th.underwater_fraction == 0).all()
    led = n.meta["research_cost_layer_s4c1"]
    assert led["electric_base_candidates"] == "cost_layer" and led["subsea_share"] == "landmass_nonland" and not led["offwind_missing_distance"]
    audit = ROOT / "results_project/s4c/s4c1/audit_integrated/COST_AUDIT_S4C1_SUMMARY.json"
    if audit.exists():
        assert json.loads(audit.read_text())["unresolved"] == []


@pytest.mark.skipif(not (BUILD / "electric_base" / "integrated_2920_3h_unsolved.nc").exists(), reason="comparison build not present")
def test_electric_base_comparison_keeps_author_costs():
    import pypsa
    n = pypsa.Network(str(BUILD / "electric_base" / "integrated_2920_3h_unsolved.nc"))
    g = n.generators
    assert np.allclose(g.loc[g.p_nom_extendable & (g.carrier == "onwind"), "capital_cost"], 114912.451148, rtol=1e-9)
    assert np.allclose(g.loc[g.p_nom_extendable & (g.carrier == "solar"), "capital_cost"], 71545.771361, rtol=1e-9)
