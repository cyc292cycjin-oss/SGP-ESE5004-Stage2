"""V4 D2a (decision 220; V4_D2A_INSTRUCTION.md sections 3.3 / 3.4): PHS stock reclassification (frozen Bhumibol group) and the asean sensitivity case of the new
PHS candidates, on small in-memory networks; the main case leaves the network unchanged. No solver, no network build."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


def _costs():
    return pd.DataFrame({"FOM": [1.0, 1.0], "investment": [2297342.24874, 2000000.0]}, index=["PHS", "hydro"])


def _toy(reclass_table=None):
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=8, freq="3h"))
    for b, c in (("TH2 4", "TH"), ("TH2 2", "TH"), ("ID_Java-Bali1 0", "ID"), ("MY_Peninsular2 0", "MY"), ("MY_Peninsular2 1", "MY")):
        n.add("Bus", b, carrier="AC"); n.buses.at[b, "country"] = c
    n.add("StorageUnit", "existing_survivor::TH2 4::Hydro::6b2ad09f452a", bus="TH2 4", carrier="PHS existing", p_nom=950.0, max_hours=6.0, efficiency_store=0.75 ** 0.5, efficiency_dispatch=0.75 ** 0.5, p_min_pu=-1.0, cyclic_state_of_charge=True)
    n.add("StorageUnit", "existing_survivor::GEM:G100000603608", bus="TH2 4", carrier="hydro existing", p_nom=500.0, max_hours=6.0, efficiency_store=0.0, efficiency_dispatch=0.9, p_min_pu=0.0, cyclic_state_of_charge=True)
    n.add("StorageUnit", "existing_survivor::MY_Peninsular2 0::Hydro::d639", bus="MY_Peninsular2 0", carrier="hydro existing", p_nom=2577.0, max_hours=6.0, efficiency_store=0.0, efficiency_dispatch=0.9, p_min_pu=0.0)
    n.storage_units_t.inflow["existing_survivor::GEM:G100000603608"] = np.linspace(100.0, 200.0, 8)
    n.storage_units_t.inflow["existing_survivor::MY_Peninsular2 0::Hydro::d639"] = np.full(8, 300.0)
    for name, c in (("existing_survivor::TH2 4::Hydro::6b2ad09f452a", "TH"), ("existing_survivor::GEM:G100000603608", "TH"), ("existing_survivor::MY_Peninsular2 0::Hydro::d639", "MY")):
        n.storage_units.loc[name, ["asset_role", "country", "existing_fixed_om_eur_per_mw_year", "existing_annual_fixed_om_eur", "hydro_subtype", "source_parent_id", "source_unit_id",
                                   "source_group_capacity_mw", "retained_electric_capacity_mw"]] = \
            ["existing_survivor", c, 22973.422487, 22973.422487 * float(n.storage_units.at[name, "p_nom"]), "Pumped Storage" if "6b2ad" in name else "Reservoir", "PPM:264", json.dumps(["G100000603603", "G100000604991"]),
             float(n.storage_units.at[name, "p_nom"]), float(n.storage_units.at[name, "p_nom"])]
    for b in ("TH2 2", "ID_Java-Bali1 0", "MY_Peninsular2 0", "MY_Peninsular2 1"):
        n.add("StorageUnit", f"{b} PHS_new", bus=b, carrier="PHS", p_nom=0.0, p_nom_extendable=True, p_nom_max=(2480.0 if b == "TH2 2" else (2400.0 if b.startswith("ID") else 0.0)), max_hours=6.0,
              efficiency_store=0.75 ** 0.5, efficiency_dispatch=0.75 ** 0.5, capital_cost=184507.761553, cyclic_state_of_charge=True, lifetime=80.0)
        n.storage_units.at[f"{b} PHS_new", "country"] = n.buses.at[b, "country"]; n.storage_units.at[f"{b} PHS_new", "s1_candidate_status"] = "REGISTERED_S4B2"
    n.meta["existing_unit_components"] = {
        "GEM:G100000603603": dict(component_type="StorageUnit", component="existing_survivor::TH2 4::Hydro::6b2ad09f452a", capacity_mw=779.0, node="TH2 4", commissioning_year=1964, retirement_year=2064.0, source="GHT"),
        "GEM:G100000604991": dict(component_type="StorageUnit", component="existing_survivor::TH2 4::Hydro::6b2ad09f452a", capacity_mw=171.0, node="TH2 4", commissioning_year=1996, retirement_year=2096.0, source="GHT")}
    n.meta["existing_annual_fixed_om_eur"] = float(n.storage_units.existing_annual_fixed_om_eur.sum())
    n.meta["required_constraint_hooks"] = ["research_existing_assets"]
    return n


def _cfg(enabled=None, v4=True, phs_case="main"):
    return {"research": {"demand": {"anchor_mode": "ras", "v4": {"enabled": v4}}, "fleet": {"phs_stock_reclass": enabled}, "supply": {"phs_case": phs_case},
                         "finance": {"uniform_discount_rate": 0.07}, "candidates": {}}}


# ---------------------------------------------------------------------------------------------------------------- 3.3 reclassification
def test_reclass_table_is_consistent_with_gem_and_egat():
    t = pd.read_csv(ROOT / "research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv", keep_default_na=False)
    assert list(t.identity) == ["GEM:G100000603603"] and float(t.gem_capacity_mw[0]) == 779.0
    assert float(t.reclass_mw[0]) == pytest.approx(608.2) and float(t.drop_mw[0]) == pytest.approx(170.8)   # EGAT 6 x 82.2 + 115 = 608.2; 779.2 - 608.2 = 171 (unit 8)
    gem = pd.read_csv(ROOT / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", keep_default_na=False, low_memory=False)
    col = [c for c in gem.columns if "GEM unit" in c or c.endswith("unit ID") or c == "GEM unit ID"]
    rows = gem[gem.apply(lambda r: "G100000603603" in r.values or "G100000604991" in r.values, axis=1)]
    assert len(rows) == 2 and sorted(rows["Capacity (MW)"].astype(float)) == [171.0, 779.0] and sorted(rows["Technology"]) == ["conventional storage", "pumped storage"]
    assert 6 * 82.2 + 115 + 171 == pytest.approx(779.2)


def test_reclass_off_leaves_the_network_unchanged():
    from s4a_fleet import reclassify_phs_stock
    for cfg in (_cfg(enabled=False, v4=True), _cfg(enabled=None, v4=False)):
        n = _toy(); before = n.storage_units.copy(); fom0 = n.meta["existing_annual_fixed_om_eur"]
        led = reclassify_phs_stock(n, _costs(), cfg, ROOT)
        assert led["enabled"] is False and n.storage_units.equals(before) and n.meta["existing_annual_fixed_om_eur"] == fom0
        assert n.meta["research_phs_stock_reclass"]["enabled"] is False


def test_reclass_splits_bhumibol_into_phs_and_reservoir():
    from s4a_fleet import reclassify_phs_stock
    n = _toy(); costs = _costs(); fom0 = n.meta["existing_annual_fixed_om_eur"]
    led = reclassify_phs_stock(n, costs, _cfg(enabled=None, v4=True), ROOT)   # null follows v4.enabled
    assert led["enabled"] and led["rule"].startswith("null") and led["mw_reclassified"] == pytest.approx(608.2) and led["mw_dropped"] == pytest.approx(170.8)
    su = n.storage_units
    phs = "existing_survivor::TH2 4::Hydro::6b2ad09f452a"; new = "existing_survivor::TH2 4::hydro existing::D2A"
    assert float(su.at[phs, "p_nom"]) == pytest.approx(171.0) and su.at[phs, "carrier"] == "PHS existing"
    assert float(su.at[phs, "existing_annual_fixed_om_eur"]) == pytest.approx(22973.422487 * 171.0) and json.loads(su.at[phs, "source_unit_id"]) == ["G100000604991"]
    assert float(su.at[phs, "source_group_capacity_mw"]) == pytest.approx(171.0) and float(su.at[phs, "retained_electric_capacity_mw"]) == pytest.approx(171.0)
    assert new in su.index and su.at[new, "carrier"] == "hydro existing" and float(su.at[new, "p_nom"]) == pytest.approx(608.2)
    assert su.at[new, "asset_role"] == "existing_survivor" and not bool(su.at[new, "p_nom_extendable"]) and float(su.at[new, "capital_cost"]) == 0.0
    assert float(su.at[new, "efficiency_store"]) == 0.0 and float(su.at[new, "efficiency_dispatch"]) == 0.9 and float(su.at[new, "p_min_pu"]) == 0.0 and su.at[new, "hydro_subtype"] == "Reservoir"
    assert int(su.at[new, "build_year"]) == 1964 and float(su.at[new, "lifetime"]) == pytest.approx(100.0)
    fom_h = 1.0 / 100.0 * 2000000.0
    assert float(su.at[new, "existing_fixed_om_eur_per_mw_year"]) == pytest.approx(fom_h) and float(su.at[new, "existing_annual_fixed_om_eur"]) == pytest.approx(fom_h * 608.2)
    # inflow proxy: the node's existing reservoir (500 MW, inflow 100..200 MW) per MW x 608.2
    want = np.linspace(100.0, 200.0, 8) / 500.0 * 608.2
    assert np.allclose(n.storage_units_t.inflow[new].values, want) and led["created"][0]["proxy_scope"] == "node"
    # identities and the FOM constant
    ident = n.meta["existing_unit_components"]
    assert ident["GEM:G100000603603"]["component"] == new and ident["GEM:G100000603603"]["capacity_mw"] == pytest.approx(608.2) and ident["GEM:G100000604991"]["component"] == phs
    assert ident["GEM:G100000603603"]["d2a_reclass"]["drop_mw"] == pytest.approx(170.8)
    assert n.meta["existing_annual_fixed_om_eur"] == pytest.approx(fom0 - 22973.422487 * 779.0 + fom_h * 608.2)
    assert n.meta["existing_annual_fixed_om_eur"] == pytest.approx(float(su.existing_annual_fixed_om_eur.sum()))   # FOM once
    # capacity identity of every existing component = sum of its identities (the vintage cost step checks this)
    for comp in {v["component"] for v in ident.values()}:
        assert float(su.at[comp, "p_nom"]) == pytest.approx(sum(float(v["capacity_mw"]) for v in ident.values() if v["component"] == comp))
    # the hook list is unchanged (no new hook needed) and the PHS candidates untouched
    assert n.meta["required_constraint_hooks"] == ["research_existing_assets"] and float(su.at["TH2 2 PHS_new", "p_nom_max"]) == 2480.0


def test_reclass_refuses_a_mismatching_table(tmp_path):
    from s4a_fleet import reclassify_phs_stock
    t = pd.read_csv(ROOT / "research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv", keep_default_na=False)
    t.loc[0, "reclass_mw"] = 700.0
    (tmp_path / "research_inputs/fleet_v5").mkdir(parents=True); t.to_csv(tmp_path / "research_inputs/fleet_v5/PHS_STOCK_RECLASS_V4.csv", index=False)
    with pytest.raises(ValueError):
        reclassify_phs_stock(_toy(), _costs(), _cfg(enabled=True), tmp_path)


# ---------------------------------------------------------------------------------------------------------------- 3.4 asean case
def test_phs_case_main_is_unchanged():
    from s4b_candidates import phs_asean_case
    n = _toy(); before = n.storage_units.copy(); hooks = list(n.meta["required_constraint_hooks"])
    assert phs_asean_case(n, _cfg(phs_case="main"), ROOT) == dict(mode="main")
    assert n.storage_units.equals(before) and n.meta["required_constraint_hooks"] == hooks and "research_phs_energy_caps" not in n.meta
    with pytest.raises(ValueError):
        phs_asean_case(_toy(), _cfg(phs_case="other"), ROOT)


def test_phs_case_asean_tiers_costs_and_energy_caps():
    from s4b_candidates import PHS_ENERGY_HOOK, PHS_TIERS, phs_asean_case
    n = _toy(); out = phs_asean_case(n, _cfg(phs_case="asean"), ROOT)
    su = n.storage_units; t = pd.read_csv(ROOT / "research_inputs/potentials_v5/PHS_ASEAN_CASE_V4.csv", keep_default_na=False).set_index("country")
    r = 0.07; af = r / (1 - (1 + r) ** -50)
    cp = float(t.at["ID", "power_eur2020_per_kw"]) * 1e3 * af + float(t.at["ID", "fom_eur2020_per_kw_a"]) * 1e3; ce = float(t.at["ID", "energy_eur2020_per_kwh"]) * 1e3 * af
    assert cp == pytest.approx(491.248034241e3 * af + 6140.60042801) and ce == pytest.approx(43861.4316287 * af)
    # ID: the GEM-cap candidate becomes three tiers under the 103 TWh cap
    for h in PHS_TIERS:
        name = "ID_Java-Bali1 0 PHS_new" if h == 6.0 else f"ID_Java-Bali1 0 PHS_new {int(h)}h"
        assert name in su.index and float(su.at[name, "max_hours"]) == h and float(su.at[name, "capital_cost"]) == pytest.approx(cp + h * ce)
        assert float(su.at[name, "p_nom_max"]) == pytest.approx(103e6 / h) and float(su.at[name, "efficiency_store"]) == pytest.approx(0.8 ** 0.5) and bool(su.at[name, "p_nom_extendable"])
        assert su.at[name, "country"] == "ID" and su.at[name, "s1_candidate_status"] == "REGISTERED_D2A_ASEAN" and su.at[name, "carrier"] == "PHS"
    assert float(su.at["ID_Java-Bali1 0 PHS_new", "capital_cost"]) < 184507.761553   # 6 h tier about a third of the technology-data annuity
    # TH: 16 TWh cap on the GEM-cap candidate
    assert out["countries"]["TH"]["units"] == ["TH2 2 PHS_new", "TH2 2 PHS_new 12h", "TH2 2 PHS_new 24h"] and out["countries"]["TH"]["energy_cap_mwh"] == 16e6
    # MY: no GEM cap -> the node with existing reservoir hydro only
    assert out["countries"]["MY"]["node_rule"].startswith("nodes with existing reservoir hydro") and out["countries"]["MY"]["units"][0] == "MY_Peninsular2 0 PHS_new"
    assert "MY_Peninsular2 1 PHS_new 12h" not in su.index and float(su.at["MY_Peninsular2 1 PHS_new", "p_nom_max"]) == 0.0
    # countries without an ANU figure keep S4B-2
    assert out["countries"]["KH"]["mode"].startswith("kept") and "KH" not in n.meta["research_phs_energy_caps"]
    assert PHS_ENERGY_HOOK in n.meta["required_constraint_hooks"] and set(n.meta["research_phs_energy_caps"]) == {"ID", "LA", "MY", "MM", "VN", "PH", "TH"}
    assert n.meta["research_phs_energy_caps"]["ID"]["cap_mwh"] == 103e6
    # the hook is in the allowed list of the assembly
    src = (ROOT / "scripts_project/assembly_components.py").read_text(encoding="utf-8")
    assert "'research_phs_energy_cap'" in src and "install_phs_energy_cap" in src


def test_asean_table_conversion_and_registry_rows():
    t = pd.read_csv(ROOT / "research_inputs/potentials_v5/PHS_ASEAN_CASE_V4.csv", keep_default_na=False).set_index("country")
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    fx = float(reg.at["fx_usd_to_eur_2020", "value"])
    for c in ("ID", "LA", "MY", "MM", "VN", "PH", "TH"):
        assert float(t.at[c, "power_eur2020_per_kw"]) == pytest.approx(560.0 * fx) and float(t.at[c, "energy_eur2020_per_kwh"]) == pytest.approx(50.0 * fx)
        assert float(reg.at[f"phs_asean_energy_cap_{c}", "value"]) == pytest.approx(float(t.at[c, "anu_shortlist_twh"]) * 1e6) and reg.at[f"phs_asean_energy_cap_{c}", "status"] == "SENSITIVITY"
    assert float(reg.at["phs_asean_power_cost_eur2020_per_kw", "value"]) == pytest.approx(560.0 * fx) and reg.at["phs_asean_power_cost_eur2020_per_kw", "status"] == "SENSITIVITY"
    assert float(reg.at["v4_phs_stock_bhumibol_conventional_mw", "value"]) == 608.2 and float(reg.at["v4_phs_stock_th_pumped_total_mw", "value"]) == 1531.0
    from v4_common import sha256
    for pid in ("v4_phs_stock_reclass_table", "v4_phs_asean_case_table", "v4_palm_residue_basis_table", "v4_biomass_potential_2050_t04"):
        p = ROOT / reg.at[pid, "source_locator"][len("file: "):]
        assert sha256(p) == reg.at[pid, "source_sha256"], pid
