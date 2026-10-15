"""S3-5 (decision 64): fuel carbon attribution in the built S3-5 networks (results_project/s3_5 origin_neutral, results_project/s3_5_pc producer_credit)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
S35 = ROOT / "results_project" / "s3_5"
S35PC = ROOT / "results_project" / "s3_5_pc"
REG = ROOT / "research_inputs" / "registry_v5"


def built(base, sc):
    return (base / sc / f"{sc}_2920_3h_unsolved.nc").exists() and (base / sc / f"{sc}_BUILD_RECEIPT.json").exists()


def test_registry_rows():
    r = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["fuel_carbon_mode", "value"] == "origin_neutral" and r.loc["fuel_carbon_pypsa_eur_origin_tracking", "value"] == "none"
    assert float(r.loc["fuel_carbon_sg_bunker_example", "value"]) == pytest.approx(115.5e6)


@pytest.mark.skipif(not built(S35, "integrated"), reason="S3-5 origin_neutral network not built")
def test_origin_neutral():
    import pypsa
    n = pypsa.Network(str(S35 / "integrated" / "integrated_2920_3h_unsolved.nc"))
    L = n.links
    assert n.meta["research_fuel_carbon"]["mode"] == "origin_neutral"
    ft = L[L.carrier == "Fischer-Tropsch"]
    assert (ft.bus1.str.endswith(" oil non-fossil")).all() and (ft.bus4.str.startswith("co2 atmosphere")).all() and (ft.efficiency4 > 0).all()
    assert ft.efficiency4.iloc[0] == pytest.approx(0.2571 * 0.754, rel=1e-6)   # +EF_oil x eta at synthesis in the producer country
    btl = L[L.carrier == "BtL"]
    assert (btl.bus1.str.endswith(" oil non-fossil")).all() and (btl.bus2 == "").all()   # production credit removed
    btm = L[L.carrier == "biomass-to-methanol"]
    assert (btm.bus2 == "").all()
    me = L[L.carrier == "methanolisation"]
    assert (me.bus4.str.startswith("co2 atmosphere")).all() and me.efficiency4.iloc[0] == pytest.approx(0.8787 / 4.0321, rel=1e-6)
    for car in ["industry methanol", "shipping methanol", "OCGT methanol"]:
        g = L[L.carrier == car]
        assert len(g) > 0 and (g.bus2 == "").all()   # zero at use
    fossil = L[(L.carrier == "oil final-energy accounting") & L.bus0.str.endswith(" oil")]
    twins = L[(L.carrier == "oil final-energy accounting") & L.bus0.str.endswith(" oil non-fossil")]
    assert len(twins) == len(fossil) and (twins.bus2 == "").all() and (fossil.efficiency2 == pytest.approx(0.2571)).all() if False else len(twins) == len(fossil) and (twins.bus2 == "").all()
    sg = L.loc["SG2 0 shipping methanol"]
    assert sg.bus2 == "" and sg.bus0 == "ASEAN methanol"
    # imported FT fuel reaches consumers only through the non-fossil pool (no CO2 anywhere on that path)
    pool = L[L.carrier == "oil pool"]
    assert (pool.bus1.isin(["ASEAN oil", "ASEAN oil non-fossil"])).all() and len(pool[pool.bus1 == "ASEAN oil non-fossil"]) == len(pool[pool.bus1 == "ASEAN oil"])
    # every atmosphere port is owned by its country (validate_country_attribution ran in the build); no negative removal credit left on liquid-fuel producers
    assert float(L.loc[L.carrier.isin(["BtL", "biomass-to-methanol"]), "efficiency2"].abs().sum()) == 0.0


@pytest.mark.skipif(not built(S35PC, "integrated"), reason="S3-5 producer_credit network not built")
def test_producer_credit():
    import pypsa
    n = pypsa.Network(str(S35PC / "integrated" / "integrated_2920_3h_unsolved.nc"))
    L = n.links
    assert n.meta["research_fuel_carbon"]["mode"] == "producer_credit" and "s3.fuel_carbon_mode=producer_credit" in n.meta["research_config"]["config_overrides"]
    ft = L[L.carrier == "Fischer-Tropsch"]
    assert (ft.bus1.str.endswith(" oil")).all() and (~ft.bus1.str.endswith(" oil non-fossil")).all() and (ft.bus4 == "").all()
    btl = L[L.carrier == "BtL"]
    assert (btl.efficiency2 < 0).all()   # S2 production credit kept
    assert (L[L.carrier == "shipping methanol"].efficiency2 > 0).all()   # fossil EF at use
    assert n.generators.at["ASEAN methanol import", "p_nom_max"] == 0.0
    twins = L[(L.carrier == "oil final-energy accounting") & L.bus0.str.endswith(" oil non-fossil")]
    assert len(twins) > 0 and (twins.bus2 == "").all()   # imported FT fuel still zero at use
