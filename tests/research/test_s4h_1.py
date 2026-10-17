"""S4H-1 (decision 100): LA-VN grid stock 0, the four clustered LA-VN lines as zero-capacity candidates."""
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
from s4h_layers import la_vn_stock_mode  # noqa: E402

C = ROOT / "research_inputs/corridors"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4h/s4h1/builds"
LINES = ["59", "60", "63", "64"]


def test_registry_and_table():
    r = REG.loc["la_vn_grid_stock_2025"]
    assert float(r.value) == 0.0 and r.tier == "B" and r.decision_ref == "100"
    t = pd.read_csv(C / "LA_VN_STOCK_S4H1.csv", dtype={"component": str})
    assert list(t.component) == LINES and t.s_nom_author_mw.sum() == pytest.approx(1.0) and t.unit_cost_eur_per_mw_km_a.nunique() == 1
    js = json.loads((C / "LA_VN_STOCK_S4H1.json").read_text())["ipp_estimate"]
    lo, hi = js["annualised_value_eur_per_a"]
    assert js["capacity_mw"] == 572.0 and lo == pytest.approx(572.0 * js["length_km"][0] * js["unit_cost_eur_per_mw_km_a"]) and lo < hi
    assert REG.at["s4h1_ipp_export_lines_estimate", "tier"] == "C"


def test_switch():
    assert la_vn_stock_mode(CFG) == "aims_zero"
    c = copy.deepcopy(CFG); del c["research"]["network"]["la_vn_stock"]
    assert la_vn_stock_mode(c) == "author"


present = all((B / t).exists() for t in ("integrated", "integrated_author", "disconnected"))


@pytest.mark.skipif(not present, reason="S4H-1 builds not present")
def test_builds():
    import pypsa
    m = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    z = m.lines.loc[LINES]
    assert (z.s_nom == 0).all() and (z.s_nom_min == 0).all() and z.s_nom_extendable.all() and (z.border_class == "cross_border").all()
    np.testing.assert_allclose(z.s_nom_max, 20000.0)
    np.testing.assert_allclose(z.num_parallel, m.meta["research_candidate_num_parallel"]["num_parallel"])
    m.calculate_dependent_values()
    np.testing.assert_allclose(m.lines.loc[LINES, "x"], m.lines.loc[LINES, "length"] * m.line_types.loc[z.type, "x_per_length"].values / z.num_parallel.values, rtol=1e-12)
    assert m.lines.x.max() < 1e4   # the extreme LA-VN reactance of S4G (558,762 ohm) is gone
    d = pypsa.Network(str(B / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    assert not set(LINES) & set(d.lines.index)
