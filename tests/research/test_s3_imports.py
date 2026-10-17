"""S3-2 (decisions 17/18/64): extra-ASEAN import prices and the built S3-2 networks (results_project/s3_2), solver-free."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5"
IMP = ROOT / "research_inputs" / "imports_v5"
S32 = ROOT / "results_project" / "s3_2"


@pytest.fixture(scope="module")
def registry():
    return pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")


def test_import_price_table(registry):
    p = pd.read_csv(IMP / "IMPORT_PRICES_2050.csv", keep_default_na=False).set_index("carrier")
    for carrier, esc in [("hydrogen", "shipping-lh2"), ("ammonia", "shipping-lnh3"), ("methanol", "shipping-meoh"), ("oil non-fossil", "shipping-ftfuel")]:
        r = p.loc[carrier]
        assert r.esc == esc and r.status == "REGISTERED" and str(r.year) == "2040" and r.scenario == "default"
        assert float(r.applied_eur2020_per_mwh) == pytest.approx(float(r.base_eur2020_per_mwh) * 1.2, rel=1e-6)
        assert float(r.sensitivity_low) == pytest.approx(float(r.applied_eur2020_per_mwh) * 0.8, rel=1e-6) and float(r.sensitivity_high) == pytest.approx(float(r.applied_eur2020_per_mwh) * 1.2, rel=1e-6)
    assert float(p.loc["oil non-fossil"].base_eur2020_per_mwh) == pytest.approx(125.0911, abs=1e-3)   # published text: Fischer-Tropsch 125-132 EUR/MWh (Chile)
    assert float(p.loc["hydrogen"].base_eur2020_per_mwh) == pytest.approx(88.1275, abs=1e-3)
    assert float(p.loc["ammonia"].base_eur2020_per_mwh) < float(p.loc["methanol"].base_eur2020_per_mwh) < float(p.loc["oil non-fossil"].base_eur2020_per_mwh)   # methanol slightly cheaper than FT
    assert float(registry.loc["import_price_oil_non_fossil", "value"]) == pytest.approx(float(p.loc["oil non-fossil"].applied_eur2020_per_mwh), rel=1e-6)
    assert registry.loc["import_price_oil_non_fossil", "sensitivity_low"] != "" and registry.loc["import_price_base_hydrogen", "tier"] == "B"
    assert float(registry.loc["import_price_markup", "value"]) == 0.2 and registry.loc["import_carbon_treatment", "decision_ref"] == "64"
    f = pd.read_csv(IMP / "IMPORT_PRICES_FOSSIL_2050.csv").set_index("carrier")
    # S4C-0 (decision 85): the reference table lists the STEPS main prices
    assert float(f.loc["oil"].price_eur2020_per_mwh) == pytest.approx(35.3179141049) and float(f.loc["gas (LNG)"].price_eur2020_per_mwh) == pytest.approx(27.0688756865)


def built(sc):
    return (S32 / sc / f"{sc}_2920_3h_unsolved.nc").exists() and (S32 / sc / f"{sc}_BUILD_RECEIPT.json").exists()


@pytest.mark.skipif(not (built("integrated") and built("disconnected")), reason="S3-2 networks not built")
def test_s3_2_networks():
    import pypsa
    p = pd.read_csv(IMP / "IMPORT_PRICES_2050.csv", keep_default_na=False).set_index("carrier")
    for sc in ["integrated", "disconnected"]:
        n = pypsa.Network(str(S32 / sc / f"{sc}_2920_3h_unsolved.nc"))
        g = n.generators; L = n.links
        # oil: one regional pool, per-node external oil removed, every node oil bus joined bidirectionally
        assert not ((g.carrier == "oil") & (g.research_role == "EXTERNAL_SUPPLY")).any()
        assert n.buses.at["ASEAN oil", "country"] == "ASEAN" and g.at["ASEAN oil import", "marginal_cost"] == pytest.approx(11.6177349029)
        pool = L[L.carrier == "oil pool"]
        assert len(pool) == 100 and (pool.p_min_pu == -1.0).all() and (pool.bus1 == "ASEAN oil").all() and (pool.border_class == "domestic").all()
        # coal per node unchanged
        assert ((g.carrier == "coal") & (g.research_role == "EXTERNAL_SUPPLY")).sum() == 100
        # green carriers: regional buses, import generators at base x 1.2, no CO2 port, imports only (generators)
        for carrier, bus, gen in [("ammonia", "ASEAN ammonia", "ASEAN ammonia import"), ("methanol", "ASEAN methanol", "ASEAN methanol import"), ("oil non-fossil", "ASEAN oil non-fossil", "ASEAN oil non-fossil import")]:
            assert n.buses.at[bus, "country"] == "ASEAN" and g.at[gen, "bus"] == bus and g.at[gen, "p_nom_extendable"]
            assert g.at[gen, "marginal_cost"] == pytest.approx(float(p.loc[carrier].applied_eur2020_per_mwh), rel=1e-6)
        assert float(n.carriers.loc[["ammonia import", "methanol import", "FT fuel import", "H2 import", "oil import"], "co2_emissions"].abs().sum()) == 0.0
        # liquid hydrogen at LNG terminal nodes only, capped by the LNG terminal capacity, terminal capital cost
        h2 = g[g.carrier == "H2 import"]; lng = g[g.carrier == "LNG import"]
        assert len(h2) == len(lng[lng.p_nom_max > 0]) and all(abs(float(v) - 7018.0 * 1.2) < 1e-6 for v in h2.capital_cost)
        for name, z in h2.iterrows():
            node = str(z.bus)[:-3]
            assert z.p_nom_max == pytest.approx(float(lng.at[f"{node} LNG import", "p_nom_max"]))
            assert z.marginal_cost == pytest.approx(float(p.loc["hydrogen"].applied_eur2020_per_mwh), rel=1e-6)
        # same prices in both scenarios (config identical apart from the switches): checked by the shared table; no export links from the pools
        assert not L[(L.bus0.isin(["ASEAN ammonia", "ASEAN methanol", "ASEAN oil non-fossil"])) & (L.carrier != "oil pool")].index.tolist()
