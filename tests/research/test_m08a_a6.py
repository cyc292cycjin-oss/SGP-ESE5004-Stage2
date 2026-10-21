"""M08a A6 / M08-7 (decisions 129, 131): renewable layout - A6.1 ground PV density 4.6 -> 5.1 MW/km2 (no build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4a_layers import apply_renewable_profiles, apply_solar_density   # noqa: E402


def toy():
    n = pypsa.Network(); n.set_snapshots(range(2))
    for i, c in enumerate(["ID", "VN", "SG"]):
        b = f"{c}1"; n.add("Bus", b, carrier="AC"); n.buses.loc[b, "country"] = c
        n.add("Generator", f"{b} solar", bus=b, carrier="solar", p_nom_extendable=True, p_nom_max=1000.0 * (i + 1))
        n.add("Generator", f"{b} solar rooftop", bus=b, carrier="solar rooftop", p_nom_extendable=True, p_nom_max=500.0)
        n.add("Generator", f"{b} onwind", bus=b, carrier="onwind", p_nom_extendable=True, p_nom_max=700.0)
        n.add("Generator", f"{b} solar existing", bus=b, carrier="solar existing", p_nom=50.0)
    return n


@pytest.fixture(scope="module")
def cfg():
    from phase4_static import config
    return config(ROOT, "integrated")


def test_density_config(cfg):
    sd = cfg["research"]["renewable"]["solar_density"]
    assert (sd["built_mw_per_km2"], sd["target_mw_per_km2"]) == (4.6, 5.1)


def test_ground_pv_scaled_only(cfg):
    n = toy(); before = n.generators.p_nom_max.copy()
    led = apply_solar_density(n, cfg["research"]["renewable"])
    k = 5.1 / 4.6
    assert led["scale"] == pytest.approx(1.108696, abs=1e-6) and led["generators"] == 3
    g = n.generators
    sol = g.carrier == "solar"
    assert np.allclose(g.p_nom_max[sol], before[sol] * k, rtol=1e-12)                        # same factor in every country
    assert g.p_nom_max[~sol].equals(before[~sol])                                             # rooftop, onwind, existing unchanged
    assert led["p_nom_max_after_mw"] == pytest.approx(led["p_nom_max_before_mw"] * k, rel=1e-12)


def test_applied_by_the_profile_layer_even_for_original(cfg):
    c = copy.deepcopy(cfg); c["research"]["renewable"]["profile_variant"] = "original"
    n = toy(); led = apply_renewable_profiles(n, c, ROOT)
    assert led["solar_density"]["scale"] == pytest.approx(5.1 / 4.6) and n.generators.at["ID1 solar", "p_nom_max"] == pytest.approx(1000 * 5.1 / 4.6)
    c["research"]["renewable"]["solar_density"] = {"built_mw_per_km2": 4.6, "target_mw_per_km2": 4.6}   # former state = factor 1
    n = toy(); apply_renewable_profiles(n, c, ROOT)
    assert n.generators.at["ID1 solar", "p_nom_max"] == 1000.0
