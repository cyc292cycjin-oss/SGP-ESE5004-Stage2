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


# ---- 2-6 checked coordinates of approximate GEM points (decision 244) --------------------------------------------------------------
def test_gem_coord_table_and_override():
    import v5_layers as L
    t = pd.read_csv(ROOT / L.GEM_COORD_TABLE, dtype={"gem_unit_id": str})
    assert len(t) == 5 and t.gem_unit_id.is_unique and set(t.grade) <= {"A", "B", "C"} and t.source.str.startswith("https://").all()
    assert t.loc[t.node_changes, "gem_unit_id"].tolist() == ["G100001090630"]                      # only Truong Son 2: LA2 1 -> LA2 3
    tabs = pd.concat([pd.read_csv(FV / f, dtype={"gem_unit_id": str}) for f in ("FLEET_ADDITIONS_2050_V5.csv", "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv")])
    node = tabs.set_index("gem_unit_id").node
    assert all(node[r.gem_unit_id] == r.gem_node for r in t.itertuples())                         # the GEM node is the node of the addition tables
    df = pd.DataFrame(dict(gem_unit_id=["G100001090630", "X"], node=["LA2 1", "LA2 1"], capacity_mw=[350.0, 10.0]))
    out, moved = L.gem_node_override(df, cfg({"enabled": True}), ROOT)
    assert out.loc[0, "node"] == "LA2 3" and out.loc[1, "node"] == "LA2 1" and moved == [dict(gem_unit_id="G100001090630", plant="Truong Son wind farm", mw=350.0, node_from="LA2 1", node_to="LA2 3")]
    assert df.loc[0, "node"] == "LA2 1"                                                            # input frame unchanged
    assert L.gem_node_override(df, cfg(), ROOT) == (df, []) and L.gem_node_override(df, cfg({"enabled": True, "gem_coord_fix": "gem"}), ROOT)[1] == []
    with pytest.raises(ValueError):
        L.gem_node_override(df.assign(node="LA2 2"), cfg({"enabled": True}), ROOT)
    with pytest.raises(ValueError):
        L.gem_node_override(df.iloc[1:], cfg({"enabled": True}), ROOT)


# ---- 1-1 GWA v4 correction fields (decisions 241, 246 Q1 (b)) ------------------------------------------------------------------
def test_wind_gwa_factor_files():
    import json
    import numpy as np
    import xarray as xr
    rv = ROOT / "research_inputs/renewable_v5"
    f = xr.open_dataarray(rv / "WIND_GWA_CELL_FACTOR_V5.nc")
    t = pd.read_csv(rv / "WIND_GWA_CELL_FACTOR_V5.csv")
    log = json.loads((rv / "WIND_GWA_V5_LOG.json").read_text())
    v = f.values
    assert v.shape == (f.sizes["y"], f.sizes["x"]) and np.isfinite(v).all() and v.min() >= 0.5 and v.max() <= 3.0
    used = t[t.used]
    assert len(used) == log["cells_used"] == 4048 and int(t.clipped.sum()) == log["cells_clipped"] == 1 and (used.coverage >= 0.5).all()
    assert np.allclose(v[used.iy.values, used.ix.values], used.factor.values, rtol=0, atol=1e-9)
    mask = np.ones_like(v, dtype=bool); mask[used.iy.values, used.ix.values] = False
    assert (v[mask] == 1.0).all()                                                                  # unused cells carry factor 1
    pf = pd.read_csv(rv / "WIND_GWA_FARM_POINT_FACTOR_V5.csv")
    assert len(pf) == 156 and pf.factor_point.notna().all() and pf.factor_point.between(0.5, 3.0).all()
    assert np.allclose(pf.factor_point_raw.clip(0.5, 3.0), pf.factor_point)
    for k, o in log["outputs"].items():
        assert V.sha256(rv / k) == o["sha256"]


# ---- toy network helpers -----------------------------------------------------------------------------------------------------
def toy(nodes=("A 0", "A 1"), country="MY"):
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=4, freq="3h"))
    for b in nodes:
        n.add("Bus", b, carrier="AC", v_nom=380.0, x=100.0, y=3.0)
        n.add("Bus", b + " low voltage", carrier="low voltage", v_nom=0.4)
    n.buses["country"] = country   # research networks carry buses.country (not a PyPSA standard attribute)
    return n


