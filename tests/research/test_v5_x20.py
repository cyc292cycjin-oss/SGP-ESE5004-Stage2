"""V5 X20 (decisions 241, 244, 246): unit tests of the v5 switch set and build layers on toy networks (no solve, no large inputs)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))

import v5_common as V   # noqa: E402


def cfg(v5=None, v4=True):
    return {"research": {"demand": {"v4": {"enabled": v4}, "v5": dict(v5 or {})}}}


def test_switches_off_and_main():
    assert V.switches(cfg()) == V.V5_OFF and not V.is_main_set(V.V5_OFF)
    s = V.switches(cfg({"enabled": True}))
    assert s == V.V5_MAIN and V.is_main_set(s)
    assert V.switches(cfg({"enabled": False, "gas_cap_rule": "nonsense"})) == V.V5_OFF   # keys ignored while disabled
    with pytest.raises(ValueError):
        V.switches(cfg({"enabled": True}, v4=False))
    with pytest.raises(ValueError):
        V.switches(cfg({"enabled": True, "gas_cap_rule": "nonsense"}))
    with pytest.raises(ValueError):
        V.switches(cfg({"enabled": True, "solar_cap_scale_MY": 3.0}))
    with pytest.raises(ValueError):
        V.switches(cfg({"enabled": True, "unknown_key": 1}))
    assert V.switch_sha(V.V5_OFF) != V.switch_sha(V.V5_MAIN)
    assert not V.is_main_set(V.switches(cfg({"enabled": True, "offwind_asean_premium_pct": 20.0})))


def test_baseline_config_v5_off():
    import yaml
    b = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
    v5 = b["research"]["demand"]["v5"]
    assert v5["enabled"] is False
    assert set(v5) == set(V.V5_MAIN)
    assert {k: v5[k] for k in V.V5_MAIN if k != "enabled"} == {k: v for k, v in V.V5_MAIN.items() if k != "enabled"}   # listed values = the v5 main set
    assert V.switches(b) == V.V5_OFF


def test_v4_table_identity():
    import v4_common as C
    s4 = C.switches({"research": {"demand": {"v4": {"enabled": True}}}})
    assert not C.v5_table_keys(s4) and C.out_name(s4) == "out_ras"
    s4b = C.switches({"research": {"demand": {"v4": {"enabled": True}, "v5": {"enabled": False}}}})
    assert s4b == s4 and C.switch_sha(s4b) == C.switch_sha(s4)   # v5 disabled: v4 folder identity of 26c2e47d
    s5 = C.switches({"research": {"demand": {"v4": {"enabled": True}, "v5": {"enabled": True}}}})
    assert s5["v5_neu_gas_growth"] == "product" and s5["v5_biomass_residue_fix"] == "corrected"
    assert C.out_name(s5) == "out_ras_v5" and C.is_v5_main_tables(s5) and not C.is_main_set(s5)
    s5b = C.switches({"research": {"demand": {"v4": {"enabled": True}, "v5": {"enabled": True, "neu_gas_growth": "industry_multiplier"}}}})
    assert C.out_name(s5b).startswith("out_ras_") and C.out_name(s5b) != "out_ras_v5"
    s5c = C.switches({"research": {"demand": {"v4": {"enabled": True}, "v5": {"enabled": True, "offwind_asean_premium_pct": 20.0}}}})
    assert C.out_name(s5c) == "out_ras_v5"   # a network-only v5 key leaves the table folder unchanged
    assert C.switches(None, {**C.V4_MAIN, "v5_neu_gas_growth": "product", "v5_biomass_residue_fix": "corrected"}) == s5   # v4_industry.py --set route
    with pytest.raises(ValueError):
        C.switches(None, {**C.V4_MAIN, "v5_neu_gas_growth": "product"})   # all table-level v5 keys or none
    with pytest.raises(ValueError):
        C.switches(None, {**C.V4_MAIN, "v5_neu_gas_growth": "x", "v5_biomass_residue_fix": "corrected"})
    with pytest.raises(ValueError):
        C.switches({"research": {"demand": {"v4": {"enabled": False}, "v5": {"enabled": True}}}})


def test_network_meta_record_and_check():
    class N:
        meta: dict = {}
    n = N(); n.meta = {}
    c_on, c_off = cfg({"enabled": True}), cfg()
    assert V.check_network_meta_v5(n.meta, c_off) == dict(enabled=False)
    with pytest.raises(ValueError):
        V.check_network_meta_v5(n.meta, c_on)
    rec = V.record(n, V.switches(c_on), {}, {"layer": {"x": 1}})
    assert rec["switch_sha256"] == V.switch_sha(V.V5_MAIN) and rec["main_set"] and n.meta["v5_x20"] is rec
    assert V.check_network_meta_v5(n.meta, c_on)["main_set"]
    with pytest.raises(ValueError):
        V.check_network_meta_v5(n.meta, c_off)
    with pytest.raises(ValueError):
        V.check_network_meta_v5(n.meta, cfg({"enabled": True, "offwind_asean_premium_pct": 10.0}))
