"""S4E-1 (decision 94): adjacent cross-border corridor completion."""
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
from s4e_layers import corridor_mode, corridor_tables  # noqa: E402

C = ROOT / "research_inputs/corridors"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
B = ROOT / "results_project/s4e/build_s4e1"


def test_adjacency_table():
    a = pd.read_csv(C / "ADJACENCY_S4E1.csv")
    assert int(a.adjacent.sum()) == 49 and a[a.adjacent].shared_border_km.min() >= 1.0
    assert not ((a.shared_border_km > 0) & (a.shared_border_km < 1.0)).any()   # no unclear contact
    assert (a.action == "new candidate").sum() == 31 and (a.action == "existing corridor").sum() == 18
    pairs = {tuple(sorted((r.country_a, r.country_b))) for r in a[a.action == "new candidate"].itertuples()}
    assert {("BN", "MY"), ("ID", "MY"), ("ID", "TL")} <= pairs   # expected by the instruction
    assert (a.basis.str.len() > 0).all()


def test_corridor_tables():
    old = pd.read_csv(C / "cross_border_corridors.csv", float_precision="round_trip")
    new = pd.read_csv(C / "CORRIDORS_S4E1.csv", float_precision="round_trip")
    dom = pd.read_csv(C / "DOMESTIC_CORRIDORS_S4E1.csv")
    assert len(new) == len(old) + 34
    pd.testing.assert_frame_equal(new.iloc[: len(old)].reset_index(drop=True), old, check_dtype=False)   # 2025 stock rows unchanged
    add = new.iloc[len(old):]
    assert (add.capacity_2025_mw == 0).all() and (add.country_from != add.country_to).all()
    assert (add.component_type == "Line").sum() == 31 and (add[add.component_type == "Line"].subsea_share == 0).all()
    dc = add[add.component_type == "Link"]
    assert len(dc) == 3 and set(dc.carrier) == {"DC"} and all(s.startswith(("APG4 ", "APG7 ", "APG16 ")) for s in dc.component)
    assert len(dom) == 3 and (dom.country_from == dom.country_to).all() and set(dom.component.str.split().str[0]) == {"APG3", "APG18a", "APG18b"}
    assert (new.length_km > 0).all()


def test_subsea_superset():
    s1 = pd.read_csv(C / "SUBSEA_SHARE_S4C1.csv"); s2 = pd.read_csv(C / "SUBSEA_SHARE_S4E1.csv")
    k = ["loc0", "loc1"]
    m = s1.merge(s2, on=k, suffixes=("", "_new"))
    assert len(m) == len(s1) and (m.share_landmass_nonland == m.share_landmass_nonland_new).all()   # existing pairs unchanged
    new = pd.read_csv(C / "CORRIDORS_S4E1.csv").iloc[26:]; dom = pd.read_csv(C / "DOMESTIC_CORRIDORS_S4E1.csv")
    keys = set(zip(s2.loc0, s2.loc1))
    for r in pd.concat([new, dom]).itertuples():
        assert tuple(sorted((r[1], r[2]))) in keys


def test_stock_and_graph():
    st = pd.read_csv(C / "APG_STOCK_CHECK_S4E1.csv", dtype={"apg_no": str})
    diff = st[st.verdict.str.startswith("DIFFERENT")]
    assert list(diff.apg_no) == ["2"] and float(diff.model_2025_mw.iloc[0]) == pytest.approx(2645.6)   # TH-MY listed, not changed
    assert set(st[st.verdict == "consistent"].apg_no) == {"1", "6", "9", "12", "13", "14", "17"}
    js = json.loads((C / "CORRIDORS_S4E1.json").read_text())
    g = js["graph"]
    assert g["isolated_after"] == [] and len(g["components_after"]) == 1
    assert {"BN-MY", "ID-TL", "MY-PH"} <= set(g["edges_after"]) and g["connected_coalitions_after"]["with_two_or_more"] == 383
    assert js["adjacency"]["unclear_below_1km"] == [] and js["gap_pairs"] == []


def test_switch():
    assert corridor_mode(CFG) == "on"
    # S4F-2 b (decision 97 b): the main corridor table moved to CORRIDORS_S4F2.csv (APG #4 at ID_Sumatra3 3); without that key the S4E-1 table
    assert corridor_tables(CFG) == ("research_inputs/corridors/CORRIDORS_S4F2.csv", "research_inputs/corridors/DOMESTIC_CORRIDORS_S4E1.csv")
    c = copy.deepcopy(CFG); del c["research"]["corridors"]["corridors_table_s4f2"]
    assert corridor_tables(c) == ("research_inputs/corridors/CORRIDORS_S4E1.csv", "research_inputs/corridors/DOMESTIC_CORRIDORS_S4E1.csv")
    c = copy.deepcopy(CFG); del c["research"]["corridors"]["adjacency_completion"]
    assert corridor_mode(c) == "off" and corridor_tables(c) == ("research_inputs/corridors/cross_border_corridors.csv", None)
    c["research"]["corridors"]["adjacency_completion"] = "maybe"
    with pytest.raises(ValueError):
        corridor_mode(c)


present = all((B / t).exists() for t in ("integrated", "disconnected", "integrated_off"))


@pytest.mark.skipif(not present, reason="S4E-1 builds not present")
def test_builds():
    import pypsa
    n = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    xb_l = n.lines[n.lines.border_class == "cross_border"]; xb_k = n.links[n.links.border_class == "cross_border"]
    assert len(xb_l) == 52 and (xb_k.carrier == "DC").sum() == 8
    for car in ("H2 pipeline", "CO2 pipeline"):
        assert (xb_k.carrier == car).sum() == 55   # pipelines follow the new topology (decision 59)
    new = n.lines.loc[[x for x in n.lines.index if str(x).startswith("S4E1")]]
    assert len(new) == 31 and (new.s_nom == 0).all() and new.s_nom_extendable.all()
    dom = n.links.loc[[x for x in n.links.index if str(x).startswith(("APG3 ", "APG18a ", "APG18b "))]]
    assert len(dom) == 3 and (dom.border_class == "domestic").all() and (dom.p_nom == 0).all()
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    assert not (d.lines.border_class == "cross_border").any() and not (d.links.border_class == "cross_border").any()
    assert all(x in d.links.index for x in dom.index)   # domestic candidates in both scenarios
    o = pypsa.Network(str(B / "integrated_off" / "integrated_2920_3h_unsolved.nc"))
    assert (o.lines.border_class == "cross_border").sum() == 21 and not any(str(x).startswith("S4E1") for x in o.lines.index)
