"""M08a A5 / M08-4 (decision 131): CO2 storage unified to ERIA-GCCSI 2024 P50, annual cap = potential / 50 (no build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s2_layers import co2_storage_caps   # noqa: E402

REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
TABLE = ROOT / "research_inputs" / "co2_v5" / "CO2_STORAGE_POTENTIAL_UNIFIED.csv"


@pytest.fixture(scope="module")
def setup():
    from phase4_static import config
    cfg = config(ROOT, "integrated")
    reg = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    return cfg["research"]["s2"]["co2"], reg


def test_table_values():
    t = pd.read_csv(TABLE, keep_default_na=False).set_index("country")
    exp = {"VN": 5.30, "PH": 0.067, "MY": 128.8, "ID": 51.3, "BN": 18.6, "TH": 16.0}
    for c, v in exp.items():
        assert float(t.at[c, "potential_gt"]) == pytest.approx(v, abs=0.05 if v > 1 else 0.001), c
    assert float(t.at["KH", "potential_gt"]) == 0.09 and float(t.at["KH", "high_gt"]) == 45.0
    for c in ("TL", "LA", "MM", "SG"):
        assert float(t.at[c, "potential_gt"]) == 0.0
    assert t.at["LA", "status"] == "UNASSESSED" and t.at["MM", "status"] == "UNASSESSED" and t.at["SG", "status"] == "SOURCE_ZERO"


def test_annual_caps_vn_ph(setup):
    R, reg = setup
    assert R["storage_potential_source"] == "eria_gccsi_2024_unified" and R["storage_potential_case"] == "p50" and R["storage_years"] == 50
    caps, pots, info = co2_storage_caps(R, reg)
    assert caps["VN"] / 1e6 == pytest.approx(106.068, abs=1e-3)    # instruction: VN 106 Mt/a
    assert caps["PH"] / 1e6 == pytest.approx(1.344, abs=1e-6)      # instruction: PH 1.34 Mt/a
    assert caps["KH"] / 1e6 == pytest.approx(1.8) and caps["MY"] == pytest.approx(pots["MY"] * 1e9 / 50)
    assert all(caps[c] == 0 for c in ("TL", "LA", "MM", "SG"))
    assert info["status"]["LA"] == "UNASSESSED" and len(info["table_sha256"]) == 64
    R2 = dict(R, storage_years=25)   # the cap follows the configured horizon (no hard-coded /50)
    assert co2_storage_caps(R2, reg)[0]["VN"] == pytest.approx(2 * caps["VN"])


def test_cases_and_former_source(setup):
    R, reg = setup
    lo = co2_storage_caps(dict(R, storage_potential_case="low"), reg)[1]
    hi = co2_storage_caps(dict(R, storage_potential_case="high"), reg)[1]
    assert lo["VN"] == pytest.approx(3.3034) and hi["VN"] == pytest.approx(9.3034) and hi["KH"] == 45.0
    old_caps, old_pots, old = co2_storage_caps(dict(R, storage_potential_source="registry_d1"), reg)
    assert old_caps["VN"] == 236e6 and old_pots["PH"] == 22.3 and old["source"] == "registry_d1"
    with pytest.raises(ValueError):
        co2_storage_caps(dict(R, storage_potential_case="p90"), reg)


def test_registry_rows(setup):
    _, r = setup
    assert r.loc["co2_storage_unified_table", "value"] == "research_inputs/co2_v5/CO2_STORAGE_POTENTIAL_UNIFIED.csv"
    for c in ("LA", "MM"):
        assert r.loc[f"co2_storage_potential_unassessed_{c}", "value"] == "0" and r.loc[f"co2_storage_potential_unassessed_{c}", "status"] == "REGISTERED"
        assert "UNASSESSED" in r.loc[f"co2_storage_potential_{c}", "description"]
    assert "历史：已被 co2_injection_cap_unified_VN 替代" in r.loc["co2_injection_cap_VN", "description"]
    assert r.loc["co2_storage_potential_KH", "tier"] == "C" and r.loc["co2_storage_potential_VN", "tier"] == "B"
