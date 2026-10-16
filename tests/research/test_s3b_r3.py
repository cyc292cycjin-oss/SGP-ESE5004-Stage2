"""S3B R3 (decision 68): LNG regasification expansion switch research.s3.gas.lng_expansion = existing_only (main) | cap_factor (sensitivity)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
REG = ROOT / "research_inputs" / "registry_v5"
R3 = ROOT / "results_project" / "s3b" / "r3"


def test_config_registry_and_caps_table():
    from phase4_static import config
    G = config(ROOT, "integrated")["research"]["s3"]["gas"]
    assert G["lng_expansion"] == "existing_only" and G["lng_cap_factor"] == 2.5
    r = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert r.loc["lng_terminal_expansion_mode", "value"] == "existing_only" and r.loc["lng_terminal_expansion_cap_factor", "status"] == "SENSITIVITY"
    for k in ["lng_regas_capex_ref_ulvestad_overland_2012", "lng_regas_capex_ref_eria_2016", "lng_regas_capex_ref_pypsa_eur_import_branch", "gas_pipeline_MY_SG_capacity_search_s3b"]:
        assert r.loc[k, "status"] == "REFERENCE_ONLY"
    assert r.loc["gas_pipeline_existing_malaysia_singapore", "status"] == "DATA_PENDING"
    assert 7018 * 0.5 < float(r.loc["lng_regas_capex_ref_ulvestad_overland_2012", "value"]) < 7018 * 1.5
    t = pd.read_csv(ROOT / "research_inputs/lng_terminals_v5/LNG_EXPANSION_MODES_S3B_R3.csv")
    assert (t.main_p_nom_max_mw == t.existing_mw).all() and (t.h2_import_cap_mw == t.sensitivity_p_nom_max_mw).all()


def built(mode):
    return (R3 / mode / "integrated" / "integrated_2920_3h_unsolved.nc").exists()


@pytest.mark.skipif(not (built("main") and built("cap_factor")), reason="S3B R3 networks not built")
def test_r3_networks():
    import pypsa
    from v5.v5_gates import gate_b14_terminal_caps
    nm = pypsa.Network(str(R3 / "main" / "integrated" / "integrated_2920_3h_unsolved.nc"))
    nc = pypsa.Network(str(R3 / "cap_factor" / "integrated" / "integrated_2920_3h_unsolved.nc"))
    lm, lc = nm.generators[nm.generators.carrier == "LNG import"], nc.generators[nc.generators.carrier == "LNG import"]
    assert (lm.p_nom_max == lm.p_nom).all() and (lm.p_nom > 0).all() and len(lm) == 9 and len(lc) == 16
    ex = lc[lc.p_nom > 0]
    assert (ex.p_nom_max <= 2.5 * ex.p_nom * (1 + 1e-9)).all() and len(lc[lc.p_nom == 0]) == 7   # 7 proposed-only sites in the sensitivity
    h_m = nm.generators[nm.generators.carrier == "H2 import"].p_nom_max.sort_index(); h_c = nc.generators[nc.generators.carrier == "H2 import"].p_nom_max.sort_index()
    assert h_m.index.equals(h_c.index) and (h_m == h_c).all()   # liquid-H2 terminal caps unchanged by R3
    for n, mode in [(nm, "existing_only"), (nc, "cap_factor")]:
        b14 = gate_b14_terminal_caps(n)
        assert b14["passed"] and b14["expansion"] == mode and len(b14["terminals"]) == 16
