"""S4G-1 (decision 98): line-type electrical parameters of the 19 author-readjusted cross-border AC lines."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4g_layers import readjust_impedance_mode  # noqa: E402

C = ROOT / "research_inputs/corridors"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4g/s4g1/builds"
T = pd.read_csv(C / "READJUST_IMPEDANCE_S4G1.csv", dtype={"line": str}, float_precision="round_trip").set_index("line")
RTOL = 1e-9   # the table passes through CSV (about 1e-12 relative rounding)


def test_source_relation():
    from s4g_1_data import source_checks
    s = source_checks()
    assert s["pypsa"]["version"] == "0.30.3" and "def apply_line_types" in s["pypsa"]["apply_line_types"]
    assert "num_parallel" in s["simplify_network"]["lines"]["181"] and "np.sqrt(3)" in s["base_network"]["lines"]["694"]
    js = json.loads((C / "READJUST_IMPEDANCE_S4G1.json").read_text())
    assert js["stored_x_equals_type_x_frozen"] is True   # the frozen base stores the type values: PyPSA used the author x before S4G


def test_table():
    assert len(T) == 19 and T.at["91", "s_nom_used_mw"] == 80.0 and T.at["91", "s_nom_frozen_mw"] == 380.0
    np.testing.assert_allclose(np.sqrt(3) * T.v_nom_kv * T.i_nom_ka * T.num_parallel_s4g, T.s_nom_used_mw, rtol=RTOL)   # s_nom = sqrt3 v i n
    np.testing.assert_allclose(T.x_s4g, 0.0 + T.x_type_frozen * T.num_parallel_frozen / T.num_parallel_s4g, rtol=RTOL)   # x ~ 1 / num_parallel
    np.testing.assert_allclose(T.b_s4g, T.b_type_frozen * T.num_parallel_s4g / T.num_parallel_frozen, rtol=RTOL)   # b ~ num_parallel
    la_th = T[T.country_pair == "LA-TH"]
    assert la_th.x_s4g.nunique() == 1 or np.allclose(la_th.x_s4g, la_th.x_s4g.iloc[0])   # s_nom shared by length -> one x
    assert REG.at["s4g1_readjust_impedance_switch", "value"] == "pypsa_eur|author"


def test_switch():
    assert readjust_impedance_mode(CFG) == "pypsa_eur"
    c = copy.deepcopy(CFG); del c["research"]["network"]["readjust_impedance"]
    assert readjust_impedance_mode(c) == "author"
    c["research"]["network"]["readjust_impedance"] = "half"
    with pytest.raises(ValueError):
        readjust_impedance_mode(c)


present = all((B / t).exists() for t in ("integrated", "integrated_author", "disconnected"))


@pytest.mark.skipif(not present, reason="S4G-1 builds not present")
def test_builds():
    import pypsa
    m = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    o = pypsa.Network(str(B / "integrated_author" / "integrated_2920_3h_unsolved.nc"))
    np.testing.assert_allclose(m.lines.loc[T.index, "num_parallel"], T.num_parallel_s4g, rtol=RTOL)
    np.testing.assert_allclose(o.lines.loc[T.index, "num_parallel"], T.num_parallel_frozen, rtol=RTOL)
    assert (m.lines.loc[T.index, "s_nom"] == o.lines.loc[T.index, "s_nom"]).all() and (m.lines.loc[T.index, "capital_cost"] == o.lines.loc[T.index, "capital_cost"]).all()
    np.testing.assert_allclose(m.lines.loc[T.index, "s_nom_max"], m.lines.loc[T.index, "s_nom"] + 20000.0)
    m.calculate_dependent_values()   # PyPSA recomputes x from the type: the corrected value is the one used
    np.testing.assert_allclose(m.lines.loc[T.index, "x"], T.x_s4g, rtol=RTOL)
    other = m.lines.index.difference(T.index)
    np.testing.assert_allclose(m.lines.loc[other, "num_parallel"], o.lines.loc[other, "num_parallel"])   # nothing else changed
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    assert not set(T.index) & set(d.lines.index)
