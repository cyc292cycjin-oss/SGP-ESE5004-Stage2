"""S4J-2 (decision 105 a): transmission losses as PyPSA-Eur v2025.07.0 (AC loss tangents at solve time, lossy DC, pipeline compression, split links)."""
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
from s4j_layers import AC_TRANSMISSION_LOSSES, LOSS_EFFICIENCY, REV, SYNC_HOOK, transmission_losses_mode  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
C = ROOT / "research_inputs/corridors"
B = ROOT / "results_project/s4j/s4j2/builds/integrated/integrated_2920_3h_unsolved.nc"


def test_switch_and_parameters():
    assert transmission_losses_mode(CFG) == "pypsa_eur"
    c = copy.deepcopy(CFG); del c["research"]["network"]["transmission_losses"]
    assert transmission_losses_mode(c) == "none"
    c["research"]["network"]["transmission_losses"] = "half"
    with pytest.raises(ValueError):
        transmission_losses_mode(c)
    assert AC_TRANSMISSION_LOSSES == 2 and "CO2 pipeline" not in LOSS_EFFICIENCY
    assert LOSS_EFFICIENCY["DC"]["efficiency_static"] == 0.98 and LOSS_EFFICIENCY["DC"]["efficiency_per_1000km"] == 0.977
    assert LOSS_EFFICIENCY["H2 pipeline"]["compression_per_1000km"] == 0.018 and LOSS_EFFICIENCY["gas pipeline"]["compression_per_1000km"] == 0.01


def test_tables():
    L = pd.read_csv(C / "LOSS_LINKS_S4J2.csv", keep_default_na=False)
    assert (abs(L.efficiency - L.efficiency_expected) < 1e-12).all() and (abs(L.efficiency2 - L.efficiency2_expected) < 1e-12).all()
    rev = L[L.kind == "reversed"]
    assert (rev.capital_cost == 0).all() and (rev.length_km == 0).all() and set(rev.link.str[: -len(REV)]) == set(L[L.kind == "forward"].link)
    assert (L[L.carrier != "DC"].bus2 != "").all() and (L[L.carrier == "DC"].efficiency2 == 0).all()
    js = json.loads((C / "LOSSES_S4J2.json").read_text())
    assert js["model_check"]["ac_tangents"] == 2 and js["model_check"]["loss_variables"] == 56 * js["model_check"]["lines"]
    assert js["model_check"]["sync_rows"] == js["model_check"]["reversed_extendable"] > 0


@pytest.mark.skipif(not B.exists(), reason="S4J-2 build not present")
def test_build():
    import pypsa
    n = pypsa.Network(str(B))
    assert n.meta["research_transmission_losses"]["mode"] == "pypsa_eur" and SYNC_HOOK in n.meta["required_constraint_hooks"]
    L = n.links[n.links.carrier.isin(list(LOSS_EFFICIENCY))]
    assert (L.p_min_pu == 0).all()
    co2 = n.links[n.links.carrier == "CO2 pipeline"]
    assert (co2.efficiency == 1).all() and (co2.p_min_pu == -1).all()
    for x in L.index[L.reversed.astype(bool)]:
        f = n.links.loc[x[: -len(REV)]]; r = n.links.loc[x]
        assert (r.bus0, r.bus1) == (f.bus1, f.bus0) and r.p_nom_max == f.p_nom_max and r.efficiency == f.efficiency and r.border_class == f.border_class
    gas = L[L.carrier == "gas pipeline"]
    assert np.allclose(gas.efficiency2, -0.01 * gas.length_original / 1e3)
