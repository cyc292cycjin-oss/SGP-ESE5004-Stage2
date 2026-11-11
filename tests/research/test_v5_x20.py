"""V5 X20 (decisions 241, 244, 246): unit tests of the v5 switch set and build layers on toy networks (no solve, no large inputs)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
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


# ---- 2-5 lifetime boundary and geothermal 40 a (decisions 244, 246 Q2 (b)) -------------------------------------------------------
S1_JSON = ROOT / "research/06_scope_redesign/p1_step1_20261015/evidence/S1_SELECTED_ASSET_SURVIVAL_2050.json"
FV = ROOT / "research_inputs/fleet_v5"
EB = ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"


def test_in_service_rule():
    assert V.in_service(2010, 40, "inclusive") and not V.in_service(2010, 40, "strict")
    assert V.in_service(2011, 40, "strict") and not V.in_service(2009, 40, "inclusive") and not V.in_service(2051, 40, "inclusive")
    with pytest.raises(ValueError):
        V.in_service(2010, 40, "loose")


def test_s1_geothermal_rule_and_unit_table():
    import json
    from s2_layers import geothermal_unit_table
    S = json.loads(S1_JSON.read_text())
    surv = {r["AssetID"] for r in S["unit_evidence"]["records"] if r.get("Technology") == "Geothermal" and r["SurvivalStatus"] == "SURVIVES_2050"}
    r30 = V.s1_geothermal_in_service(S1_JSON, "strict", 30)
    assert {r["AssetID"] for r in r30} == surv and abs(sum(float(r["OriginalCapacity"]) for r in r30) - 186.0) < 1e-9
    r40 = V.s1_geothermal_in_service(S1_JSON, "inclusive", 40)
    by_c = {}
    for r in r40:
        by_c[r["Country"]] = by_c.get(r["Country"], 0.0) + float(r["OriginalCapacity"])
    assert len(r40) == 20 and abs(by_c["ID"] - 1051.0) < 1e-9 and abs(by_c["PH"] - 72.0) < 1e-9
    t4, t30 = geothermal_unit_table(S1_JSON), geothermal_unit_table(S1_JSON, ("strict", 30))
    assert t4.equals(t30) and abs(t4[t4.in_service_2050].OriginalCapacity.astype(float).sum() - 186.0) < 1e-9   # strict / 30 a = the v4 table
    t40 = geothermal_unit_table(S1_JSON, ("inclusive", 40))
    live = t40[t40.in_service_2050]
    assert set(live.AssetID) == {r["AssetID"] for r in r40} and (live.Lifetime == 40.0).all()
    assert (live.RetirementYear.astype(float) == live.CommissioningYear.astype(float) + 40).all()


def test_v5_fleet_additions_no_double_count():
    """Q2 (b): the GEM path excludes the S1 geothermal records of the S2 path and every frozen-stock identity; the 8 S1 boundary units
    (RetirementYear 2050, 2,503.1 MW) enter through the GEM table only (7 units, 1,833.1 MW) or not at all (North Bangkok 1, GIPT mothballed)."""
    import json
    a5 = pd.read_csv(FV / "FLEET_ADDITIONS_2050_V5.csv", dtype={"gem_unit_id": str})
    geo40 = {str(r["AssetID"]).replace("GEM:", "") for r in V.s1_geothermal_in_service(S1_JSON, "inclusive", 40)}
    assert not set(a5.gem_unit_id) & geo40
    S = json.loads(S1_JSON.read_text())
    bnd = [r for r in S["unit_evidence"]["records"] if str(r.get("RetirementYear"))[:4] == "2050" and r.get("Technology") != "Geothermal"]
    assert len(bnd) == 8 and abs(sum(float(r["OriginalCapacity"]) for r in bnd) - 2503.1) < 1e-9
    ids = {str(r["AssetID"]).replace("GEM:", "") for r in bnd}
    inside = ids & set(a5.gem_unit_id)
    assert ids - inside == {"G100000404448"} and abs(a5[a5.gem_unit_id.isin(inside)].capacity_mw.sum() - 1833.1) < 1e-9
    ev = json.loads((FV / "FLEET_S4A_EVIDENCE_V5.json").read_text())["v5_x20"]
    assert ev["boundary"] == "inclusive" and ev["geothermal_lifetime"] == 40 and set(ev["s1_geothermal_s2_path"]["units"]) == geo40
    if EB.exists():
        import netCDF4
        ds = netCDF4.Dataset(EB); frozen = json.loads(ds.getncattr("meta"))["existing_unit_components"]; ds.close()
        assert not {f"GEM:{g}" for g in a5.gem_unit_id} & set(frozen) and not {f"GEM:{g}" for g in ids} & set(frozen)