# ---- 1-3 ASEAN offshore-wind premium (decision 241) ---------------------------------------------------------------------------
def test_offwind_premium():
    import v5_layers as L
    n = toy()
    n.add("Generator", "A 0 offwind-dc-2025 c2", bus="A 0", carrier="offwind-dc", p_nom_extendable=True, capital_cost=100.0)
    n.add("Generator", "A 0 offwind-float-2025", bus="A 0", carrier="offwind-float", p_nom_extendable=True, capital_cost=200.0)
    n.add("Generator", "existing_survivor::A 0::offwind existing::S4A", bus="A 0", carrier="offwind existing", p_nom=50.0, capital_cost=0.0)
    n.add("Generator", "A 0 onwind-2025", bus="A 0", carrier="onwind", p_nom_extendable=True, capital_cost=80.0)
    before = n.generators.capital_cost.copy()
    assert L.apply_offwind_premium(n, cfg({"enabled": True}))["generators"] == 0 and n.generators.capital_cost.equals(before)   # 0 % main: unchanged
    assert L.apply_offwind_premium(n, cfg({"offwind_asean_premium_pct": 20.0}))["generators"] == 0 and n.generators.capital_cost.equals(before)   # v5 off
    led = L.apply_offwind_premium(n, cfg({"enabled": True, "offwind_asean_premium_pct": 10.0}))
    c = n.generators.capital_cost
    assert led["generators"] == 2 and abs(c["A 0 offwind-dc-2025 c2"] - 110.0) < 1e-12 and abs(c["A 0 offwind-float-2025"] - 220.0) < 1e-12
    assert c["A 0 onwind-2025"] == 80.0 and c["existing_survivor::A 0::offwind existing::S4A"] == 0.0


# ---- 1-4 solar cap factors and the MY land-use variants (decision 241, Q15 (a)) ------------------------------------------------------
def test_solar_my_variants_table():
    import v5_layers as L
    t = pd.read_csv(ROOT / L.SOLAR_MY_VARIANTS).set_index("variant")
    assert list(t.index) == ["lc100", "open_forest", "oil_palm"] and t.at["lc100", "factor"] == 1.0
    assert abs(t.at["lc100", "cap_before_mw"] - 86396.0293) < 1e-3                                   # = the W14 MY ground-mounted solar cap
    assert abs(t.at["open_forest", "factor"] - 198.0 / 86.4) < 1e-12                                  # X20_SPEC 1.4 item 3
    assert abs(t.at["oil_palm", "added_area_km2"] - 51700.4) < 0.1 and abs(t.at["oil_palm", "factor"] - (1 + 51700.4146 * 5.1 / 86396.0293)) < 1e-6


def test_solar_cap_scale_layer():
    import v5_layers as L
    n = toy(("A 0", "B 0"))
    n.buses.loc["B 0", "country"] = "ID"
    n.add("Generator", "A 0 solar-2025", bus="A 0", carrier="solar", p_nom_extendable=True, p_nom_max=10.0)
    n.add("Generator", "B 0 solar-2025", bus="B 0", carrier="solar", p_nom_extendable=True, p_nom_max=7.0)
    n.add("Generator", "A 0 solar rooftop-2025", bus="A 0 low voltage", carrier="solar rooftop", p_nom_extendable=True, p_nom_max=3.0)
    n.add("Generator", "existing_survivor::A 0::solar existing::S4A", bus="A 0", carrier="solar existing", p_nom=2.0, p_nom_max=2.0)
    before = n.generators.p_nom_max.copy()
    assert "by_country" not in L.apply_solar_cap_scale(n, cfg({"solar_cap_scale_MY": 2.0}), ROOT) and n.generators.p_nom_max.equals(before)   # v5 off
    assert L.apply_solar_cap_scale(n, cfg({"enabled": True}), ROOT)["by_country"] == {} and n.generators.p_nom_max.equals(before)             # main: unchanged
    led = L.apply_solar_cap_scale(n, cfg({"enabled": True, "solar_cap_scale_MY": 2.0, "solar_cap_scale_ID": 0.5}), ROOT)
    p = n.generators.p_nom_max
    assert p["A 0 solar-2025"] == 20.0 and p["B 0 solar-2025"] == 3.5 and p["A 0 solar rooftop-2025"] == 3.0 and p["existing_survivor::A 0::solar existing::S4A"] == 2.0
    assert set(led["by_country"]) == {"MY", "ID"}
    n2 = toy(); n2.add("Generator", "A 0 solar-2025", bus="A 0", carrier="solar", p_nom_extendable=True, p_nom_max=10.0)
    led2 = L.apply_solar_cap_scale(n2, cfg({"enabled": True, "solar_landuse_my": "oil_palm"}), ROOT)
    t = pd.read_csv(ROOT / L.SOLAR_MY_VARIANTS).set_index("variant")
    assert abs(n2.generators.at["A 0 solar-2025", "p_nom_max"] - 10.0 * t.at["oil_palm", "factor"]) < 1e-9 and led2["variant_factor"] == t.at["oil_palm", "factor"]


