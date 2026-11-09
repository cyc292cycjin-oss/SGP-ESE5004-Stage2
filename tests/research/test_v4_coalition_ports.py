"""V4 W20b (decision 230): include_bunker="ports" of scripts_project/v4_coalition.py - the bunker player split by bunkering port into sub-players
B_i (the bunker loads on the port / airport nodes of country i) merged into country i. No solver.

V4_W20B_INSTRUCTION.md section 2.2:
(a) all 11 countries + "ports" -> component-identical to the W14 package integrated network, 2920x3h and 56 snapshots;
(b) include_bunker=False: the 17 W20 networks are rebuilt byte-identically (SHA256 registered by W20, evidence/STATIC_CHECKS_W20.json);
(c) every "ports" coalition: the countries of the bunker-load nodes are a subset of the members, and every bunker load at a member node is kept
    with its energy identical to the full network (per load and snapshot);
(d) the bunker account connects only (and all) metering links of member nodes, with its hook; the account premises hold.
Toy tests always run; the real-network tests are skipped when the git-ignored inputs are absent and FAIL when a file differs.
The W20 test file (test_v4_coalition.py) is run unchanged next to this one (False / True behaviour unchanged).
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
import pypsa  # noqa: E402

import v4_coalition as V  # noqa: E402

_spec = importlib.util.spec_from_file_location("w20_coalition_tests", Path(__file__).with_name("test_v4_coalition.py"))
_w20 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_w20)
toy = _w20.toy   # the W20 toy network (ID - MY - SG, bunker at ID1 and SG1)

MAIN = Path(os.environ.get("W20_MAIN_CHECKOUT", "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"))
BASE_2920 = Path(os.environ.get("W20_BASE_2920", MAIN / "results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc"))
BASE_56 = Path(os.environ.get("W20_BASE_56", MAIN / "results_project/v4w14/trunc56/w14_integrated_56.nc"))
SHA_2920 = "86f6d6a0fce2f0e04d12ee7993aee885256fcaadadaeeca308414017738c801d"
W20_STATIC = ROOT / "research/06_scope_redesign/p1_v4_w20_20261109/evidence/STATIC_CHECKS_W20.json"
W20_NETS = MAIN / "results_project/v4w20/nets56"
ACC = V.BUNKER_STORE


# ----------------------------------------------------------------------------------------------------------------------------- toy
def test_bunker_mode_values():
    assert V.bunker_mode(False) == "none" and V.bunker_mode(None) == "none" and V.bunker_mode(True) == "all" and V.bunker_mode("ports") == "ports"
    assert V.bunker_mode(np.bool_(True)) == "all" and V.bunker_mode(np.bool_(False)) == "none"
    for bad in ("harbour", "True", 1.5, "PORTS"):
        with pytest.raises(ValueError):
            V.bunker_mode(bad)


def test_w20b_runs():
    R = V.w20b_runs()
    assert list(R) == V.W20B_ORDER == ["R0"] + V.COALITION_ORDER and len(R) == 18
    assert R["R0"] == dict(members=tuple(V.COUNTRIES), include_bunker=False, net="R0_noBunker")
    for k in V.COALITION_ORDER:
        assert R[k] == dict(members=V.coalitions()[k], include_bunker="ports", net=f"{k}_ports")


def test_toy_ports_full_is_identity():
    n0 = toy(); n, led = V.coalition_subnetwork(n0, V.COUNTRIES, include_bunker="ports")
    d = V.network_diff(n0, n)
    assert d["identical"], d
    rc = n.meta["research_coalition"]
    assert rc["include_bunker"] == "ports" and rc["rules_version"] == "W20b-v1" and rc["decision"] == "230"
    assert led["bunker"]["mode"] == "ports" and led["bunker"]["loads_kept"] == 2 and led["bunker"]["terminal_buses_removed"] == 0


def test_toy_ports_subset_follows_the_ports():
    n, led = V.coalition_subnetwork(toy(), ["ID", "MY"], include_bunker="ports")
    assert "ID1 aviation international oil final" in n.buses.index and "SG1 aviation international oil final" not in n.buses.index
    assert "ID1 aviation international oil demand" in n.loads.index and "SG1 aviation international oil demand" not in n.loads.index
    assert ACC in n.stores.index and "research_bunker_net_zero" in n.meta["required_constraint_hooks"]
    assert [p["link"] for p in n.meta["research_bunkers"]["account"]["ports"]] == ["ID1 aviation international oil meter"]
    assert list(n.meta["research_bunkers"]["asean_loads"]) == ["ID1 aviation international oil demand"]
    B = led["bunker"]
    assert B["mode"] == "ports" and B["loads_kept"] == 1 and B["loads_removed"] == 1 and B["metering_links_kept"] == 1 and B["account_kept"]
    assert B["energy_mwh_kept_by_country"] == {"ID": 8.0} and B["energy_mwh_removed"] == 8.0   # 2 MW x 4 snapshots x weight 1
    assert led["removed_by_rule"]["R3_bunker"] == {"Bus": 1, "Load": 1, "Link": 1}
    # same components as the W20 node rule (include_bunker=True on a subset); only the coalition metadata differs
    t, _ = V.coalition_subnetwork(toy(), ["ID", "MY"], include_bunker=True)
    d = V.network_diff(t, n)
    assert d["identical"], d
    assert t.meta["research_coalition"]["include_bunker"] is True and t.meta["research_coalition"]["rules_version"] == "W20-v1"


def test_toy_ports_member_without_bunker_drops_the_account():
    n, led = V.coalition_subnetwork(toy(), ["MY"], include_bunker="ports")
    assert not (n.buses.country == "ASEAN").any() and ACC not in n.stores.index
    assert "research_bunker_net_zero" not in n.meta["required_constraint_hooks"] and "research_bunkers" not in n.meta
    assert led["bunker"]["removed"] is True and led["bunker"]["mode"] == "ports" and led["bunker"]["loads_kept"] == 0


def test_toy_ports_refusals():
    t = toy(); t.buses.loc["ID1 aviation international oil final", "location"] = ""
    with pytest.raises(ValueError):                         # a bunker bus without a port / airport node of a country
        V.coalition_subnetwork(t, ["ID", "MY"], include_bunker="ports")
    with pytest.raises(ValueError):
        V.coalition_subnetwork(toy(), ["ID", "MY"], include_bunker="harbour")
    t = toy(); t.mremove("Link", ["ID1 aviation international oil meter"])
    with pytest.raises(ValueError):                         # bunker load at a member node but no meter into the account
        V.coalition_subnetwork(t, ["ID", "MY"], include_bunker="ports")


def test_toy_false_and_true_unchanged_metadata():
    n, led = V.coalition_subnetwork(toy(), ["ID", "MY"])
    rc = n.meta["research_coalition"]
    assert rc["include_bunker"] is False and rc["rules_version"] == "W20-v1" and rc["decision"] == "228" and led["bunker"]["removed"] is True
    assert "mode" in led["bunker"] and led["bunker"]["mode"] == "asean_account_nodal"   # the W20 ledger keeps research_bunkers.mode here


# ------------------------------------------------------------------------------------------------------------------- real networks
def _need(p: Path):
    if not p.is_file():
        pytest.skip(f"{p} not present (git-ignored results)")


@pytest.fixture(scope="module")
def base56():
    _need(BASE_56)
    return pypsa.Network(str(BASE_56))


def _port_country(n0):
    bc = n0.buses.country.astype(str); loc = n0.buses.location.astype(str)
    return {b: str(bc[loc[b]]) for b in n0.buses.index[bc == "ASEAN"] if b != ACC}


def test_a_ports_identity_2920():
    _need(BASE_2920)
    assert V.sha(BASE_2920) == SHA_2920
    n0 = pypsa.Network(str(BASE_2920)); n = pypsa.Network(str(BASE_2920))
    n, led = V.coalition_subnetwork(n, V.COUNTRIES, include_bunker="ports", inplace=True)
    d = V.network_diff(n0, n)
    assert d["identical"], d
    assert led["removed_total"] == {} and led["bunker"]["loads_kept"] == 130 and led["bunker"]["metering_links_kept"] == 82
    assert led["bunker"]["terminal_buses_removed"] == 0 and led["bunker"]["account_kept"]


def test_a_ports_identity_56(base56):
    _need(BASE_2920)
    n = pypsa.Network(str(BASE_2920)); n, _ = V.coalition_subnetwork(n, V.COUNTRIES, include_bunker="ports", inplace=True); V.cut(n, 56)
    d = V.network_diff(base56, n)          # the W14 cut56 file of the same network
    assert d["identical"], d
    m, _ = V.coalition_subnetwork(base56, V.COUNTRIES, include_bunker="ports")
    d = V.network_diff(base56, m)
    assert d["identical"], d


def _w20_registered() -> dict:
    if not W20_STATIC.is_file():
        pytest.skip(f"{W20_STATIC} not present")
    return {k: v["network_sha256"] for k, v in json.loads(W20_STATIC.read_text())["networks"].items()}


@pytest.mark.parametrize("name", V.COALITION_ORDER)
def test_b_false_networks_byte_identical_to_w20(tmp_path, name):
    _need(BASE_2920)
    reg = _w20_registered()
    env = dict(os.environ, PYTHONHASHSEED="0")
    r = subprocess.run([sys.executable, str(ROOT / "scripts_project/v4_coalition.py"), "build", "--base", str(BASE_2920), "--coalition", name, "--out", str(tmp_path),
                        "--truncate", "56", "--expect-base-sha256", SHA_2920[:16]], capture_output=True, text=True, env=env, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-2000:]
    got = V.sha(tmp_path / f"{name}_56_unsolved.nc")
    assert got == reg[name], (name, got, reg[name])
    w20_file = W20_NETS / f"{name}_56_unsolved.nc"
    if w20_file.is_file():
        assert V.sha(w20_file) == reg[name]


@pytest.mark.parametrize("name", V.COALITION_ORDER)
def test_c_d_ports_coalition(base56, name):
    S = set(V.coalitions()[name]); pc = _port_country(base56)
    n, led = V.coalition_subnetwork(base56, sorted(S), include_bunker="ports")
    bc = n.buses.country.astype(str)
    term = {b for b in n.buses.index[bc == "ASEAN"] if b != ACC}
    # (c) bunker loads: node countries within the members; every load at a member node kept, energy identical per load and snapshot
    ld = n.loads.index[n.loads.bus.astype(str).isin(term)]
    assert {pc[str(n.loads.at[x, "bus"])] for x in ld} <= S, "(c) bunker load at a non-member node"
    base_ld = [x for x in base56.loads.index if str(base56.loads.at[x, "bus"]) in pc]
    want = sorted(x for x in base_ld if pc[str(base56.loads.at[x, "bus"])] in S)
    assert sorted(ld) == want, "(c) bunker loads at member nodes differ"
    p0 = base56.get_switchable_as_dense("Load", "p_set")[want]; p1 = n.get_switchable_as_dense("Load", "p_set")[want]
    assert np.array_equal(p0.to_numpy(), p1.to_numpy()) and (p0.index == p1.index).all(), "(c) bunker load profiles differ"
    w = base56.snapshot_weightings.generators
    assert np.array_equal(base56.snapshot_weightings.to_numpy(), n.snapshot_weightings.to_numpy())
    e = p0.mul(w, axis=0).sum()
    byc = {}
    for x in want:
        byc[pc[str(base56.loads.at[x, "bus"])]] = byc.get(pc[str(base56.loads.at[x, "bus"])], 0.0) + float(e[x])
    got = led["bunker"]["energy_mwh_kept_by_country"]
    assert set(got) == set(byc) and all(abs(got[c] - byc[c]) <= 1e-9 * max(1.0, byc[c]) for c in byc), "(c) energy by country"
    assert set(byc) == {pc[str(base56.loads.at[x, "bus"])] for x in base_ld} & S
    # (d) the account connects exactly the metering links of member nodes, each fed from a member; hook and premises
    P = V.port_columns(n.links)
    acc_links = set(n.links.index[n.links[P].astype(str).eq(ACC).any(axis=1)])
    base_meters = set(base56.links.index[base56.links[V.port_columns(base56.links)].astype(str).eq(ACC).any(axis=1)])
    want_m = {x for x in base_meters if pc[str(base56.links.at[x, "bus1"])] in S}
    assert acc_links == want_m and len(want_m) > 0, "(d) metering links on the account differ"
    for x in acc_links:
        assert str(n.links.at[x, "bus2"]) == ACC and bc[str(n.links.at[x, "bus0"])] in S and pc[str(n.links.at[x, "bus1"])] in S, f"(d) {x}"
    assert {p["link"] for p in n.meta["research_bunkers"]["account"]["ports"]} == acc_links
    assert "research_bunker_net_zero" in n.meta["required_constraint_hooks"] and ACC in n.stores.index
    from s4c_layers import validate_bunker_account
    acc = validate_bunker_account(n)                          # account contract + V3.1 premises (raises on failure)
    assert {p["link"] for p in acc["ports"]} == acc_links
    # supply links of the kept terminals: from member national liquid buses only; none of the removed terminals' links left
    sup = n.links[n.links[P].astype(str).isin(term).any(axis=1)]
    assert {bc[str(b)] for b in sup.bus0} <= S
    assert set(n.meta["research_bunkers"]["by_country"]) == S & set(base56.meta["research_bunkers"]["by_country"])
    rc = n.meta["research_coalition"]
    assert rc["include_bunker"] == "ports" and rc["rules_version"] == "W20b-v1" and rc["members"] == sorted(S)


def test_ports_vs_true_same_components_real(base56):
    a, _ = V.coalition_subnetwork(base56, V.coalitions()["LTMS"], include_bunker=True)
    b, _ = V.coalition_subnetwork(base56, V.coalitions()["LTMS"], include_bunker="ports")
    d = V.network_diff(a, b, ignore_meta=("research_coalition", "research_bunkers"))
    assert d["identical"], d
