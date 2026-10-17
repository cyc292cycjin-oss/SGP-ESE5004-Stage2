"""S4C-2 (decision 83; user decision 2026-10-17): national hydro inflow = Ember 2019-2025 median x 1.1, option B (capacity shares) main,
option A (runoff shares) and frozen_base as switch values; new-build proxies from the corrected same-country stock."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
TGT = ROOT / "research_inputs/hydro_v5/HYDRO_NATIONAL_TARGET_S4C2.csv"
BUILD = ROOT / "results_project/s4c/build_s4c2"


def test_targets():
    t = pd.read_csv(TGT, keep_default_na=False).set_index("country")
    assert float(t.at["VN", "target_mwh"]) == pytest.approx(80.621 * 1.1e6, rel=1e-6)
    assert float(t.at["ID", "target_mwh"]) == pytest.approx(31.165 * 1.1e6, rel=1e-6)
    assert t.at["SG", "status"] == "NO_EMBER_DATA" and t.at["BN", "status"] == "SOURCE_ZERO"
    assert (t.loc[t.status == "REGISTERED", "multiplier"].astype(float) == 1.1).all()


def _net(tag):
    import pypsa
    p = BUILD / tag / "integrated_2920_3h_unsolved.nc"
    return pypsa.Network(str(p)) if p.exists() else None


@pytest.mark.skipif(not (BUILD / "integrated" / "integrated_2920_3h_unsolved.nc").exists(), reason="S4C-2 build not present")
def test_main_option_b():
    n = _net("integrated"); h = n.meta["research_hydro_inflow"]
    assert h["mode"] == "national_observed"
    for c, v in h["countries"].items():
        assert v["energy_after_mwh"] == pytest.approx(v["target_mwh"] - v["ror_clipped_mwh"], rel=1e-9)
    u = pd.DataFrame(h["units"])
    res = u[u.kind == "reservoir"]
    for c, x in res.groupby("country"):   # B: one annual CF per country for the reservoirs (run-of-river may lose clipped energy)
        assert x.cf_after.max() - x.cf_after.min() < 1e-9
    assert (u.cf_after <= 1.0 + 1e-9).all() and set(h["totals"]["anomalous_units_cf_gt_1_before"]) and len(h["totals"]["anomalous_units_cf_gt_1_before"]) == 8
    nb = pd.DataFrame(h["new_build"])
    assert nb.scope.str.startswith("country").all()
    w = n.snapshot_weightings.generators
    su = n.storage_units; inf = n.storage_units_t.inflow
    name = "ID_Kalimantan4 9 hydro_new"
    cf = float((inf[name] * w).sum() / (su.at[name, "p_nom_max"] * 8760))
    assert cf == pytest.approx(h["countries"]["ID"]["target_mwh"] / (h["countries"]["ID"]["stock_mw"] * 8760), rel=0.02)


@pytest.mark.skipif(not (BUILD / "frozen_base" / "integrated_2920_3h_unsolved.nc").exists(), reason="comparison build not present")
def test_frozen_base_unchanged_and_option_a():
    n0 = _net("frozen_base"); nA = _net("runoff_shares")
    assert n0.meta["research_hydro_inflow"]["mode"] == "frozen_base"
    a = nA.meta["research_hydro_inflow"]; assert a["mode"] == "national_observed_runoff_shares"
    u = pd.DataFrame(a["units"]); res = u[(u.kind == "reservoir") & (u.energy_before_mwh > 0)]
    ratio = (res.energy_after_mwh / res.energy_before_mwh).groupby(res.country).agg(["min", "max"])
    assert ((ratio["max"] - ratio["min"]) < 1e-9).all()   # A: one factor per country, runoff shares kept