# ---- 1-5 hydro inflow on the operating stock, multiplier, spill report (decision 241, Q14) ------------------------------------------
def _hydro_net():
    n = toy(("A 0",))
    n.add("StorageUnit", "h_op", bus="A 0", carrier="hydro existing", p_nom=60.0, max_hours=10.0)
    n.add("StorageUnit", "h_con", bus="A 0", carrier="hydro existing", p_nom=40.0, max_hours=10.0)
    n.storage_units["country"] = "MY"; n.generators["country"] = pd.Series(dtype=str)
    n.storage_units_t.inflow = pd.DataFrame({"h_op": [30.0] * 4, "h_con": [10.0] * 4}, index=n.snapshots)
    n.meta = {"existing_unit_components": {"GEM:a": dict(component="h_op", capacity_mw=60.0, gem_status="operating", commissioning_year=2010),
                                           "GEM:b": dict(component="h_con", capacity_mw=40.0, gem_status="construction", commissioning_year=2027)}}
    return n


def test_operating_share():
    import v5_layers as L
    n = _hydro_net()
    assert L.operating_share(n, "h_op", 60.0)[0] == 1.0 and L.operating_share(n, "h_con", 40.0)[0] == 0.0 and L.operating_share(n, "x", 5.0) == (1.0, "no identity: operating")
    n.meta["existing_unit_components"]["AUTH:c"] = dict(component="h_op", capacity_mw=20.0)   # author unit without GEM status: operating
    n.meta["existing_unit_components"]["GEM:d"] = dict(component="h_op", capacity_mw=20.0, gem_status="operating", commissioning_year=2026)
    assert L.operating_share(n, "h_op", 100.0)[0] == pytest.approx(0.8)


def test_hydro_inflow_operating_denominator(tmp_path):
    from s4c_layers import apply_hydro_inflow_normalization
    pd.DataFrame(dict(country=["MY"], target_mwh=[1100.0], multiplier=[1.1], status=["REGISTERED"])).to_csv(tmp_path / "T.csv", index=False)
    c = lambda v5: {"research": {"hydro": {"inflow_normalization": "national_observed", "target_table": "T.csv"}, "demand": {"v4": {"enabled": True}, "v5": v5}}}   # noqa: E731
    e = lambda n: n.storage_units_t.inflow.sum().to_dict()   # noqa: E731  (snapshot weight 1)
    n = _hydro_net(); apply_hydro_inflow_normalization(n, c({}), tmp_path)
    assert e(n) == pytest.approx({"h_op": 660.0, "h_con": 440.0})                                   # v4: T shared by capacity incl. construction
    n = _hydro_net(); led = apply_hydro_inflow_normalization(n, c({"enabled": True}), tmp_path)
    assert e(n) == pytest.approx({"h_op": 1100.0, "h_con": 1100.0 * 40 / 60})                       # v5: u = T / operating MW, construction units add u x p_nom
    assert led["v5"]["countries"]["MY"]["operating_mw"] == 60.0 and list(led["v5"]["countries"]["MY"]["partly_or_not_operating"]) == ["h_con"]
    n = _hydro_net(); apply_hydro_inflow_normalization(n, c({"enabled": True, "hydro_inflow_multiplier": 1.0}), tmp_path)
    assert e(n) == pytest.approx({"h_op": 1000.0, "h_con": 1000.0 * 40 / 60})                       # multiplier 1.0: T / 1.1
    n = _hydro_net(); apply_hydro_inflow_normalization(n, c({"enabled": True, "hydro_inflow_denominator": "all_stock"}), tmp_path)
    assert e(n) == pytest.approx({"h_op": 660.0, "h_con": 440.0})                                   # all_stock = v4


