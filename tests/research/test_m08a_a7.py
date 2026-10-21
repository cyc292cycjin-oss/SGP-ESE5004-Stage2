"""M08a A7 (decisions 132, 133): scenario / coalition / finance variants of a base network (toy networks; no build, no solve)."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from m08a_layers import (VARIANT_DEFAULTS, apply_co2_shipping, apply_remove_countries, apply_stock_mode,   # noqa: E402
                         non_default_variants, variant_values)

CC = ["ID", "MY", "SG"]


def toy(scenario="integrated"):
    n = pypsa.Network(); n.set_snapshots(range(2)); n.snapshot_weightings.loc[:, :] = 3.0
    def bus(name, carrier, c):
        n.add("Bus", name, carrier=carrier); n.buses.loc[name, "country"] = c
    for c in CC:
        bus(f"{c}1", "AC", c); bus(f"{c}1 gas", "gas", c); bus(f"{c}1 co2 stored", "co2 stored", c); bus(f"{c}1 oil", "oil", c)
        bus(f"co2 atmosphere {c}", "co2", c); bus(f"co2 sequestered extra-ASEAN {c}", "co2 sequestered extra-ASEAN", c)
        n.add("Load", f"{c}1 load", bus=f"{c}1", p_set=100.0); n.loads.loc[f"{c}1 load", "country"] = c
        n.add("Store", f"co2 atmosphere {c}", bus=f"co2 atmosphere {c}", e_nom_extendable=True, e_min_pu=-1)
        n.add("Store", f"co2 sequestered extra-ASEAN {c}", bus=f"co2 sequestered extra-ASEAN {c}", carrier="co2 sequestered extra-ASEAN", e_nom_extendable=True)
        n.add("Link", f"{c}1 co2 export extra-ASEAN", bus0=f"{c}1 co2 stored", bus1=f"co2 sequestered extra-ASEAN {c}", carrier="CO2 export extra-ASEAN", p_nom_extendable=True)
    for c in ("ID", "MY"):
        bus(f"co2 sequestered {c}", "co2 sequestered", c)
        n.add("Store", f"co2 sequestered {c}", bus=f"co2 sequestered {c}", carrier="co2 sequestered", e_nom_extendable=True, e_nom_max=1e6)
    bus("ASEAN oil", "oil", "ASEAN"); bus("ASEAN ammonia", "ammonia", "ASEAN")
    for c in CC:
        n.add("Link", f"oil pool {c}1", bus0="ASEAN oil", bus1=f"{c}1 oil", carrier="oil pool", p_nom_extendable=True)
    n.add("Load", "ASEAN aviation international oil demand", bus="ASEAN oil", p_set=40.0); n.loads.loc["ASEAN aviation international oil demand", "country"] = "ASEAN"
    n.add("Load", "MY1 industry ammonia demand", bus="ASEAN ammonia", p_set=7.0); n.loads.loc["MY1 industry ammonia demand", "country"] = "MY"
    n.add("Generator", "MY1 LNG import", bus="MY1 gas", carrier="LNG import", p_nom_extendable=True, p_nom_max=np.inf)
    n.add("Generator", "ID1 solar", bus="ID1", carrier="solar", p_nom_extendable=True, capital_cost=100.0)
    n.add("Generator", "ID1 solar rooftop", bus="ID1", carrier="solar rooftop", p_nom_extendable=True, capital_cost=100.0)
    for g, c in (("ID1 solar", "ID"), ("ID1 solar rooftop", "ID"), ("MY1 LNG import", "MY")):
        n.generators.loc[g, "country"] = c
    if scenario == "integrated":
        n.add("Line", "L stock", bus0="ID1", bus1="MY1", s_nom=100.0, s_nom_min=100.0, s_nom_extendable=True, s_nom_max=20100.0, x=0.1, r=0.01, capital_cost=50.0, carrier="AC")
        n.add("Line", "L cand", bus0="MY1", bus1="SG1", s_nom=0.0, s_nom_min=0.0, s_nom_extendable=True, s_nom_max=20000.0, x=0.1, r=0.01, capital_cost=50.0, carrier="AC")
        n.add("Link", "DC stock", bus0="ID1", bus1="SG1", p_nom=50.0, p_nom_min=50.0, p_nom_extendable=True, p_nom_max=20050.0, carrier="DC", capital_cost=10.0)
        n.add("Link", "DC stock-reversed", bus0="SG1", bus1="ID1", p_nom=50.0, p_nom_min=0.0, p_nom_extendable=True, p_nom_max=20050.0, carrier="DC", capital_cost=0.0)
        n.add("Link", "gas pipeline existing ID-SG", bus0="ID1 gas", bus1="SG1 gas", p_nom=8795.0, p_nom_min=8795.0, p_nom_extendable=True, carrier="gas pipeline")
        n.add("Link", "H2 pipeline ID1 -> MY1", bus0="ID1", bus1="MY1", p_nom_extendable=True, carrier="H2 pipeline", capital_cost=5.0)
    n.add("Link", "ID1 co2 ship to MY", bus0="ID1 co2 stored", bus1="co2 sequestered MY", carrier="CO2 ship", p_nom_extendable=True)
    n.add("Link", "MY1 co2 ship to ID", bus0="MY1 co2 stored", bus1="co2 sequestered ID", carrier="CO2 ship", p_nom_extendable=True)
    L = n.links
    L["reversed"] = L.index.str.endswith("-reversed")
    L["gas_pipeline_kind"] = np.where(L.index.str.startswith("gas pipeline existing"), "existing_2025", "")
    L["country"] = [str(n.buses.at[b, "country"]) if str(n.buses.at[b, "country"]) != "ASEAN" else str(n.buses.at[b1, "country"]) for b, b1 in zip(L.bus0, L.bus1)]
    from scenario_network import tag_cross_border
    tag_cross_border(n)
    n.meta.update(scenario=scenario, existing_unit_components={"u1": dict(component_type="Generator", component="MY1 LNG import", capacity_mw=0.0, commissioning_year=2020)},
                  research_co2_storage=dict(caps_t_per_year={"ID": 1e6, "MY": 1e6, "SG": 0.0}), store_power_rules={"co2 sequestered ID": "charge_only", "co2 sequestered MY": "charge_only"},
                  demand_owners={x: {} for x in n.loads.index}, existing_annual_fixed_om_eur=0.0)
    n.generators["existing_annual_fixed_om_eur"] = 0.0
    return n


def bus_ports(n):
    out = set()
    for c in n.iterate_components(["Generator", "Load", "Store", "StorageUnit", "Link", "Line"]):
        for col in [k for k in c.df.columns if k == "bus" or (k.startswith("bus") and k[3:].isdigit())]:
            out |= set(c.df[col])
    return out - {""}


def demand(n):
    return float(n.get_switchable_as_dense("Load", "p_set").mul(n.snapshot_weightings.generators, axis=0).sum().sum())


def test_defaults_and_build_refusal():
    from phase4_static import config
    R = config(ROOT, "integrated")["research"]
    assert variant_values(R) == VARIANT_DEFAULTS and non_default_variants(R) == {}
    R2 = copy.deepcopy(R); R2["coalition"]["remove_countries"] = ["VN"]; R2["finance"]["wacc_mode"] = "country_specific"
    assert non_default_variants(R2) == {"coalition.remove_countries": ["VN"], "finance.wacc_mode": "country_specific"}


def test_remove_country_entirely():
    n = toy(); total = demand(n); my = 100.0 * 2 * 3 + 7.0 * 2 * 3
    led = apply_remove_countries(n, ["MY"])
    assert demand(n) == pytest.approx(total - my) and led["demand_removed_mwh"] == pytest.approx(my)   # remaining = integrated - removed country demand
    my_buses = {b for b in bus_ports(toy()) if b.startswith("MY1") or b.endswith(" MY")}
    assert not (bus_ports(n) & my_buses) and not (n.buses.country == "MY").any()                        # no component references a removed bus
    assert "ASEAN aviation international oil demand" in n.loads.index and "MY1 industry ammonia demand" not in n.loads.index
    assert "L stock" not in n.lines.index and "H2 pipeline ID1 -> MY1" not in n.links.index and "ID1 co2 ship to MY" not in n.links.index
    assert "MY1 LNG import" not in n.generators.index and "oil pool MY1" not in n.links.index and "oil pool ID1" in n.links.index
    assert n.meta["research_countries"] == ["BN", "ID", "KH", "LA", "MM", "PH", "SG", "TH", "TL", "VN"]
    assert "MY" not in n.meta["research_co2_storage"]["caps_t_per_year"] and "co2 sequestered MY" not in n.meta["store_power_rules"]
    assert set(n.meta["demand_owners"]) == set(n.loads.index) and n.meta["existing_unit_components"] == {}
    from carrier_architecture import network_countries
    assert "MY" not in network_countries(n)
    with pytest.raises(ValueError):
        apply_remove_countries(toy(), ["XX"])


def test_keep_stock_no_new():
    n = toy("integrated"); led = apply_stock_mode(n, "keep_stock_no_new")
    assert set(n.lines.index) == {"L stock"} and (n.lines.loc["L stock", ["s_nom", "s_nom_min", "s_nom_max"]] == 100.0).all()
    assert {"DC stock", "DC stock-reversed", "gas pipeline existing ID-SG"} <= set(n.links.index) and "H2 pipeline ID1 -> MY1" not in n.links.index
    assert (n.links.loc["DC stock-reversed", ["p_nom", "p_nom_min", "p_nom_max"]] == 50.0).all() and n.links.at["gas pipeline existing ID-SG", "p_nom_max"] == 8795.0
    assert n.links.loc[["DC stock", "DC stock-reversed"], "p_nom_extendable"].all()
    assert led["kept_lines"] == 1 and led["kept_links_forward"] == 2 and led["kept_reversed_twins"] == 1 and led["removed_lines"] == 1
    assert "ID1 co2 ship to MY" in n.links.index   # maritime trade unchanged
    with pytest.raises(ValueError):
        apply_stock_mode(toy("disconnected"), "keep_stock_no_new")
    assert apply_stock_mode(toy("disconnected"), "remove_all") == dict(mode="remove_all")


def test_co2_shipping_forbid():
    n = toy("disconnected"); led = apply_co2_shipping(n, "forbid")
    assert led["removed"] == 2 and not n.links.carrier.isin(["CO2 ship", "CO2 transit ship", "CO2 transit rail"]).any()
    assert (n.links.carrier == "CO2 export extra-ASEAN").sum() == 3
    assert led["sink_channels_after"]["SG"]["sink_kinds"] == ["extra_asean"] and led["sink_channels_after"]["ID"]["sink_kinds"] == ["extra_asean"]
    assert led["sink_channels_before"]["ID"]["sink_kinds"] == ["extra_asean", "national_other_asean"]
    with pytest.raises(ValueError):
        apply_co2_shipping(toy("integrated"), "forbid")
    assert apply_co2_shipping(toy("integrated"), "allow") == dict(mode="allow")


def toy_b1(with_mm=False, transit=True, transit_to="co2 sequestered extra-ASEAN LA"):
    """VN (coast, national store + extra-ASEAN), LA (landlocked: LA1 - LA2 pipeline; LA1 transit export extra-ASEAN, rail into the VN store,
    LA2 transit ship into the VN store), optional MM whose only outlet is a CO2 ship into the VN store."""
    n = pypsa.Network(); n.set_snapshots(range(2))
    def bus(name, carrier, c):
        n.add("Bus", name, carrier=carrier); n.buses.loc[name, "country"] = c
    for b, c in (("VN1 co2 stored", "VN"), ("LA1 co2 stored", "LA"), ("LA2 co2 stored", "LA")) + ((("MM1 co2 stored", "MM"),) if with_mm else ()):
        bus(b, "co2 stored", c); n.add("Store", b, bus=b, carrier="co2 stored", e_nom_extendable=True, e_cyclic=True)
    bus("TL1 co2 stored", "co2 stored", "TL")   # pass-through bus (no store, no pipeline, no sink link): listed apart, not a node without sink
    for c in ("VN", "LA"):
        bus(f"co2 sequestered extra-ASEAN {c}", "co2 sequestered extra-ASEAN", c)
        n.add("Store", f"co2 sequestered extra-ASEAN {c}", bus=f"co2 sequestered extra-ASEAN {c}", carrier="co2 sequestered extra-ASEAN", e_nom_extendable=True)
    bus("co2 sequestered VN", "co2 sequestered", "VN")
    n.add("Store", "co2 sequestered VN", bus="co2 sequestered VN", carrier="co2 sequestered", e_nom_extendable=True, e_nom_max=106e6)
    links = [("VN1 co2 sequestration", "VN1 co2 stored", "co2 sequestered VN", "CO2 sequestration", "VN", 0.0),
             ("VN1 co2 export extra-ASEAN", "VN1 co2 stored", "co2 sequestered extra-ASEAN VN", "CO2 export extra-ASEAN", "VN", 0.0),
             ("CO2 pipeline LA1 -> LA2", "LA1 co2 stored", "LA2 co2 stored", "CO2 pipeline", "LA", 0.0),
             ("LA1 co2 transit to VN store", "LA1 co2 stored", "co2 sequestered VN", "CO2 transit rail", "LA", 10.0),
             ("LA2 co2 transit ship to VN", "LA2 co2 stored", "co2 sequestered VN", "CO2 transit ship", "LA", 25.0)]
    if transit:
        links.append(("LA1 co2 transit export extra-ASEAN", "LA1 co2 stored", transit_to, "CO2 transit export extra-ASEAN", "LA", 10.0033))
    if with_mm:
        links.append(("MM1 co2 ship to VN", "MM1 co2 stored", "co2 sequestered VN", "CO2 ship", "MM", 20.0))
    for k, b0, b1, car, c, mc in links:
        n.add("Link", k, bus0=b0, bus1=b1, carrier=car, p_nom_extendable=True, marginal_cost=mc, p_min_pu=-1.0 if car == "CO2 pipeline" else 0.0)
        n.links.loc[k, "country"] = c
    n.meta.update(scenario="disconnected")
    return n


def test_b1_landlocked_transit_kept_and_checked():
    """Supplement 01 section 2: under b1 LA keeps ONLY its transit corridor to its own extra-ASEAN store; every country keeps a sink."""
    n = toy_b1(); led = apply_co2_shipping(n, "forbid")
    assert led["removed_by_carrier"] == {"CO2 transit rail": 1, "CO2 transit ship": 1}
    assert "LA1 co2 transit export extra-ASEAN" in n.links.index and n.links.at["LA1 co2 transit export extra-ASEAN", "bus1"] == "co2 sequestered extra-ASEAN LA"
    assert led["landlocked_transit"]["LA"] == dict(transit_links=1, store="co2 sequestered extra-ASEAN LA", land_leg_eur2020_per_t={"LA1 co2 transit export extra-ASEAN": 10.0033},
                                                    links_into_other_national_stores=0)
    after = led["sink_channels_after"]
    assert after["LA"]["sink_kinds"] == ["extra_asean"] and after["LA"]["nodes_without_sink"] == []          # LA2 reaches the corridor through the pipeline
    assert after["VN"]["sink_kinds"] == ["extra_asean", "national_own"] and after["VN"]["national_cap_t_per_year"] == 106e6
    assert led["sink_channels_before"]["LA"]["sink_kinds"] == ["extra_asean", "national_other_asean"]
    assert after["TL"] == dict(nodes=0, nodes_without_sink=[], passthrough_buses=["TL1 co2 stored"], sink_kinds=[], direct_links_by_carrier={},
                               national_cap_t_per_year=0.0, process_emission_nodes=0)
    with pytest.raises(ValueError, match="MM"):                               # a country whose only outlet was intra-ASEAN shipping: refused
        apply_co2_shipping(toy_b1(with_mm=True), "forbid")
    with pytest.raises(ValueError, match="LA"):                               # no transit corridor: LA would lose every outlet
        apply_co2_shipping(toy_b1(transit=False), "forbid")
    with pytest.raises(AssertionError):                                       # a transit link into another country's store is not a transit-only corridor
        apply_co2_shipping(toy_b1(transit_to="co2 sequestered extra-ASEAN VN"), "forbid")


def test_country_wacc_rules():
    from phase4_static import config
    from s2_costs import annuity, build_research_costs
    from s4c_layers import apply_wacc_mode
    cfg = config(ROOT, "integrated"); costs, _ = build_research_costs(ROOT, cfg, ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv")
    t = pd.read_csv(ROOT / cfg["research"]["finance"]["country_wacc_table"]).set_index("country")
    assert len(t) == 11 and t.at["TL", "wacc_real"] == pytest.approx((t.at["KH", "wacc_real"] + t.at["LA", "wacc_real"] + t.at["MM", "wacc_real"]) / 3, abs=1e-6)
    cs = copy.deepcopy(cfg); cs["research"]["finance"]["wacc_mode"] = "country_specific"
    n = toy("integrated"); led = apply_wacc_mode(n, costs, cs, ROOT)
    life, fom, r0 = float(costs.at["solar-utility", "lifetime"]), float(costs.at["solar-utility", "FOM"]) / 100, float(costs.at["solar-utility", "discount rate"])
    rid = float(t.at["ID", "wacc_real"])
    assert n.generators.at["ID1 solar", "capital_cost"] == pytest.approx(100 * (annuity(life, rid) + fom) / (annuity(life, r0) + fom), rel=1e-12)
    assert n.generators.at["ID1 solar rooftop", "capital_cost"] == 100.0 and led["distributed_kept_at_cost_row_rate"] >= 1   # technology_data_fixed
    lf, lfom, lr0 = (float(costs.at["HVAC overhead", k]) for k in ("lifetime", "FOM", "discount rate"))
    rmean = (rid + float(t.at["MY", "wacc_real"])) / 2
    assert n.lines.at["L stock", "capital_cost"] == pytest.approx(50 * (annuity(lf, rmean) + lfom / 100) / (annuity(lf, lr0) + lfom / 100), rel=1e-12)
    cp = copy.deepcopy(cs); cp["research"]["finance"]["distributed_wacc_rule"] = "proportional"
    n2 = toy("integrated"); apply_wacc_mode(n2, costs, cp, ROOT)
    rl, rf, rr0 = (float(costs.at["solar-rooftop", k]) for k in ("lifetime", "FOM", "discount rate"))
    assert rr0 == pytest.approx(0.04) and n2.generators.at["ID1 solar rooftop", "capital_cost"] == pytest.approx(
        100 * (annuity(rl, rid * rr0 / 0.07) + rf / 100) / (annuity(rl, rr0) + rf / 100), rel=1e-12)


def test_variant_script_deterministic(tmp_path, monkeypatch):
    """End to end on a toy base network: same input -> same output SHA256; receipt with input / output hashes."""
    from m08a_variants import derive
    from phase4_static import config
    from scenario_network import config_sha
    monkeypatch.setenv("PYTHONHASHSEED", "0")
    R = config(ROOT, "disconnected")["research"]; R["config_overrides"] = []
    n = toy("disconnected"); n.meta.update(research_config=json.loads(json.dumps(R, default=str)), research_config_sha256=config_sha(R))
    base = tmp_path / "disconnected_2920_3h_unsolved.nc"; n.export_to_netcdf(base)
    r1 = derive(ROOT, base, tmp_path / "a", {"disconnected.co2_shipping_intra_asean": "forbid"})
    r2 = derive(ROOT, base, tmp_path / "b", {"disconnected.co2_shipping_intra_asean": "forbid"})
    assert r1["output"]["sha256"] == r2["output"]["sha256"] and r1["base"]["sha256"] == hashlib.sha256(base.read_bytes()).hexdigest()
    assert r1["base"]["stale_config"] is False and r1["ledgers"]["co2_shipping"]["removed"] == 2
    out = pypsa.Network(r1["output"]["path"])
    assert out.meta["research_config"]["disconnected"]["co2_shipping_intra_asean"] == "forbid"
    assert out.meta["research_config_sha256"] == config_sha(out.meta["research_config"]) and "disconnected.co2_shipping_intra_asean=forbid" in out.meta["research_config"]["config_overrides"]
    with pytest.raises(SystemExit):   # a base built with another config is refused
        m = pypsa.Network(str(base)); m.meta["research_config_sha256"] = "0" * 64; p = tmp_path / "stale.nc"; m.export_to_netcdf(p)
        derive(ROOT, p, tmp_path / "c", {"disconnected.co2_shipping_intra_asean": "forbid"})
