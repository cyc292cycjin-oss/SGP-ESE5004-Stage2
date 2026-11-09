"""V4 W20 (decision 228): coalition subnetworks (scripts_project/v4_coalition.py). No solver.

Toy tests always run. The real-network tests (instruction 2.3 (a)-(c)) read the W14 v4 main integrated network (SHA256 86f6d6a0..., package
hpc_package_v4/networks) and its 56-snapshot cut; they are skipped when the files are absent (fresh worktree) and FAIL when the file differs.
(a) members = all 11, include_bunker=True -> component-identical to the input (2920x3h and 56); building then cutting = cutting then building;
(b) every leave-one-out network holds no component, no boundary branch, no liquid bus / ship of the removed country, every category of decision
133 (2)a covered (attribution re-derived here from the BASE bus -> country map, independent of the module);
(c) the three bloc networks: country set and retained stock cross-border facilities (re-derived independently, and country pairs within the
geographic expectation); (d) the main build path does not import the module (the A2 fallback tests are run separately, instruction 2.3 (d)).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
import pypsa  # noqa: E402

import v4_coalition as V  # noqa: E402

MAIN = Path(os.environ.get("W20_MAIN_CHECKOUT", "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"))
BASE_2920 = Path(os.environ.get("W20_BASE_2920", MAIN / "results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc"))
BASE_56 = Path(os.environ.get("W20_BASE_56", MAIN / "results_project/v4w14/trunc56/w14_integrated_56.nc"))
SHA_2920 = "86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d"
LIQ = ("oil", "oil non-fossil", "methanol", "ammonia")


# ----------------------------------------------------------------------------------------------------------------------------- toy
def toy():
    """ID - MY - SG, AC lines ID1-MY1 (stock) and MY1-SG1 (candidate), a DC link MY-SG with a member-side converter, national liquid buses with
    ships, atmospheres, a CO2 store, a Lao-style transit link of ID via a SG coastal node, the bunker player at ID1 and SG1."""
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=4, freq="3h"))
    def bus(name, carrier, c, loc=""):
        n.add("Bus", name, carrier=carrier); n.buses.loc[name, "country"] = c; n.buses.loc[name, "location"] = loc
    for c in ("ID", "MY", "SG"):
        bus(f"{c}1", "AC", c, f"{c}1"); bus(f"{c} oil", "oil", c); bus(f"co2 atmosphere {c}", "co2 atmosphere", c)
        n.add("Store", f"co2 atmosphere {c}", bus=f"co2 atmosphere {c}", carrier="co2 atmosphere", e_nom_extendable=True, e_min_pu=-1)
        n.add("Load", f"{c}1 electricity", bus=f"{c}1", carrier="electricity", p_set=10.0); n.loads.loc[f"{c}1 electricity", "country"] = c
        n.add("Generator", f"{c}1 solar", bus=f"{c}1", carrier="solar", p_nom_extendable=True, capital_cost=1.0)
        n.add("Generator", f"{c} oil import", bus=f"{c} oil", carrier="oil", p_nom_extendable=True, marginal_cost=50.0)
        n.add("Link", f"oil pool {c}1", bus0=f"{c} oil", bus1=f"{c}1", carrier="oil pool", p_nom_extendable=True, p_min_pu=-1)
        n.links.loc[f"oil pool {c}1", "country"] = c
    bus("co2 sequestered MY", "co2 sequestered", "MY")
    n.add("Store", "co2 sequestered MY", bus="co2 sequestered MY", carrier="co2 sequestered", e_nom_extendable=True)
    bus("SG2 DC", "DC", "SG", "SG2"); bus("SG2", "AC", "SG", "SG2"); bus("MY2 DC", "DC", "MY", "MY2")
    n.add("Load", "SG2 electricity", bus="SG2", carrier="electricity", p_set=1.0); n.loads.loc["SG2 electricity", "country"] = "SG"
    n.add("Line", "L stock", bus0="ID1", bus1="MY1", carrier="AC", s_nom=100.0, s_nom_extendable=True, x=0.1, r=0.01)
    n.add("Line", "L cand", bus0="MY1", bus1="SG1", carrier="AC", s_nom=0.0, s_nom_extendable=True, x=0.1, r=0.01)
    n.add("Line", "L SG", bus0="SG1", bus1="SG2", carrier="AC", s_nom=50.0, x=0.1, r=0.01)
    n.add("Link", "DC MY-SG", bus0="MY2 DC", bus1="SG2 DC", carrier="DC", p_nom=10.0, p_nom_extendable=True)
    n.add("Link", "DC MY-SG-reversed", bus0="SG2 DC", bus1="MY2 DC", carrier="DC", p_nom=10.0, p_nom_extendable=True)
    n.add("Link", "convert MY2", bus0="MY2 DC", bus1="MY1", carrier="B2B", p_nom=20.0, capital_cost=3.0, p_min_pu=-1)
    n.add("Link", "convert SG2", bus0="SG2 DC", bus1="SG2", carrier="B2B", p_nom=20.0, capital_cost=3.0, p_min_pu=-1)
    n.links["reversed"] = False; n.links.loc["DC MY-SG-reversed", "reversed"] = True
    for a, b in (("ID", "MY"), ("MY", "SG"), ("SG", "ID")):
        k = f"{a} oil ship to {b}"; n.add("Link", k, bus0=f"{a} oil", bus1=f"{b} oil", carrier="oil ship", p_nom=1e6); n.links.loc[k, "country"] = a
    n.add("Link", "ID1 co2 transit ship to MY", bus0="ID1", bus1="co2 sequestered MY", carrier="CO2 transit ship", p_nom_extendable=True)
    n.links.loc["ID1 co2 transit ship to MY", ["country", "via_coastal_node"]] = ["ID", "SG1"]
    bus("co2 bunkers ASEAN", "co2 bunkers", "ASEAN", "")
    n.add("Store", "co2 bunkers ASEAN", bus="co2 bunkers ASEAN", carrier="co2 bunkers", e_nom_extendable=True); n.stores.loc["co2 bunkers ASEAN", "country"] = "ASEAN"
    for c in ("ID", "SG"):
        f = f"{c}1 aviation international oil final"; bus(f, "oil final energy", "ASEAN", f"{c}1")
        n.add("Load", f"{c}1 aviation international oil demand", bus=f, carrier="oil final energy", p_set=2.0); n.loads.loc[f"{c}1 aviation international oil demand", "country"] = "ASEAN"
        k = f"{c}1 aviation international oil meter"
        n.add("Link", k, bus0=f"{c} oil", bus1=f, bus2="co2 bunkers ASEAN", efficiency2=0.26, carrier="oil final-energy accounting", p_nom_extendable=True)
        n.links.loc[k, "country"] = c
    for c in ("ID", "SG"):
        k = f"{c}1 existing fossil"
        n.add("Link", k, bus0=f"{c} oil", bus1=f"{c}1", bus2=f"co2 atmosphere {c}", efficiency2=0.27, carrier="oil existing", p_nom=5.0)
        n.links.loc[k, ["country", "asset_role", "existing_annual_fixed_om_eur"]] = [c, "existing_survivor", 7.0 if c == "ID" else 11.0]
    n.madd("Carrier", ["AC", "DC", "B2B", "oil", "oil pool", "oil ship", "solar", "electricity", "co2 atmosphere", "co2 sequestered", "CO2 transit ship", "co2 bunkers",
                      "oil final energy", "oil final-energy accounting", "oil existing", "unused already"])
    n.meta.update(scenario="integrated", required_constraint_hooks=["research_bunker_net_zero", "research_country_net_zero", "research_existing_assets",
                                                                    "research_cross_border_existing_fom"],
                  research_bunkers=dict(mode="asean_account_nodal", account=dict(present=True, store="co2 bunkers ASEAN",
                                        ports=[dict(link=f"{c}1 aviation international oil meter", port="bus2") for c in ("ID", "SG")]),
                                        asean_loads={f"{c}1 aviation international oil demand": dict(bus=f"{c}1 aviation international oil final") for c in ("ID", "SG")}),
                  research_carbon=dict(constraint_scope="per_country", country_cap_tco2={c: 0.0 for c in V.COUNTRIES}),
                  research_co2_storage=dict(caps_t_per_year={c: (5.0 if c == "MY" else 0.0) for c in V.COUNTRIES}),
                  existing_unit_components={"U1": dict(component_type="Link", component="ID1 existing fossil"), "U2": dict(component_type="Link", component="SG1 existing fossil")},
                  existing_annual_fixed_om_eur=18.0,
                  existing_cross_border_fom_ledger=[dict(component_type="Line", component="L stock", annual_fom_eur=4.0), dict(component_type="Link", component="DC MY-SG", annual_fom_eur=2.0)],
                  existing_cross_border_fom_eur=6.0, store_power_rules={"co2 sequestered MY": "charge_only"},
                  demand_owners={x: x for x in n.loads.index}, demand_identity={x: dict(country=str(n.loads.at[x, "country"])) for x in n.loads.index})
    return n


def test_toy_full_with_bunker_is_identity():
    n0 = toy(); n, led = V.coalition_subnetwork(n0, V.COUNTRIES, include_bunker=True)
    d = V.network_diff(n0, n)
    assert d["identical"], d
    assert led["full_coalition"] and not any(led["removed_by_rule"].get(r) for r in led["removed_by_rule"]) and n.meta["research_coalition"]["members"] == list(V.COUNTRIES)
    assert "research_coalition" not in n0.meta   # the input is not changed (inplace=False)


def test_toy_coalition_rules_and_metadata():
    n, led = V.coalition_subnetwork(toy(), ["ID", "MY"])
    assert set(n.buses.country) == {"ID", "MY"}
    R = led["removed_by_rule"]
    assert R["R1_bus_country"]["Bus"] == 5 and R["R2_boundary"] == {"Line": 1, "Link": 4}
    assert {"SG1", "SG2", "SG oil", "SG2 DC", "co2 atmosphere SG"} & set(n.buses.index) == set()
    assert "L cand" not in n.lines.index and "L stock" in n.lines.index and "L SG" not in n.lines.index
    assert {"DC MY-SG", "DC MY-SG-reversed", "MY oil ship to SG", "SG oil ship to ID"} & set(n.links.index) == set()
    assert "ID oil ship to MY" in n.links.index
    b = {r["component"] for r in led["boundary_components"]}
    assert {"L cand", "DC MY-SG", "DC MY-SG-reversed", "MY oil ship to SG", "SG oil ship to ID"} == b
    assert "convert SG2" not in n.links.index and "L SG" not in n.lines.index                      # SG internal facilities: R1
    # the member-side converter of the removed DC link is a new dead end: kept and listed with its fixed cost (3 x 20)
    assert "convert MY2" in n.links.index and "MY2 DC" in n.buses.index
    assert [(r["bus"], r["component"], r["fixed_cost_constant_eur"]) for r in led["dead_end_member_components_kept"]] == [("MY2 DC", "convert MY2", 60.0)]
    # the bunker player leaves with its hook and metadata
    assert not (n.buses.country == "ASEAN").any() and "co2 bunkers ASEAN" not in n.stores.index and "ID1 aviation international oil meter" not in n.links.index
    assert "research_bunker_net_zero" not in n.meta["required_constraint_hooks"] and "research_bunkers" not in n.meta
    assert R["R3_bunker"]["Load"] == 2 and R["R3_bunker"]["Bus"] == 3
    # transit through a non-member: kept (port rule) and listed
    assert "ID1 co2 transit ship to MY" in n.links.index and [r["component"] for r in led["transit_via_non_member"]] == ["ID1 co2 transit ship to MY"]
    # metadata of the hooks
    assert n.meta["research_countries"] == ["ID", "MY"]
    assert set(n.meta["research_carbon"]["country_cap_tco2"]) == {"ID", "MY"} and set(n.meta["research_co2_storage"]["caps_t_per_year"]) == {"ID", "MY"}
    assert list(n.meta["existing_unit_components"]) == ["U1"] and n.meta["existing_annual_fixed_om_eur"] == 7.0
    assert [r["component"] for r in n.meta["existing_cross_border_fom_ledger"]] == ["L stock"] and n.meta["existing_cross_border_fom_eur"] == 4.0
    assert led["existing_cross_border_fom_boundary_eur"] == 2.0 and led["d8_addback_eur"] == 1.0
    assert set(n.meta["demand_owners"]) == set(n.loads.index) == set(n.meta["demand_identity"])
    # clean-up: carriers that became unreferenced (not the one unreferenced in the base)
    assert led["carriers_removed"] == ["co2 bunkers", "oil final energy", "oil final-energy accounting"]
    assert "unused already" in n.carriers.index and "DC" in n.carriers.index   # unreferenced in the base: left; DC still on the member DC bus
    from carrier_architecture import network_countries
    assert network_countries(n) == {"ID", "MY"}


def test_toy_dangling_bus_removed():
    n0 = toy(); n0.add("Bus", "MY3 DC", carrier="DC"); n0.buses.loc["MY3 DC", ["country", "location"]] = ["MY", "MY3"]
    n0.add("Link", "DC MY3-SG2", bus0="MY3 DC", bus1="SG2 DC", carrier="DC", p_nom_extendable=True)
    n, led = V.coalition_subnetwork(n0, ["ID", "MY"])
    assert led["dangling_buses_removed"] == ["MY3 DC"] and "MY3 DC" not in n.buses.index


def test_toy_bunker_kept_on_a_subset_follows_the_nodes():
    n, led = V.coalition_subnetwork(toy(), ["ID", "MY"], include_bunker=True)
    assert "ID1 aviation international oil final" in n.buses.index and "SG1 aviation international oil final" not in n.buses.index
    assert "co2 bunkers ASEAN" in n.stores.index and "research_bunker_net_zero" in n.meta["required_constraint_hooks"]
    assert [p["link"] for p in n.meta["research_bunkers"]["account"]["ports"]] == ["ID1 aviation international oil meter"]
    assert list(n.meta["research_bunkers"]["asean_loads"]) == ["ID1 aviation international oil demand"]


def test_toy_refusals():
    with pytest.raises(ValueError):
        V.coalition_subnetwork(toy(), ["XX"])
    with pytest.raises(ValueError):
        V.coalition_subnetwork(toy(), [])
    n, _ = V.coalition_subnetwork(toy(), ["ID", "MY"])
    with pytest.raises(ValueError):
        V.coalition_subnetwork(n, ["ID"])
    t = toy(); t.meta["scenario"] = "disconnected"
    with pytest.raises(ValueError):
        V.coalition_subnetwork(t, ["ID"])


def test_coalition_list():
    C = V.coalitions()
    assert V.COALITION_ORDER[:6] == ["GMS", "LTMS", "BIMP", "nonGMS", "nonLTMS", "nonBIMP"] and len(V.COALITION_ORDER) == 17 == len(C)
    assert C["GMS"] == ("KH", "LA", "MM", "TH", "VN") and C["LTMS"] == ("LA", "MY", "SG", "TH") and C["BIMP"] == ("BN", "ID", "MY", "PH")
    assert C["nonGMS"] == ("BN", "ID", "MY", "PH", "SG", "TL") and C["nonLTMS"] == ("BN", "ID", "KH", "MM", "PH", "TL", "VN") and C["nonBIMP"] == ("KH", "LA", "MM", "SG", "TH", "TL", "VN")
    assert all(len(C["minus" + c]) == 10 and c not in C["minus" + c] for c in V.COUNTRIES)


# ------------------------------------------------------------------------------------------------------------------- real networks
def _need(p: Path):
    if not p.is_file():
        pytest.skip(f"{p} not present (git-ignored results)")


@pytest.fixture(scope="module")
def base56():
    _need(BASE_56)
    return pypsa.Network(str(BASE_56))


def _attr(n0):
    """independent attribution: component -> set of countries of its port buses in the BASE network."""
    bc = n0.buses.country.astype(str).to_dict(); out = {}
    for c in n0.iterate_components(["Load", "Generator", "Store", "StorageUnit", "Line", "Link"]):
        P = [x for x in c.df.columns if x == "bus" or (x.startswith("bus") and x[3:].isdigit())]
        for name, row in c.df[P].astype(str).iterrows():
            out[(c.name, name)] = {bc[b] for b in row if b in bc}
    return out


def test_a_identity_2920():
    _need(BASE_2920)
    assert V.sha(BASE_2920) == SHA_2920
    n0 = pypsa.Network(str(BASE_2920)); n = pypsa.Network(str(BASE_2920))
    n, led = V.coalition_subnetwork(n, V.COUNTRIES, include_bunker=True, inplace=True)
    d = V.network_diff(n0, n)
    assert d["identical"], d
    assert led["removed_total"] == {} and led["dead_end_member_components_kept"] == [] and led["transit_via_non_member"] == []


def test_a_identity_56_and_cut_commutes(base56):
    _need(BASE_2920)
    n = pypsa.Network(str(BASE_2920)); n, _ = V.coalition_subnetwork(n, V.COUNTRIES, include_bunker=True, inplace=True); V.cut(n, 56)
    d = V.network_diff(base56, n)   # the W14 cut56 file of the same network
    assert d["identical"], d
    a = pypsa.Network(str(BASE_2920)); a, _ = V.coalition_subnetwork(a, V.coalitions()["LTMS"], inplace=True); V.cut(a, 56)   # build, then cut
    b, _ = V.coalition_subnetwork(base56, V.coalitions()["LTMS"])                                                              # cut, then build
    d = V.network_diff(a, b)
    assert d["identical"], d


def test_a_full_without_bunker_removes_only_the_bunker(base56):
    n, led = V.coalition_subnetwork(base56, V.COUNTRIES)
    assert set(led["removed_by_rule"]) <= {"R3_bunker", "R5_cleanup"} and led["removed_by_rule"]["R3_bunker"]["Load"] == 130
    assert led["removed_by_rule"]["R3_bunker"]["Bus"] == int((base56.buses.country == "ASEAN").sum())
    assert n.meta["existing_annual_fixed_om_eur"] == base56.meta["existing_annual_fixed_om_eur"] and n.meta["existing_cross_border_fom_eur"] == base56.meta["existing_cross_border_fom_eur"]


@pytest.mark.parametrize("cc", V.COUNTRIES)
def test_b_leave_one_out(base56, cc):
    att = _attr(base56)
    n, led = V.coalition_subnetwork(base56, V.coalitions()["minus" + cc])
    assert cc not in set(n.buses.country.astype(str)) and "ASEAN" not in set(n.buses.country.astype(str))
    kept = {(c.name, x) for c in n.iterate_components(["Load", "Generator", "Store", "StorageUnit", "Line", "Link"]) for x in c.df.index}
    assert not [k for k in kept if cc in att[k]]                                     # no component with a port in the removed country
    assert not [k for k in kept if k[0] in ("Line", "Link") and not att[k] <= set(V.coalitions()["minus" + cc])]   # no boundary branch
    assert not [x for x in n.loads.index if str(n.loads.at[x, "country"]) in (cc, "ASEAN")]
    assert not ({f"{cc} {c}" for c in LIQ} & set(n.buses.index))                    # its national liquid buses
    ship = re.compile(rf"(^{cc} .* ship to )|( ship to {cc}$)|(transit to {cc}( |$))|(^{cc} .* transit to )")
    assert not [x for x in n.links.index if ship.search(x)]                          # its shipping / transit access
    assert not ({f"co2 atmosphere {cc}", f"co2 sequestered {cc}", f"co2 sequestered extra-ASEAN {cc}"} & set(n.stores.index))
    assert cc not in n.meta["research_countries"] and cc not in n.meta["research_carbon"]["country_cap_tco2"] and cc not in n.meta["research_co2_storage"]["caps_t_per_year"]
    # decision 133 (2)a categories: each one that the country has in the base is gone
    cat = {
        "demand": [("Load", x) for x in base56.loads.index],
        "resources_potentials": [("Generator", x) for x in base56.generators.index] + [("Store", x) for x in base56.stores.index[base56.stores.research_role.astype(str) == "FINITE_RESOURCE"]],
        "facilities_stock": [(t, x) for t in ("Generator", "Link", "StorageUnit") for x in base56.df(t).index[base56.df(t).asset_role.astype(str).str.startswith("existing")]],
        "facilities_candidates": [(t, x) for t in ("Generator", "Link", "StorageUnit", "Store") for x in base56.df(t).index[base56.df(t).asset_role.astype(str) == "new_build_candidate"]],
        "liquid_buses_shipping": [("Link", x) for x in base56.links.index[base56.links.research_role.astype(str) == "LIQUID_SHIPPING"]],
        "co2_shipping": [("Link", x) for x in base56.links.index[base56.links.research_role.astype(str).isin(["CO2_SHIPPING", "CO2_TRANSIT"])]],
        "pipelines": [("Link", x) for x in base56.links.index[base56.links.carrier.astype(str).str.endswith("pipeline")]],
        "lines": [("Line", x) for x in base56.lines.index] + [("Link", x) for x in base56.links.index[base56.links.carrier.isin(["DC", "dedicated plant line"])]],
    }
    covered = {}
    for k, items in cat.items():
        mine = [i for i in items if cc in att[i]]
        covered[k] = len(mine)
        assert not (set(mine) & kept), (k, sorted(set(mine) & kept)[:3])
    assert covered["demand"] > 0 and covered["resources_potentials"] > 0 and covered["liquid_buses_shipping"] > 0 and covered["co2_shipping"] > 0
    xb = {(r["component_type"], r["component"]) for r in n.meta["existing_cross_border_fom_ledger"]}
    assert not [k for k in xb if cc in att[k]]


EXPECTED_PAIRS = {"GMS": {"KH|LA", "KH|TH", "KH|VN", "LA|MM", "LA|TH", "LA|VN", "MM|TH", "MM|VN", "TH|VN"},   # land / sea neighbours within the bloc
                  "LTMS": {"LA|TH", "MY|TH", "MY|SG", "SG|TH"}, "BIMP": {"BN|MY", "ID|MY", "MY|PH", "BN|ID", "ID|PH", "BN|PH"}}


@pytest.mark.parametrize("bloc", ["GMS", "LTMS", "BIMP"])
def test_c_blocs(base56, bloc):
    S = set(V.coalitions()[bloc]); att = _attr(base56)
    n, led = V.coalition_subnetwork(base56, sorted(S))
    assert set(n.buses.country.astype(str)) == S and n.meta["research_countries"] == sorted(S)
    nom = {"Line": "s_nom", "Link": "p_nom"}
    phys = lambda t, x: t == "Line" or str(base56.links.at[x, "carrier"]) in ("DC", "dedicated plant line", "gas pipeline", "H2 pipeline", "CO2 pipeline")   # noqa: E731
    expect = sorted((t, x) for (t, x), cs in att.items() if t in ("Line", "Link") and len(cs) >= 2 and cs <= S and phys(t, x) and float(base56.df(t).at[x, nom[t]]) > 0)
    got = sorted((r["component_type"], r["component"]) for r in led["retained_cross_border_stock"])
    assert got == expect
    pairs = {"|".join(r["countries"]) for r in led["retained_cross_border_stock"]}
    assert pairs <= EXPECTED_PAIRS[bloc], pairs - EXPECTED_PAIRS[bloc]
    grid = {"|".join(r["countries"]) for r in led["retained_cross_border_stock"] if r["carrier"] in ("AC", "DC", "dedicated plant line")}
    want_grid = {"GMS": {"KH|LA", "KH|TH", "KH|VN", "LA|MM", "LA|TH", "LA|VN"}, "LTMS": {"LA|TH", "MY|TH", "MY|SG"}, "BIMP": {"ID|MY"}}[bloc]
    assert grid == want_grid, grid
    assert led["bunker"]["removed"] is True and "research_bunker_net_zero" not in n.meta["required_constraint_hooks"]


def test_cli_deterministic_and_receipt(tmp_path):
    _need(BASE_56)
    env = dict(os.environ, PYTHONHASHSEED="0")
    shas = []
    for k in ("a", "b"):
        r = subprocess.run([sys.executable, str(ROOT / "scripts_project/v4_coalition.py"), "build", "--base", str(BASE_56), "--coalition", "BIMP", "--out", str(tmp_path / k)],
                           capture_output=True, text=True, env=env, cwd=ROOT)
        assert r.returncode == 0, r.stderr[-2000:]
        shas.append(V.sha(tmp_path / k / "BIMP_56_unsolved.nc"))
        rec = json.loads((tmp_path / k / "BIMP_56_COALITION_RECEIPT.json").read_text())
        assert rec["solver_runs"] == 0 and rec["ledger"]["members"] == ["BN", "ID", "MY", "PH"]
    assert shas[0] == shas[1]


def test_d_main_build_path_does_not_import_the_module():
    for f in ("s2_network.py", "m08a_variants.py", "m08a_layers.py", "s2_solve.py", "build_research_assets.py", "scenario_network.py", "assembly_components.py"):
        assert "v4_coalition" not in (ROOT / "scripts_project" / f).read_text(), f