def test_hydro_spill_tables():
    import v5_layers as L
    su = pd.DataFrame(dict(carrier=["hydro", "hydro", "hydro existing"], p_nom_opt=[50.0, 0.5, 30.0], p_nom_max=[100.0, 10.0, 30.0], bus=["A 0"] * 3), index=["n1", "n2", "e1"])
    inflow = pd.DataFrame(dict(n1=[1e6, 1e6], n2=[2e5, 2e5], e1=[5e5, 5e5])); spill = pd.DataFrame(dict(n1=[6e5, 6e5], n2=[2e5, 2e5], e1=[1e5, 1e5]))
    r = L.hydro_spill_tables(su, inflow, spill, [3.0, 3.0], pd.Series("MY", index=su.index))
    t = r["totals"]
    assert t["new_inflow_full_cap_twh"] == pytest.approx(7.2) and t["new_spill_reported_twh"] == pytest.approx(4.8)
    assert t["new_spill_bookkeeping_twh"] == pytest.approx(6.0 * 0.5 + 1.2) and t["new_spill_true_twh"] == pytest.approx(4.8 - 4.2)   # n2 built 0.5 MW < 1 MW -> unbuilt
    assert t["existing_spill_twh"] == pytest.approx(0.6) and r["all_reported_spill_twh"] == pytest.approx(5.4)


# ---- 1-1 farm-point calibration, decision-251 bound, calibrated_gwa_v5 profiles ---------------------------------------------------
RV = ROOT / "research_inputs/renewable_v5"


def test_onwind_v5_calibration_tables():
    a = pd.read_csv(RV / "WIND_CALIBRATION_ALPHA_V5.csv").set_index("country"); s = pd.read_csv(RV / "WIND_OBSERVED_CF_SUMMARY.csv").set_index("country")
    cal = a[a.calibrated_individually]
    assert set(cal.index) == {"PH", "TH", "VN"} and (cal.alpha_grade == "B").all()
    w = s.loc[cal.index, "max_capacity_gw"]; aw = float((cal.alpha_main * w).sum() / w.sum())
    rest = a[~a.calibrated_individually]
    assert (rest.alpha_main - aw).abs().max() < 1e-12 and (rest.alpha_range_low == cal.alpha_main.min()).all() and (rest.alpha_range_high == cal.alpha_main.max()).all()
    fm = pd.read_csv(RV / "WIND_FARMS_MODEL_CF_2013_V5.csv")
    for c in cal.index:   # the farm-point calibrated CF (NREL 4 MW, capacity-weighted) equals the Ember observation
        d = fm[fm.iso == c]
        assert abs(float((d.cf_calibrated_nrel4mw * d["Capacity (MW)"]).sum() / d["Capacity (MW)"].sum()) - float(a.at[c, "cf_obs"])) < 1e-6
    pf = pd.read_csv(RV / "WIND_GWA_FARM_POINT_FACTOR_V5.csv").set_index("GEM unit/phase ID")
    assert (fm.set_index("GEM unit/phase ID").factor_point == pf.loc[fm["GEM unit/phase ID"], "factor_point"].values).all()


def test_onwind_effective_multiplier_bound():
    import json
    t = pd.read_csv(RV / "WIND_EFFECTIVE_MULTIPLIER_V5.csv"); ev = json.loads((RV / "WIND_EFFECTIVE_MULTIPLIER_V5.json").read_text())
    assert (t.set == "b").all() and t.cell_factor.all() and t.m_p50.between(0.8, 1.6).all() and t.median_in_bounds.all() and ev["stop"] == []
    assert (t.m_p10 <= t.m_p50).all() and (t.m_p50 <= t.m_p90).all() and tuple(ev["bounds"]) == (0.8, 1.6)
    a = pd.read_csv(RV / "WIND_CALIBRATION_ALPHA_V5.csv").set_index("country").alpha_main
    assert (t.set_index("country").alpha - a.reindex(t.country).values).abs().max() < 1e-12
    assert t.alpha_table_sha256.iloc[0] == V.sha256(RV / "WIND_CALIBRATION_ALPHA_V5.csv")


def test_wquantile():
    import numpy as np
    from v5_wind_effective_multiplier import wquantile
    v = np.array([3.0, 1.0, 2.0]); w = np.array([1.0, 1.0, 2.0])
    assert wquantile(v, w, 0.1) == 1.0 and wquantile(v, w, 0.5) == 2.0 and wquantile(v, w, 0.9) == 3.0 and wquantile(v, w, 0.25) == 1.0


