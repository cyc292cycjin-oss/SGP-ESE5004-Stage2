"""S4J-3 (decision 105 b): TH-MY DC bidirectional; converter-station B2B follows its DC link at no cost."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4j_layers import B2B_HOOK, REV  # noqa: E402

T = pd.read_csv(ROOT / "research_inputs/corridors/DC_CONVERTERS_S4J3.csv", keep_default_na=False)
JS = json.loads((ROOT / "research_inputs/corridors/DC_CONVERTERS_S4J3.json").read_text())
B = ROOT / "results_project/s4j/s4j3/builds"
KNG = "Khlong Ngae – Gurun"


def test_table():
    assert JS["meta"]["one_way_made_bidirectional"] == [KNG]
    pairs = T[T.kind == "b2b_pair"]
    assert set(pairs.name) == {"convert_412_577", "convert_599_890"} and set(pairs.b2b_following) == {KNG}
    assert set(T[T.kind == "b2b_reported"].name) == {"convert_935_1501"}
    k = T[(T.kind == "dc_link") & (T.name == KNG)].iloc[0]
    assert k.reversed_copy == KNG + REV and k.noloss_p_min_pu == -1.0
    assert JS["model"]["b2b_rows"] == 2 and JS["model"]["sync_rows"] == 322


@pytest.mark.skipif(not (B / "integrated").exists(), reason="S4J-3 builds not present")
def test_build():
    import pypsa
    n = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    assert B2B_HOOK in n.meta["required_constraint_hooks"]
    for c in ("convert_412_577", "convert_599_890"):
        z = n.links.loc[c]
        assert z.p_nom_extendable and z.capital_cost == 0 and z.p_nom_min == 2000 and z.p_nom_max == 2000 + 20000 and z.p_min_pu == -1
    assert not n.links.at["convert_935_1501", "p_nom_extendable"]
    r = n.links.loc[KNG + REV]
    assert (r.bus0, r.bus1) == (n.links.at[KNG, "bus1"], n.links.at[KNG, "bus0"]) and r.capital_cost == 0
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    assert KNG not in d.links.index and not d.links.at["convert_412_577", "p_nom_extendable"]
