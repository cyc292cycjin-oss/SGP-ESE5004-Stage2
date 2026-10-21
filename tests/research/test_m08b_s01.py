"""M08b supplement 01 (decision 137): review decisions D (GATES_V6 SHA choice), 8, 9, 11 and the registered limitations (no build, no solve)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
sys.path.insert(0, str(ROOT / "scripts_project" / "v5"))
import gates_v6 as g6   # noqa: E402

BR = dict(network=dict(sha256="a" * 64, snapshots=2920), daily_network=dict(sha256="d" * 64, snapshots=365))
DEM = ROOT / "research_inputs" / "demand_v5"
REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
COST = ROOT / "research_inputs" / "cost_layers_v5"
ASEAN = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def reg():
    return pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")


def rec(snapshots, truncated_to=None):
    return dict(input_network=dict(sha256="x" * 64, snapshots=snapshots, truncated_to=truncated_to))


def test_registered_sha_truncated_runs_take_the_2920_network():
    """item D: only an untruncated 365-snapshot run is checked against the 365x24h network; a truncated run of the 2920x3h file (56 snapshots,
    or a 365-snapshot probe) and a full 2920x3h run against the 2920x3h network of the build receipt."""
    assert g6.registered_sha_from_build_receipt(BR, rec(56, 56)) == "a" * 64            # M08b smoke: --truncate 56 on the 2920x3h file
    assert g6.registered_sha_from_build_receipt(BR, rec(365, 365)) == "a" * 64          # a 365-snapshot probe of the 2920x3h file
    assert g6.registered_sha_from_build_receipt(BR, rec(2920)) == "a" * 64
    assert g6.registered_sha_from_build_receipt(BR, rec(365)) == "d" * 64               # untruncated 365x24h run (level 2)
    assert g6.registered_sha_from_build_receipt(BR, rec(365, 0)) == "d" * 64            # --truncate 0 = no truncation
    assert g6.registered_sha_from_build_receipt(dict(network=BR["network"]), rec(365)) == "a" * 64   # receipt without a daily network
    assert g6.registered_sha_from_build_receipt(BR, None) == "a" * 64


def test_transport_electricity_counted_once(reg):
    """item 8: transport electricity rows (2019 rail / electric road x ATS growth) are in the base load; the transport fuel rows carry anchor - that
    electricity, and the land-transport EV / FCEV / ICE loads come only from non-electricity land-transport rows -> counted once, kept."""
    from s2_layers import LAND_TRANSPORT_ACCOUNTS, TABLE_BASE_SECTORS
    an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    t = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False); t["v"] = pd.to_numeric(t.value_2050_mwh, errors="coerce").fillna(0.0)
    tel = t[(t.sector == "Transport") & (t.carrier == "electricity")]
    assert "Transport" in TABLE_BASE_SECTORS and not set(tel.account) & LAND_TRANSPORT_ACCOUNTS
    for c in ASEAN:
        tc = t[(t.country == c) & (t.sector == "Transport")]
        el, fuel = float(tc[tc.carrier == "electricity"].v.sum()), float(tc[tc.carrier != "electricity"].v.sum())
        assert el == pytest.approx(an.at[c, "transport_elec_anchor_mwh"], rel=1e-9, abs=1e-6)
        assert fuel == pytest.approx(an.at[c, "transport_anchor_mwh"] - an.at[c, "transport_elec_anchor_mwh"], rel=1e-9, abs=1e-6)
    assert float(an.transport_elec_anchor_mwh.sum()) / 1e6 == pytest.approx(5.3, abs=0.1)
    assert reg.at["demand_transport_electricity_counted_once", "value"] == "counted_once"


def test_b11_completeness_retired(reg):
    """item 9: the S1-era completeness check is no longer run by the M08b static checks; registered with its reason; the supply-route check stays."""
    import m08b_static
    src = Path(m08b_static.__file__).read_text()
    assert "gate_b11_completeness(" not in src and "gate_b11_supply_routes(" in src and m08b_static.B11_RETIRED["retired"] is True
    r = reg.loc["gate_b11_completeness_retired"]
    assert r.value == "retired" and r.status == "REGISTERED" and "287" in r.description


def test_cost_layer_documentation_rows(reg):
    """item 11: no registry row cites the pre-M08a cost-layer files any more; rows citing the active layer carry its values (currency rows recomputed)."""
    now, old = COST / "technology_data_v0.15.0_EUR2020", COST / "technology_data_v0.15.0_EUR2020_ea20gdp"
    old_shas = {sha(old / "costs_2050_EUR2020.csv"), sha(old / "costs_2050_EUR2020_prepared.csv")}
    assert not reg.source_sha256.isin(old_shas).any()
    raw = pd.read_csv(now / "costs_2050_EUR2020.csv").drop_duplicates(["technology", "parameter"]).set_index(["technology", "parameter"]).value
    from m08b_data import s3_3_param_id
    td = {s3_3_param_id(tech, p): v for (tech, p), v in raw.items()}
    rows = reg[reg.source_sha256 == sha(now / "costs_2050_EUR2020.csv")]
    am = rows[rows.index.str.startswith("ammonia_methanol_td_")]
    assert len(am) == 28 and all(float(r.value) == pytest.approx(td[pid], rel=1e-11) for pid, r in am.iterrows())
    assert float(reg.at["gas_pipeline_cost_onshore", "value"]) == pytest.approx(raw[("CH4 (g) pipeline", "investment")], rel=1e-11)
    assert float(reg.at["gas_pipeline_cost_submarine", "value"]) == pytest.approx(raw[("CH4 (g) submarine pipeline", "investment")], rel=1e-11)
    assert f"investment {raw[('CH4 (g) pipeline', 'investment')]:.2f} EUR/MW/km" in reg.at["gas_pipeline_cost_onshore", "description"]
    assert float(reg.at["ammonia_methanol_td_haber-bosch_investment", "value"]) == pytest.approx(919.11643802, rel=1e-9)   # 962.87 x 0.795333 / 0.833196


def test_registered_limitations(reg):
    """items A, 5, 6, 12, C: registered as decided (no new technology, no new source)."""
    assert reg.at["industry_heat_hydrogen_not_represented", "value"] == "not_represented" and "UNDERESTIMATED" in reg.at["industry_heat_hydrogen_not_represented", "description"]
    assert reg.at["demand_transport_carrier_efficiency_assumption", "tier"] == "C"
    assert reg.at["industry_other_bucket_mechanical_fuel", "value"] == "fixed_oil" and reg.at["industry_other_bucket_mechanical_fuel", "tier"] == "C"
    assert reg.at["industry_heat_band_asean_distribution", "status"] == "DATA_PENDING" and "LCET-CN" in reg.at["industry_heat_band_asean_distribution", "description"]
    assert reg.at["network_builder_script", "value"] == "scripts_project/s2_network.py"