def test_calibrated_gwa_v5_profiles_and_classes():
    import numpy as np
    import xarray as xr
    for N in (1, 3):
        new = xr.open_dataset(RV / f"profiles_calibrated_gwa_v5_c{N}_3h.nc"); ref = xr.open_dataset(RV / f"profiles_calibrated_modern_c{N}_3h.nc")
        for k in ("offwind_ac", "offwind_dc", "solar"):   # offshore and solar = the pypsa_eur run, as in calibrated_modern
            assert np.array_equal(new[k].values, ref[k].values, equal_nan=True)
        assert list(new.onwind.bus.values) == list(ref.onwind.bus.values) and not np.array_equal(new.onwind.values, ref.onwind.values)
        assert float(new.onwind.min()) >= 0.0 and float(new.onwind.max()) <= 1.0
        cls = pd.read_csv(RV / f"S4A_PROFILE_CLASSES_calibrated_gwa_v5_c{N}.csv")
        assert set(cls.variant) == {"calibrated_gwa_v5"} and set(cls.tech) == {"onwind", "offwind-ac", "offwind-dc", "solar"}
        s = cls[cls.tech == "onwind"].groupby("node").potential_share.sum()
        assert np.allclose(s.values, 1.0, atol=1e-9)                                                 # the classes partition the node potential
    import json
    man = json.loads((RV / "MANIFEST_V5.json").read_text())
    assert all(man[f"profiles_calibrated_gwa_v5_c{N}_3h.nc"]["sha256"] == V.sha256(RV / f"profiles_calibrated_gwa_v5_c{N}_3h.nc") for N in (1, 3))


def test_profile_variant_switch():
    import numpy as np
    import pypsa
    from s4a_layers import apply_renewable_profiles
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2920, freq="3h"))
    base = {"research": {"renewable": {"profile_variant": "calibrated_modern", "resource_classes": 3, "profile_dir": "research_inputs/renewable_v5"},
                         "demand": {"v4": {"enabled": True}, "v5": {}}}}
    led4 = apply_renewable_profiles(n, base, ROOT)
    assert led4["profile_variant"] == "calibrated_modern" and "S4A_PROFILE_CLASSES_c3.csv" in led4["files"]
    c5 = {"research": dict(base["research"], demand={"v4": {"enabled": True}, "v5": {"enabled": True}})}
    led5 = apply_renewable_profiles(n, c5, ROOT)
    assert led5["profile_variant"] == "calibrated_gwa_v5" and set(led5["files"]) == {"profiles_calibrated_gwa_v5_c3_3h.nc", "profiles_calibrated_gwa_v5_c1_3h.nc",
                                                                                     "S4A_PROFILE_CLASSES_calibrated_gwa_v5_c3.csv"}
    c5e = {"research": dict(base["research"], demand={"v4": {"enabled": True}, "v5": {"enabled": True, "onwind_calibration": "ember_country"}})}
    assert apply_renewable_profiles(n, c5e, ROOT)["profile_variant"] == "calibrated_modern"
    assert np.isfinite(led5["solar_density"]["scale"])


