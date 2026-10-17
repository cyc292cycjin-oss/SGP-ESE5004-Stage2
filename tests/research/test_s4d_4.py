"""S4D-4 (decision 91b): coalition switch research.cross_border.coalition."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4d_layers import coalition_members, connected_coalitions  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
B = ROOT / "results_project/s4d/s4d4/builds"
ALL = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]


def test_members():
    sw = dict(electricity=True, H2=True, gas=True, co2=True, coalition=None)
    assert coalition_members(sw) is None and "coalition" not in CFG["research"]["cross_border"]   # absent key = no effect (switch metadata of older networks unchanged)
    assert coalition_members(dict(electricity=True, H2=True, gas=True, co2=True)) is None
    assert coalition_members(dict(sw, coalition=["my", "SG"])) == {"MY", "SG"} and coalition_members(dict(sw, coalition=[])) == set()
    with pytest.raises(ValueError):
        coalition_members(dict(sw, coalition=["MY", "XX"]))
    with pytest.raises(ValueError):
        coalition_members(dict(sw, coalition="MY,SG"))
    with pytest.raises(ValueError):
        coalition_members(dict(sw, electricity=False, coalition=["MY", "SG"]))   # defined on top of the integrated switches


def test_override_parsing():
    # the build and gate B12 parse list / null overrides with yaml (s2_network.build_scenario_s2, v5_gates.gate_b12_hash)
    from v5.v5_gates import gate_b12_hash  # noqa: F401  (import check: the module loads with the new parser)
    assert yaml.safe_load("[MY,SG]") == ["MY", "SG"] and yaml.safe_load("[]") == [] and yaml.safe_load("null") is None
    src = (ROOT / "scripts_project/s2_network.py").read_text()
    assert "old is None or isinstance(old, (list, dict))" in src and 'NEW_OVERRIDE_KEYS = ("cross_border.coalition",' in src
    g = (ROOT / "scripts_project/v5/v5_gates.py").read_text()
    assert "old is None or isinstance(old,(list,dict))" in g and "key not in ('cross_border.coalition'," in g


def test_connected_coalitions_toy():
    r = connected_coalitions({("A", "B"), ("B", "C")}, ["A", "B", "C", "D"])
    # singletons 4; pairs AB, BC; triple ABC -> 7 connected, 3 with two or more members
    assert r["total"] == 7 and r["with_two_or_more"] == 3 and r["by_size"] == {1: 4, 2: 2, 3: 1}


present = all((B / t).exists() for t in ("integrated", "disconnected", "coal_all11", "coal_empty", "coal_MY_SG", "coal_LA_TH"))


def _net(tag):
    import pypsa
    sc = "disconnected" if tag == "disconnected" else "integrated"
    return pypsa.Network(str(B / tag / f"{sc}_2920_3h_unsolved.nc"))


def _same(a, b):
    for c in ("Bus", "Link", "Store", "Generator", "Load", "StorageUnit", "Line"):
        x, y = a.df(c).sort_index(), b.df(c).sort_index()
        if set(x.index) != set(y.index):
            return False
        cols = sorted((set(x.columns) | set(y.columns)) - {"border_class"} if c == "Bus" else set(x.columns) | set(y.columns))
        if not x.reindex(columns=cols).equals(y.reindex(columns=cols)):
            return False
    return True


@pytest.mark.skipif(not present, reason="S4D-4 builds not present")
def test_builds():
    i, d = _net("integrated"), _net("disconnected")
    assert _same(_net("coal_all11"), i) and _same(_net("coal_empty"), d)
    for tag, mem in (("coal_MY_SG", {"MY", "SG"}), ("coal_LA_TH", {"LA", "TH"})):
        n = _net(tag)
        for typ in ("Line", "Link"):
            x = n.df(typ)[n.df(typ).border_class == "cross_border"]
            assert len(x) and all({n.buses.at[z.bus0, "country"], n.buses.at[z.bus1, "country"]} == mem for _, z in x.iterrows()) or typ == "Line" and tag == "coal_MY_SG"
        assert (n.links.carrier == "CO2 ship").sum() == 504   # maritime trade unaffected
        assert n.meta["research_cross_border"]["ledger"]["coalition"]["members"] == sorted(mem)
