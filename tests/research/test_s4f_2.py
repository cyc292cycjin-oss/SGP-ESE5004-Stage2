"""S4F-2 (decision 97): TH-MY stock, APG #4 endpoint, Lao CO2 into the Vietnamese store, SG-VN / SG-KH second batch, author readjust audit."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4f_layers import (TRANSIT_RAIL_CARRIER, apply_th_my_stock, extend_optional_corridors, lao_vn_store_mode, optional_corridor_mode,  # noqa: E402
                        th_my_stock_mode)
from scenario_network import MARITIME_TRADE_CARRIERS  # noqa: E402

C = ROOT / "research_inputs/corridors"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4f/s4f2/builds"
DUP = [f"250878579-{i}_0" for i in range(1, 5)]


def test_th_my_table():
    t = pd.read_csv(C / "TH_MY_STOCK_S4F2.csv", dtype={"component": str}).set_index("component")
    assert list(t.loc[DUP, "action"].unique()) == ["remove"] and (t.loc[DUP, "frozen_base_mw"] == 491.4).all()
    assert t.at["91", "action"] == "set_capacity" and t.at["91", "corrected_mw"] == 80.0 and t.at["91", "grade"] == "C" and "not Sadao" in t.at["91", "basis"]
    assert t.at["Khlong Ngae – Gurun", "action"] == "keep" and t.at["Khlong Ngae – Gurun", "corrected_mw"] == 300.0
    assert t.frozen_base_mw.sum() == pytest.approx(2645.6) and t.corrected_mw.sum() == pytest.approx(380.0)   # = APG #2
    assert float(REG.at["th_my_line91_s_nom_2025", "value"]) == 80.0 and REG.at["th_my_line91_s_nom_2025", "tier"] == "C"
    assert float(REG.at["th_my_hvdc_khlong_ngae_gurun_2025", "value"]) == 300.0


def toy():
    import pypsa
    n = pypsa.Network()
    for b in ["MY_Peninsular2 0", "TH2 0", "MY_Peninsular22 0", "TH21 0"]:
        n.add("Bus", b, carrier="AC", country=b[:2])
    n.add("Line", "91", bus0="MY_Peninsular2 0", bus1="TH2 0", x=1.0, s_nom=380.0, s_nom_min=380.0, s_nom_extendable=True)
    for k in DUP:
        n.add("Link", k, bus0="MY_Peninsular22 0", bus1="TH21 0", carrier="DC", p_nom=491.4, p_nom_min=491.4, p_nom_extendable=True)
    n.add("Link", "Khlong Ngae – Gurun", bus0="TH21 0", bus1="MY_Peninsular22 0", carrier="DC", p_nom=300.0, p_nom_min=300.0, p_nom_extendable=True)
    cor = pd.DataFrame([dict(component_type="Line", component="91", capacity_2025_mw=380.0, nominal_mw_in_base=380.0)] +
                       [dict(component_type="Link", component=k, capacity_2025_mw=491.4, nominal_mw_in_base=491.4) for k in DUP + ["Khlong Ngae – Gurun"]])
    return n, cor


def test_apply_th_my_stock():
    assert th_my_stock_mode(CFG) == "apg_aims"
    n, cor = toy(); cor2, led = apply_th_my_stock(n, cor, CFG, ROOT)
    assert not any(k in n.links.index for k in DUP) and n.lines.at["91", "s_nom"] == 80.0 and n.lines.at["91", "s_nom_min"] == 80.0
    assert n.links.at["Khlong Ngae – Gurun", "p_nom_min"] == 300.0 and led["th_my_total_after_mw"] == pytest.approx(380.0)
    assert set(cor2.component) == {"91", "Khlong Ngae – Gurun"} and float(cor2[cor2.component == "91"].capacity_2025_mw.iloc[0]) == 80.0
    c = copy.deepcopy(CFG); c["research"]["network"]["th_my_stock"] = "frozen_base"
    n, cor = toy(); cor3, led = apply_th_my_stock(n, cor, c, ROOT)
    assert len(cor3) == 6 and n.lines.at["91", "s_nom_min"] == 380.0 and led["mode"] == "frozen_base"
    n, cor = toy(); n.lines.at["91", "s_nom_min"] = 381.0
    with pytest.raises(ValueError):
        apply_th_my_stock(n, cor, CFG, ROOT)   # the frozen-base value is checked before the change


def test_apg4_endpoint_and_optional():
    s4e = pd.read_csv(C / "CORRIDORS_S4E1.csv"); s4f = pd.read_csv(C / "CORRIDORS_S4F2.csv")
    assert len(s4e) == len(s4f)
    a4 = s4f[s4f.component.str.startswith("APG4 ")].iloc[0]
    assert {a4["from"], a4["to"]} == {"ID_Sumatra3 3", "MY_Peninsular2 1"} and a4.component_type == "Link" and a4.capacity_2025_mw == 0.0
    a16 = s4f[s4f.component.str.startswith("APG16 ")].iloc[0]
    assert "ID_Sumatra2 0" in (a16["from"], a16["to"])   # #16 keeps the Batam end
    sub = pd.read_csv(C / "SUBSEA_SHARE_S4F2.csv"); pairs = set(zip(sub.loc0, sub.loc1))
    assert ("ID_Sumatra3 3", "MY_Peninsular2 1") in pairs and ("KH2 0", "SG2 0") in pairs and ("SG2 0", "VN2 0") in pairs
    s4e_sub = pd.read_csv(C / "SUBSEA_SHARE_S4E1.csv")
    pd.testing.assert_frame_equal(sub.iloc[:len(s4e_sub)].reset_index(drop=True), s4e_sub, check_dtype=False)   # old rows unchanged
    opt = pd.read_csv(C / "OPTIONAL_CORRIDORS_S4F2.csv")
    assert len(opt) == 2 and set(opt.country_from + "-" + opt.country_to) <= {"KH-SG", "SG-KH", "SG-VN", "VN-SG"}
    assert optional_corridor_mode(CFG) == "off"
    cor, led = extend_optional_corridors(s4f, CFG, ROOT); assert len(cor) == len(s4f) and led["added"] == []
    c = copy.deepcopy(CFG); c["research"]["corridors"]["optional_sg_vn_kh"] = "on"
    cor, led = extend_optional_corridors(s4f, c, ROOT); assert len(cor) == len(s4f) + 2 and len(led["added"]) == 2


def test_lao_vn_store_and_trade_class():
    assert lao_vn_store_mode(CFG) == "on" and TRANSIT_RAIL_CARRIER in MARITIME_TRADE_CARRIERS
    src = (ROOT / "scripts_project/s4d_ledger.py").read_text()
    assert '"CO2 transit rail": "co2_transit_rail_freight"' in src


def test_author_readjust_audit():
    a = pd.read_csv(C / "AUTHOR_READJUST_LINES_S4F2.csv", dtype={"line": str})
    js = json.loads((C / "AUTHOR_READJUST_LINES_S4F2.json").read_text())
    for pair, v in js["pair_sums"].items():
        assert v["s_nom"] == pytest.approx(v["aims"], abs=1e-6)   # the author's AIMS totals, distributed by length
    assert "91" in set(a.line) and a.set_index("line").at["91", "s_nom_mw"] == 380.0
    assert {"in_ac_loop", "ac_path_via_third_country", "ratio_s_nom_to_rating", "x_ohm"} <= set(a.columns)


present = all((B / t).exists() for t in ("integrated", "disconnected", "integrated_frozen_th_my", "integrated_sg_vn_kh"))


@pytest.mark.skipif(not present, reason="S4F-2 builds not present")
def test_builds():
    import pypsa
    n = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    assert not any(k in n.links.index for k in DUP) and n.lines.at["91", "s_nom_min"] == 80.0 and n.links.at["Khlong Ngae – Gurun", "p_nom_min"] == 300.0
    assert any(str(k).startswith("APG4 ID_Sumatra3 3") for k in n.links.index) and not any(str(k).startswith("APG4 ID_Sumatra2 0") for k in n.links.index)
    rail = n.links[n.links.carrier == TRANSIT_RAIL_CARRIER]
    assert len(rail) == 6 and (rail.bus1 == "co2 sequestered VN").all() and (rail.border_class == "maritime_trade").all()
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    assert (d.links.carrier == TRANSIT_RAIL_CARRIER).sum() == 6 and not (d.links.border_class == "cross_border").any()
    f = pypsa.Network(str(B / "integrated_frozen_th_my" / "integrated_2920_3h_unsolved.nc"))
    assert all(k in f.links.index for k in DUP) and f.lines.at["91", "s_nom_min"] == 380.0
    o = pypsa.Network(str(B / "integrated_sg_vn_kh" / "integrated_2920_3h_unsolved.nc"))
    assert sum(str(k).startswith(("APGother1", "APGother2")) for k in o.links.index) == 2