# ---- 1-2 existing wind on the best class, Q12 existing solar profile (decisions 241, 246) ------------------------------------------
def test_existing_profile_column():
    import v5_layers as L
    n = toy()
    cols = ["A 0 onwind-2025", "A 0 onwind-2025 c1", "A 0 onwind-2025 c2", "A 0 offwind-ac-2025", "A 0 offwind-ac-2025 c1", "A 0 solar-2025", "A 0 solar-2025 c1",
            "A 0 solar-2025 c2", "A 0 solar rooftop-2025", "A 1 onwind-2025", "A 1 solar-2025"]
    for c in cols:
        n.add("Generator", c, bus="A 0", carrier="x")
    n.generators_t.p_max_pu = pd.DataFrame(0.3, index=n.snapshots, columns=cols)
    f = L.existing_profile_column
    assert f(n, "A 0", "onwind existing", cfg())[0] == "A 0 onwind-2025"                                            # v5 off: class 0
    assert f(n, "A 0", "onwind existing", cfg({"enabled": True}))[0] == "A 0 onwind-2025 c2"                         # best class
    assert f(n, "A 0", "offwind existing", cfg({"enabled": True}))[0] == "A 0 offwind-ac-2025 c1"                   # falls back to the highest present class
    assert f(n, "A 1", "onwind existing", cfg({"enabled": True})) == ("A 1 onwind-2025", "class 0 (no higher class at the node)")
    assert f(n, "A 0", "onwind existing", cfg({"enabled": True, "existing_wind_profile": "class0"}))[0] == "A 0 onwind-2025"
    assert f(n, "A 0", "solar existing", cfg({"enabled": True, "existing_solar_profile": "node_average"}))[0] == "A 0 solar rooftop-2025"
    assert f(n, "A 0", "solar existing", cfg({"enabled": True, "existing_solar_profile": "best_class"}))[0] == "A 0 solar-2025 c2"
    assert f(n, "A 1", "solar existing", cfg({"enabled": True, "existing_solar_profile": "node_average"}))[0] == "A 1 solar-2025"   # no rooftop column
    assert f(n, "A 0", "solar existing", cfg({"enabled": True, "existing_solar_profile": "class0"}))[0] == "A 0 solar-2025"


# ---- 1-6 geothermal caps on the reserve basis, PH rebuild with the v5 lifetime rule (decision 241, Q16) -----------------------------
def test_geothermal_id_potential_table():
    import v5_layers as L
    t = pd.read_csv(ROOT / L.GEOTHERMAL_ID_TABLE).set_index("case")
    assert t.potential_mw.to_dict() == {"resource_potential": 23590, "reserves_2017": 17506, "proven_probable": 5460}
    assert 12046 + 2493 + 2967 == 17506 and 2493 + 2967 == 5460


@pytest.mark.skipif(not EB.exists(), reason="electric base not available")
def test_geothermal_caps_v5():
    import pypsa
    import v5_layers as L
    n = pypsa.Network(str(EB))
    caps = pd.read_csv(ROOT / "research_inputs/potentials_v5/CANDIDATE_CAPS_S4B2_BY_NODE.csv")
    caps = caps[(caps["mode"] == "national_potential") & (caps.variant == "announced_preconstruction")]
    rb4 = L.ph_geothermal_rebuild(n, "strict", 30)
    assert abs(float(rb4.sum()) - 1827.0) < 0.5                                                     # = the S4B-2 rebuild part (REG candidate_cap_geothermal_PH)
    for life, bnd in ((30, "strict"), (40, "inclusive")):
        for case, pot in (("reserves_2017", 17506.0), ("proven_probable", 5460.0), ("resource_potential", 23590.0)):
            m = n.copy()
            m.add("Generator", "x geo", bus=m.buses.index[m.buses.country == "ID"][0], carrier="geothermal existing", p_nom=1000.0 + life)
            out, led = L.geothermal_caps_v5(m, caps, cfg({"enabled": True, "geothermal_cap_id": case, "geothermal_existing_lifetime": life, "lifetime_boundary": bnd}), ROOT)
            stock = led["ID"]["stock_mw"]
            idc = out[(out.carrier == "geothermal") & (out.country == "ID")].p_nom_max_mw.sum()
            assert abs(idc + stock - pot) < 1e-6                                                       # cap + stock = the chosen potential
            other = out[~((out.carrier == "geothermal") & out.country.isin(["ID", "PH"]))]
            assert other.equals(caps[~((caps.carrier == "geothermal") & caps.country.isin(["ID", "PH"]))])
            ph = out[(out.carrier == "geothermal") & (out.country == "PH")].p_nom_max_mw.sum(); ph0 = caps[(caps.carrier == "geothermal") & (caps.country == "PH")].p_nom_max_mw.sum()
            assert abs(ph - (ph0 - led["PH_rebuild"]["v4_mw"] + led["PH_rebuild"]["v5_mw"])) < 1e-6
            if life == 30:
                assert abs(ph - ph0) < 1e-9 and led["PH_rebuild"]["v5_mw"] == led["PH_rebuild"]["v4_mw"]
            else:
                assert led["PH_rebuild"]["v5_mw"] < led["PH_rebuild"]["v4_mw"]                       # 40 a / inclusive: fewer units retire before 2050
    assert L.geothermal_caps_v5(n, caps, cfg(), ROOT)[0] is caps                                      # v5 off: the table rows as they are
