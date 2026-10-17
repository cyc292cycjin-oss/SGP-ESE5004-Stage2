"""S4H-2 (decision 101): reference num_parallel of the AC candidates, APG17 by the line-type relation, reference candidates for every country pair with AC stock."""
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
from s4h_layers import candidate_np_mode  # noqa: E402

C = ROOT / "research_inputs/corridors"
CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
JS = json.loads((C / "CORRIDORS_S4H2.json").read_text())
B = ROOT / "results_project/s4h/s4h2/builds"


def test_registry():
    for k in ("s4h2_candidate_num_parallel_switch", "s4h2_candidate_convention_sources", "s4h2_apg17_readjust", "s4h2_readjust_impedance_table",
              "s4h2_reference_candidates", "s4h2_candidate_completeness_table", "s4h2_subsea_table"):
        assert REG.at[k, "decision_ref"] == "101"
    assert REG.at["s4h2_candidate_num_parallel_switch", "value"] == "one_circuit|template43"


def test_corridor_tables():
    old = pd.read_csv(C / "CORRIDORS_S4F2.csv", float_precision="round_trip"); new = pd.read_csv(C / "CORRIDORS_S4H2.csv", float_precision="round_trip")
    add = new.iloc[len(old):]
    pd.testing.assert_frame_equal(new.iloc[: len(old)].reset_index(drop=True), old, check_dtype=False)
    assert len(add) == len(JS["new_components"]) and add.component.str.startswith("S4H2 ").all() and (add.capacity_2025_mw == 0).all()
    assert (add[add.component_type == "Line"].subsea_share == 0).all() and set(add[add.component_type == "Link"].carrier) <= {"DC"}
    assert (add.country_from != add.country_to).all() and all(c["consistent"] for c in JS["new_components"])
    T = pd.read_csv(C / "CANDIDATE_COMPLETENESS_S4H2.csv", keep_default_na=False)
    need = T[T.needs_reference_candidate.astype(str).str.lower() == "true"]
    assert (need.added.str.len() > 0).all() and (T[T.needs_reference_candidate.astype(str).str.lower() != "true"].added == "").all()
    s1 = pd.read_csv(C / "SUBSEA_SHARE_S4F2.csv"); s2 = pd.read_csv(C / "SUBSEA_SHARE_S4H2.csv")
    assert len(s1) == len(s2) and (s1.share_landmass_nonland == s2.share_landmass_nonland).all()


def test_readjust_table():
    g = pd.read_csv(C / "READJUST_IMPEDANCE_S4G1.csv", dtype={"line": str}, float_precision="round_trip")
    h = pd.read_csv(C / "READJUST_IMPEDANCE_S4H2.csv", dtype={"line": str}, float_precision="round_trip")
    pd.testing.assert_frame_equal(h.iloc[:19], g, check_dtype=False, rtol=1e-9)
    a = h.iloc[19]
    assert a.line == "APG17_LA_MM" and a.num_parallel_s4g == pytest.approx(30.0 / (math.sqrt(3) * 380.0 * 2.58), rel=1e-9)
    assert a.x_s4g == pytest.approx(a.x_type_frozen * a.num_parallel_frozen / a.num_parallel_s4g, rel=1e-9)


def test_switch():
    assert candidate_np_mode(CFG) == "one_circuit"
    c = copy.deepcopy(CFG); del c["research"]["corridors"]["candidate_num_parallel"]
    assert candidate_np_mode(c) == "template43"
    c["research"]["corridors"]["candidate_num_parallel"] = "two"
    with pytest.raises(ValueError):
        candidate_np_mode(c)


present = (B / "integrated" / "integrated_2920_3h_unsolved.nc").exists()


@pytest.mark.skipif(not present, reason="S4H-2 builds not present")
def test_build_readback():
    import pypsa
    m = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    cand = m.lines[(m.lines.s_nom == 0) & (m.lines.s_nom_min == 0) & m.lines.s_nom_extendable]
    assert (cand.num_parallel == 1.0).all() and len(cand) == m.meta["research_candidate_num_parallel"]["candidates"]
    for k in (c["component"] for c in JS["new_components"]):
        assert k in m.lines.index or k in m.links.index
    stored = m.lines.x.copy()
    m.calculate_dependent_values()
    np.testing.assert_allclose(m.lines.x, stored, rtol=1e-12)   # PyPSA recomputes the stored values
    np.testing.assert_allclose(m.lines.at["APG17_LA_MM", "num_parallel"], 30.0 / (math.sqrt(3) * 380.0 * 2.58), rtol=1e-12)
