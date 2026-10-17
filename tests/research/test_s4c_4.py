"""S4C-4 (decision 89): extra-ASEAN CO2 storage option - unit cost from IEAGHG 2004 (ship transport) + ZEP 2011 (offshore storage), switch on | off."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4c_layers import EXTRA_ASEAN_CARRIER, EXTRA_ASEAN_LINK, extra_asean_mode  # noqa: E402

TAB = ROOT / "research_inputs/co2_v5/EXTRA_ASEAN_STORAGE_COST_S4C4.csv"
REG = ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv"
BUILD = ROOT / "results_project/s4c/build_s4c4"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())


def test_unit_cost_chain():
    t = pd.read_csv(TAB).set_index(["item", "distance_km"])
    tot = float(t.loc[("unit_cost_main", 4500.0), "eur2020_per_t"])
    assert tot == pytest.approx(40.752, abs=0.01)
    # component sums reproduce the printed IEAGHG 2004 Table 5-3 totals (17.3 / 24.9 US$/t)
    assert float(t.loc[("shipping_chain_total", 3000.0), "value"]) == pytest.approx(17.3, abs=0.06)
    assert float(t.loc[("shipping_chain_total", 6000.0), "value"]) == pytest.approx(24.9, abs=0.06)
    ship = float(t.loc[("shipping_chain_total", 4500.0), "eur2020_per_t"])
    stor = float(t.reset_index().set_index("item").at["storage_offshore_SA_no_legacy_medium", "eur2020_per_t"])
    assert ship == pytest.approx(21.128 * 1.16898, rel=1e-4) and stor == pytest.approx(14.0 * 1.14668, rel=1e-4)
    assert tot == pytest.approx(ship + stor, rel=1e-9)
    r = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id").loc["co2_extra_asean_storage_cost"]
    assert r.status == "REGISTERED" and r.tier == "C" and r.source_sha256
    assert float(r.value) == pytest.approx(tot, rel=1e-9)
    assert float(r.sensitivity_low) == pytest.approx(0.5 * tot) and float(r.sensitivity_high) == pytest.approx(1.5 * tot)


def test_switch():
    assert extra_asean_mode(CFG) == "on"
    c = copy.deepcopy(CFG); c["research"]["co2"]["extra_asean_storage"] = "off"; assert extra_asean_mode(c) == "off"
    c["research"]["co2"]["extra_asean_storage"] = True; assert extra_asean_mode(c) == "on"
    c["research"]["co2"]["extra_asean_storage"] = "maybe"
    with pytest.raises(ValueError):
        extra_asean_mode(c)


present = all((BUILD / t / f"{s}_2920_3h_unsolved.nc").exists() for t, s in [("integrated", "integrated"), ("disconnected", "disconnected"), ("disconnected_off", "disconnected")])


@pytest.mark.skipif(not present, reason="S4C-4 builds not present")
def test_builds():
    import pypsa
    price = float(pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id").at["co2_extra_asean_storage_cost", "value"])
    for t, s in [("integrated", "integrated"), ("disconnected", "disconnected")]:
        n = pypsa.Network(str(BUILD / t / f"{s}_2920_3h_unsolved.nc"))
        st = n.stores[n.stores.carrier == EXTRA_ASEAN_CARRIER]; lk = n.links[n.links.carrier == EXTRA_ASEAN_LINK]
        assert len(st) == 11 and set(st.country) == set(n.buses.country[n.buses.carrier == "AC"])
        assert (st.capital_cost == price).all() and st.e_nom_extendable.all() and (st.e_nom_max == float("inf")).all() and not st.e_cyclic.any()
        assert all(n.meta["store_power_rules"][x] == "charge_only" for x in st.index)
        # same nodes as the national sequestration links: every captured-CO2 buffer node (97; the 3 auxiliary co2 stored buses
        # MY_Peninsular22 0 / PH_Visayas10 0 / TH21 0 carry only FT and SMR CC, no buffer, vent or sequestration - pre-existing structure)
        buffered = set(n.stores.bus[n.stores.research_role == "CO2_BUFFER"])
        assert (lk.border_class == "domestic").all() and set(lk.bus0) == buffered and len(lk) == 97
        assert set(lk.bus0) == set(n.links.bus0[n.links.carrier == "CO2 sequestration"]) | {b for b in buffered if n.buses.at[b, "country"] not in set(n.stores.country[n.stores.carrier == "co2 sequestered"])}
        assert all(n.buses.at[b, "country"] == n.buses.at[lk.at[x, "bus1"], "country"] for x, b in lk.bus0.items())   # export books the capturing country
        assert "research_co2_storage_cap" in n.meta["required_constraint_hooks"]   # national caps untouched (extra-ASEAN stores are not in research_co2_storage)
        assert set(n.meta["research_co2_storage"]["caps_t_per_year"]) == set(st.country)
    n = pypsa.Network(str(BUILD / "disconnected_off" / "disconnected_2920_3h_unsolved.nc"))
    assert not (n.stores.carrier == EXTRA_ASEAN_CARRIER).any() and n.meta["research_extra_asean_storage"]["mode"] == "off"
