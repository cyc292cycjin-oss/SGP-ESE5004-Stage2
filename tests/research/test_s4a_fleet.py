"""S4A-2 (L15): GEM fleet additions and GEM gas-field node allocation - data tables, config defaults and the built network."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
FV = ROOT / "research_inputs/fleet_v5"
NET = ROOT / "results_project/s4a/build_check_s4a2/integrated/integrated_2920_3h_unsolved.nc"
CLASSES = {"coal existing", "lignite existing", "oil existing", "CCGT existing", "OCGT existing", "geothermal existing", "hydro existing", "ror existing", "PHS existing",
           "solar existing", "onwind existing", "offwind existing", "waste existing"}


def test_additions_table_consistent():
    add = pd.read_csv(FV / "FLEET_ADDITIONS_2050.csv")
    assert add.gem_unit_id.is_unique and len(add) == 299
    assert add.start_year.notna().all() and (add.start_year <= 2050).all()          # no start year -> UNRESOLVED list, never added
    assert (add.retire_year == add.start_year + add.lifetime).all() and (add.retire_year > 2050).all()   # S1 lifetime rule
    assert add.Status.isin(["operating", "construction"]).all()
    assert set(add.model_class) <= CLASSES and (add.capacity_mw > 0).all()
    assert add.node.notna().all() and add.node.str[:2].eq(add.country).all()          # nearest node of the same country
    assert (add.node_distance_km < 1500).all()
    ev = json.loads((FV / "FLEET_S4A_EVIDENCE.json").read_text())
    by_cls = add.groupby("model_class").capacity_mw.sum().round(1).to_dict()
    assert by_cls == {k: round(v, 1) for k, v in ev["additions_by_class"].items()}
    assert ev["include_construction"] is True


def test_coverage_and_unresolved_tables():
    cov = pd.read_csv(FV / "FLEET_COVERAGE_GEM_2026_BY_COUNTRY_TYPE.csv")
    assert (cov.survives_2050_missing_mw <= cov.survives_2050_mw + 1e-6).all()
    assert (cov.matched_in_network_mw <= cov.gem_operating_mw + cov.gem_construction_mw + 1e-6).all()
    add = pd.read_csv(FV / "FLEET_ADDITIONS_2050.csv"); unres = pd.read_csv(FV / "FLEET_UNRESOLVED_START_YEAR.csv")
    assert not set(add.gem_unit_id) & set(unres["GEM unit/phase ID"])                  # unresolved units are not added
    assert abs(cov.survives_2050_missing_mw.sum() - add.capacity_mw.sum()) < 1.0
    shares = pd.read_csv(FV / "GAS_PRODUCTION_NODE_SHARES_GEM.csv")
    s = shares.groupby("country").share_in_country.sum(); assert np.allclose(s.values, 1.0)
    gc = pd.read_csv(FV / "GAS_FIELD_COVERAGE_VS_UNSD.csv")
    assert set(gc.country[gc.allocation == "gem_fields"]) == set(shares.country)


def test_config_defaults():
    from phase4_static import config
    cfg = config(ROOT, "integrated")["research"]
    assert cfg["fleet"]["gem_additions"] is True and cfg["fleet"]["include_construction"] is True
    assert cfg["s3"]["gas"]["production_node_allocation"] == "gem_fields"


@pytest.mark.skipif(not NET.exists(), reason="S4A-2 build check network not present")
def test_built_network_fleet_and_gas_allocation():
    import pypsa
    n = pypsa.Network(str(NET)); m = n.meta; f = m["research_fleet"]
    add = pd.read_csv(FV / "FLEET_ADDITIONS_2050.csv")
    assert f["summary"]["mw"] + f["summary"]["skipped_mw"] == pytest.approx(float(add.capacity_mw.sum()), abs=0.5)
    assert all(s["cls"] == "waste existing" for s in f["skipped"])
    ids = m["existing_unit_components"]; s4a = {k: v for k, v in ids.items() if v.get("s4a_added")}   # one identity per GEM unit, aggregated into (node, class) components
    kept = add[add.model_class != "waste existing"]
    assert set(s4a) == set("GEM:" + kept.gem_unit_id) and all(v["component"].endswith("::S4A") for v in s4a.values())
    assert len({v["component"] for v in s4a.values()}) == f["summary"]["components"]
    L = n.links; eff = (L.p_nom * L.efficiency)[L.index.str.contains("::S4A")]
    for cls in ["CCGT existing", "coal existing"]:
        assert eff[L.carrier[eff.index] == cls].sum() == pytest.approx(float(add.capacity_mw[add.model_class == cls].sum()), rel=1e-6)
    gp = m["research_gas_network"]["production"]
    assert m["research_gas_network"]["production_node_allocation"] == "gem_fields"
    assert {c for c, v in gp.items() if v.get("allocation") == "gem_fields"} == {"BN", "ID", "MM", "MY", "PH", "TH", "VN"}
    assert gp["TL"]["allocation"].startswith("load_shares")
    for c, v in gp.items():
        if v.get("shares"):
            assert sum(v["shares"].values()) == pytest.approx(1.0, abs=1e-9)
