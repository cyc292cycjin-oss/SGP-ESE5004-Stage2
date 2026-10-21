"""S3-1 (decisions 15, 35, 43, 17, 19): gas network data layer and the built S3-1 networks (results_project/s3_1), solver-free."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5"
GAS = ROOT / "research_inputs" / "gas_v5"
S31 = ROOT / "results_project" / "s3_1"


@pytest.fixture(scope="module")
def registry():
    return pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")


def test_existing_cross_border_pipelines(registry):
    ex = pd.read_csv(GAS / "GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv", keep_default_na=False)
    assert len(ex) == 7 and set(ex.status) == {"REGISTERED", "DATA_PENDING"}
    ttm = ex[ex.pipeline.str.startswith("Trans Thailand")].iloc[0]
    assert float(ttm.capacity_bcm_per_year) == 10.42 and float(ttm.capacity_mw_ncv) == pytest.approx(10.42 * 1199.0 * 0.90, rel=1e-9) and ttm.direction == "bidirectional"
    mm = ex[(ex.country_from == "MM") & (ex.country_to == "TH")]
    assert len(mm) == 3 and float(mm.capacity_bcm_per_year.astype(float).sum()) == pytest.approx(12.83)   # Yetagun + Yadana 1 + Zawtika; Ban I-Tong-Ratchaburi onshore line 12.93 bcm/y
    assert (mm.from_node == "MM2 4").all() and (mm.to_node == "TH2 2").all()
    mysg = ex[ex.pipeline == "Malaysia Singapore Gas Pipeline"].iloc[0]
    assert mysg.status == "DATA_PENDING" and mysg.capacity_mw_ncv == ""
    assert registry.loc["gas_pipeline_existing_malaysia_singapore", "status"] == "DATA_PENDING"
    assert float(registry.loc["gas_pipeline_capacity_mw_per_bcm_year", "value"]) == pytest.approx(1199.0 * 0.9)
    noted = pd.read_csv(GAS / "GAS_PIPELINES_NOTED_2025.csv")
    assert set(noted.pipeline) >= {"JDA-Arthit Gas Pipeline", "Sino-Myanmar Gas Pipeline"}


def test_production_caps(registry):
    prod = pd.read_csv(GAS / "GAS_PRODUCTION_CAPS_2050.csv", keep_default_na=False).set_index("country")
    caps = pd.read_csv(REG / "FOSSIL_PRODUCTION_CAPS_2050.csv", keep_default_na=False)
    gas = caps[caps.carrier == "gas"].set_index("country")
    for c in prod.index:
        assert float(prod.at[c, "cap_mwh_per_year"]) == pytest.approx(float(gas.at[c, "cap_mwh_per_year"]))
    assert float(prod.at["SG", "cap_mwh_per_year"]) == 0.0 and "exported" in prod.at["TL", "note"]
    assert registry.loc["gas_production_node_allocation", "value"] == "load_shares" and registry.loc["gas_production_node_allocation", "tier"] == "C"
    assert float(registry.loc["gas_production_price_rule", "value"]) == pytest.approx(float(registry.loc["fuel_price_gas_STEPS_2050_high_price", "value"]))   # S4C-0 (decision 85): STEPS main
    assert registry.loc["fuel_price_lng_regasification_adder", "status"] == "REGISTERED" and registry.loc["fuel_price_lng_regasification_adder", "value"] == "1.26"   # M08a A4 (decision 131; former DATA_PENDING)


def built(sc):
    return (S31 / sc / f"{sc}_2920_3h_unsolved.nc").exists() and (S31 / sc / f"{sc}_BUILD_RECEIPT.json").exists()


@pytest.mark.skipif(not (built("integrated") and built("disconnected")), reason="S3-1 networks not built")
def test_s3_1_networks():
    import pypsa
    ex = pd.read_csv(GAS / "GAS_PIPELINES_EXISTING_CROSS_BORDER_2025.csv", keep_default_na=False)
    reg_cap = ex[ex.status == "REGISTERED"].set_index("pipeline").capacity_mw_ncv.astype(float)
    for sc in ["integrated", "disconnected"]:
        n = pypsa.Network(str(S31 / sc / f"{sc}_2920_3h_unsolved.nc"))
        g = n.generators
        assert not ((g.carrier == "gas") & (g.research_role == "EXTERNAL_SUPPLY")).any()   # unlimited per-node gas supply removed
        assert (g.carrier == "gas production").sum() > 0 and (g.carrier == "LNG import").sum() >= 6
        caps = n.meta["external_annual_caps"]
        prod = g[g.carrier == "gas production"]
        assert set(prod.index) <= set(caps) and all(caps[i] > 0 for i in prod.index)
        by_c = pd.Series({i: caps[i] for i in prod.index}).groupby(prod.country).sum()
        table = pd.read_csv(GAS / "GAS_PRODUCTION_CAPS_2050.csv").set_index("country").cap_mwh_per_year
        for c, v in by_c.items():
            assert v == pytest.approx(float(table[c]), rel=1e-6)
        L = n.links
        pipes = L[L.carrier == "gas pipeline"]
        xb = pipes[pipes.border_class == "cross_border"]
        if sc == "integrated":
            assert len(xb) >= 21 + 6   # 21 corridor candidates + 6 registered existing links
            for name, cap in reg_cap.items():
                row = pipes.loc[f"gas pipeline existing {name}"]
                assert row.p_nom_min == pytest.approx(cap) and row.p_nom == pytest.approx(cap) and row.p_nom_extendable
            assert pipes.loc["gas pipeline existing Trans Thailand–Malaysia Gas Pipeline (TTM)"].p_min_pu == -1.0
            assert pipes.loc["gas pipeline existing Yadana Gas Pipeline 1"].p_min_pu == 0.0
        else:
            assert len(xb) == 0 and n.meta["research_cross_border"]["switches"]["gas"] is False
        lng = g[g.carrier == "LNG import"]
        assert (lng.p_nom_max >= lng.p_nom).all() and ((lng.p_nom_max <= 2.5 * lng.p_nom + 1e-6) | (lng.p_nom == 0)).all()
        assert all(abs(float(v) - 13.6739681303) < 1e-6 for v in lng.marginal_cost)   # WEO NZE Japan LNG price, regasification adder 0 (DATA_PENDING)
        # every gas bus with a consumer has a supply path: a pipeline, production, LNG or biogas upgrading
        gas_buses = set(n.buses.index[n.buses.carrier == "gas"])
        supplied = set(L[L.bus1.isin(gas_buses)].bus1) | set(L[(L.carrier == "gas pipeline") & (L.p_min_pu < 0)].bus0) | set(g[g.bus.isin(gas_buses)].bus)
        consumers = set(L[L.bus0.isin(gas_buses)].bus0)
        assert consumers <= supplied
