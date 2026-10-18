"""S4J-3 rewritten (decisions 105 b, 107 a): TH-MY DC bidirectional; converter B2B bidirectional, not extendable, fixed at the DC extension limit."""
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
from s4j_layers import REV, th_my_hvdc_mode  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
T = pd.read_csv(ROOT / "research_inputs/corridors/DC_CONVERTERS_S4J3.csv", keep_default_na=False)
JS = json.loads((ROOT / "research_inputs/corridors/DC_CONVERTERS_S4J3.json").read_text())
B = ROOT / "results_project/s4j/s4j3b/builds"
KNG = "Khlong Ngae – Gurun"


def test_switch():
    assert th_my_hvdc_mode(CFG) == "bidirectional_fixed_b2b"
    c = copy.deepcopy(CFG); del c["research"]["network"]["th_my_hvdc"]
    assert th_my_hvdc_mode(c) == "s4h"
    c["research"]["network"]["th_my_hvdc"] = "both"
    with pytest.raises(ValueError):
        th_my_hvdc_mode(c)


def test_table():
    assert JS["meta"]["mode"] == "bidirectional_fixed_b2b" and JS["meta"]["one_way_made_bidirectional"] == [KNG]
    pairs = T[T.kind == "b2b_pair"]
    assert set(pairs.name) == {"convert_412_577", "convert_599_890"} and set(pairs.converter_b2b) == {KNG}
    assert (pairs.p_nom == 20300).all() and (pairs.p_nom_extendable.astype(str).str.lower() == "false").all() and (pairs.efficiency == 1).all()
    assert set(T[T.kind == "b2b_reported"].name) == {"convert_935_1501"}
    k = T[(T.kind == "dc_link") & (T.name == KNG)].iloc[0]
    assert k.reversed_copy == KNG + REV and k.noloss_p_min_pu == -1.0
    assert JS["model"]["b2b_rows"] == 0 and JS["model"]["sync_rows"] == 322


@pytest.mark.skipif(not (B / "integrated").exists(), reason="S4J-3b builds not present")
def test_build():
    import pypsa
    n = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    assert not any(h.startswith("research_b2b") for h in n.meta["required_constraint_hooks"])
    for c in ("convert_412_577", "convert_599_890"):
        z = n.links.loc[c]
        assert (not z.p_nom_extendable) and z.p_nom == 20300 and z.p_min_pu == -1 and z.efficiency == 1
    assert not n.links.at["convert_935_1501", "p_nom_extendable"] and n.links.at["convert_935_1501", "p_nom"] == 2000
    r = n.links.loc[KNG + REV]
    assert (r.bus0, r.bus1) == (n.links.at[KNG, "bus1"], n.links.at[KNG, "bus0"]) and r.capital_cost == 0
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    assert KNG not in d.links.index and d.links.at["convert_412_577", "p_nom"] == 2000 and not d.links.at["convert_412_577", "p_nom_extendable"]
