"""S3B R2 (decision 67): other-bucket sensitivity research.s3.industry.other_bucket = idees_today."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
DEM = ROOT / "research_inputs" / "demand_v5"
REG = ROOT / "research_inputs" / "registry_v5"
OC = ["coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol"]


def test_ois_today_carrier_structure():
    t = pd.read_csv(REG / "INDUSTRY_OIS_TODAY_CARRIERS_EU27_2019.csv").set_index("carrier")
    assert t.share.sum() == pytest.approx(1.0, abs=1e-9) and t.ktoe_2019.sum() == pytest.approx(24263.3464708, rel=1e-9)   # IDEES OIS total row (fec[3])
    assert t.at["electricity", "share"] == pytest.approx(10058.33 / 24263.35, abs=1e-5) and t.at["oil", "share"] == pytest.approx(6889.22 / 24263.35, abs=1e-5)
    assert t.at["hydrogen", "share"] == 0 and t.at["ammonia", "share"] == 0
    leaf = pd.read_csv(REG / "INDUSTRY_OIS_TODAY_LEAF_ROWS_EU27_2019.csv")
    assert leaf.row.is_unique and leaf.ktoe_2019.sum() == pytest.approx(t.ktoe_2019.sum(), rel=1e-9)
    r = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["industry_other_bucket_mode", "value"] == "pypsa_eur_2050" and r.loc["industry_ois_today_share_electricity", "status"] == "SENSITIVITY"


def test_other_bucket_tables_and_switch():
    from phase4_static import config
    cfg = config(ROOT, "integrated")
    assert cfg["research"]["s3"]["industry"]["other_bucket"] == "useful_heat_bands"   # M08b B2 (decision 133): new main; pypsa_eur_2050 / idees_today stay selectable
    for mode in ["aeo8_ats_relative", "gdp", "population", "aeo8_ats_relative_level"]:
        main = pd.read_csv(DEM / f"INDUSTRY_2050_SUMMARY_{mode}.csv").set_index("country")
        today = pd.read_csv(DEM / f"INDUSTRY_2050_SUMMARY_{mode}_OTHER_IDEES_TODAY.csv").set_index("country")
        assert (DEM / f"INDUSTRY_2050_SUMMARY_{mode}_TD_SENSITIVITY_OTHER_IDEES_TODAY.csv").exists()
        assert list(main.index) == list(today.index) and (main.other_bucket == "pypsa_eur_2050").all() and (today.other_bucket == "idees_today").all()
        ob = pd.read_csv(DEM / "INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == mode].set_index("country")
        for c in main.index:
            # carriers without the biomass overflow / hydrogen clip: the difference equals the other-bucket difference (other sub-sectors, steel and cement unchanged)
            for oc in ["coal", "oil", "electricity", "heat", "ammonia", "methanol"]:
                d_tab = today.at[c, f"pe_{oc}_mwh"] - main.at[c, f"pe_{oc}_mwh"]
                d_ob = ob.at[c, f"other_2050_idees_today_{oc}_mwh"] - ob.at[c, f"other_2050_pypsa_eur_2050_{oc}_mwh"]
                assert d_tab == pytest.approx(d_ob, rel=1e-9, abs=1e-3)
            assert today.at[c, "pe_gas_mwh"] + today.at[c, "pe_biomass_mwh"] - main.at[c, "pe_gas_mwh"] - main.at[c, "pe_biomass_mwh"] == pytest.approx(
                ob.at[c, "other_2050_idees_today_gas_mwh"] + ob.at[c, "other_2050_idees_today_biomass_mwh"] - ob.at[c, "other_2050_pypsa_eur_2050_gas_mwh"] - ob.at[c, "other_2050_pypsa_eur_2050_biomass_mwh"], rel=1e-9, abs=1e-3)
    idx = ob.loc["ID"]
    assert idx.other_share_of_industry_2019 > 0.8 and idx.other_2019_coal_mwh / idx.other_2019_mwh > 0.3   # ID: the other bucket carries most of the industrial coal


def test_s2_layers_selects_other_bucket_table():
    import inspect
    import s2_layers
    src = inspect.getsource(s2_layers.add_demand_layer)
    assert "_OTHER_IDEES_TODAY.csv" in src and "other_bucket" in src
    from v5.v5_gates import gate_b12_hash
    assert "industry_other_bucket" in inspect.getsource(gate_b12_hash) and "demand_growth_method" in inspect.getsource(gate_b12_hash)
