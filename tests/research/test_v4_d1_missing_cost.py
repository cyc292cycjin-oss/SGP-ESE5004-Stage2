"""V4 D1 section 3 (decisions 212 item 5, 215 item 5): research.biomass.missing_cost_rule. proxy (v4 main): the five oil_palm_trunk Stores (registry cost
DATA_PENDING, empty cost column) get the registry proxy of unsourced residues; every other biomass Store keeps its cost; zero (v3.1): the unchanged v3.1
path (no ledger / meta entry, every Store cost = cost column or 0). The registry rule row equals the proxy rows. No solver, no network build (the
conversion links are skipped: no nodes)."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv"
TRUNK = {"ID", "KH", "MY", "PH", "TH"}


def _registry():
    return pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")


def _layer(csv: Path, missing, monkeypatch):
    import pypsa
    import s2_layers as L
    monkeypatch.setattr(L, "cost", lambda costs, tech, par: 1.0)   # no nodes -> no conversion link; the cost lookups are not used for the Stores
    n = pypsa.Network(); n.set_snapshots(range(2))
    led = L.add_biomass_layer(n, None, dict(biomass=dict(potential_layer="main", categories_excluded=["logging_residues"])), csv, [], 0.9, missing_cost=missing)
    return n, led


def test_rule_row_equals_the_proxy_rows():
    import s2_layers as L
    reg = _registry()
    row = reg.loc[L.MISSING_COST_PROXY_ID]
    peers = reg[reg.index.str.startswith("biomass_cost_") & reg.source.str.startswith(L.MISSING_COST_PROXY_SOURCE)]
    assert len(peers) == 32 and set(peers.value) == {row.value} and float(row.value) == pytest.approx(6.26706128163, abs=1e-11)
    assert row.status == "REGISTERED" and row.tier == "C" and "212 item 5" in row.decision_ref and "D (generic residue proxy" in row.description
    assert set(peers.sensitivity_low) == {row.sensitivity_low} and set(peers.sensitivity_high) == {row.sensitivity_high}
    pend = reg[reg.index.str.startswith("biomass_cost_") & (reg.status == "DATA_PENDING")]
    assert {p.split("_")[2] for p in pend.index} == TRUNK and all(p.endswith("_oil_palm_trunk") for p in pend.index)
    m = L.biomass_missing_cost(reg, "proxy")
    assert m["proxy_eur_per_mwh"] == float(row.value) and m["peer_rows"] == 32
    assert L.biomass_missing_cost(reg, "zero") is None
    with pytest.raises(ValueError):
        L.biomass_missing_cost(reg, "other")
    bad = reg.copy(); bad.at[L.MISSING_COST_PROXY_ID, "value"] = "7.0"
    with pytest.raises(ValueError):
        L.biomass_missing_cost(bad, "proxy")


@pytest.mark.parametrize("table", ["BIOMASS_POTENTIAL_2050.csv", "BIOMASS_POTENTIAL_2050_V4.csv"])
def test_proxy_only_on_the_trunk_pools_and_zero_is_v31(table, monkeypatch):
    import s2_layers as L
    csv = ROOT / "research_inputs/biomass_v5" / table
    reg = _registry()
    n0, led0 = _layer(csv, L.biomass_missing_cost(reg, "zero"), monkeypatch)
    n1, led1 = _layer(csv, L.biomass_missing_cost(reg, "proxy"), monkeypatch)
    # zero = the v3.1 path: cost column or 0, no record of the rule
    df = pd.read_csv(csv, keep_default_na=False).set_index(["country", "category"])
    for name, s in n0.stores.iterrows():
        c, cat = name.split(" biomass ")
        v = df.at[(c, cat), "cost_eur2020_per_mwh"]
        assert s.marginal_cost == (float(v) if v != "" else 0.0), name
    assert "missing_cost_rule" not in led0 and "missing_cost_rule" not in n0.meta["research_biomass"]
    # proxy: the five trunk Stores only
    proxy = float(reg.at[L.MISSING_COST_PROXY_ID, "value"])
    trunk = {f"{c} biomass oil_palm_trunk" for c in TRUNK}
    assert trunk <= set(n1.stores.index) and set(n1.stores.index) == set(n0.stores.index)
    diff = n1.stores.marginal_cost != n0.stores.marginal_cost
    assert set(n1.stores.index[diff]) == trunk
    assert (n1.stores.loc[sorted(trunk), "marginal_cost"] == proxy).all() and (n0.stores.loc[sorted(trunk), "marginal_cost"] == 0.0).all()
    other = n1.stores.drop(index=sorted(trunk))
    pd.testing.assert_frame_equal(other, n0.stores.drop(index=sorted(trunk)))
    pd.testing.assert_series_equal(n1.stores.e_nom, n0.stores.e_nom)
    mcl = led1["missing_cost_rule"]
    assert n1.meta["research_biomass"]["missing_cost_rule"] == mcl and {x["store"] for x in mcl["stores"]} == trunk and mcl["proxy_eur_per_mwh"] == proxy
    # zero-cost pools registered as 0 with a source (biogas MSW / POME) keep 0 under proxy
    reg0 = [i for i in n1.stores.index if ("msw_organic_biogas" in i or "oil_palm_pome" in i)]
    assert reg0 and (n1.stores.loc[reg0, "marginal_cost"] == 0.0).all()


def test_build_reads_the_switch(monkeypatch):
    from phase4_static import config
    from v4_common import switches
    cfg = config(ROOT, "integrated")
    assert switches(cfg)["missing_cost_rule"] == "zero"
    cfg["research"]["demand"]["v4"]["enabled"] = True
    assert switches(cfg)["missing_cost_rule"] == "proxy"
    src = (ROOT / "scripts_project/s2_network.py").read_text()
    assert 'missing_cost=biomass_missing_cost(registry, v4_switches(cfg)["missing_cost_rule"])' in src
