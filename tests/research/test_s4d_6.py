"""S4D-6: cloud package at the S4D final commit (profile A, ledger exports) and the registered first-batch sensitivities."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4d_layers import extra_asean_cost_scale  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
PKG = ROOT / "research/06_scope_redesign/p1_step4d_20261017/cloud_package"
REG = ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv"
B = ROOT / "results_project/s4d/s4d6/builds"


def test_scale_key():
    assert "extra_asean_cost_scale" not in CFG["research"]["co2"] and extra_asean_cost_scale(CFG) == 1.0   # absent = 1.0, config hash of the main unchanged
    c = copy.deepcopy(CFG); c["research"]["co2"]["extra_asean_cost_scale"] = 1.5; assert extra_asean_cost_scale(c) == 1.5
    c["research"]["co2"]["extra_asean_cost_scale"] = 0
    with pytest.raises(ValueError):
        extra_asean_cost_scale(c)
    src = (ROOT / "scripts_project/s2_network.py").read_text(); g = (ROOT / "scripts_project/v5/v5_gates.py").read_text()
    assert '"co2.extra_asean_cost_scale"' in src and "'co2.extra_asean_cost_scale'" in g


def test_package_scripts():
    run = (PKG / "run_365x24h.sh").read_text(); mk = (PKG / "make_package.sh").read_text(); pf = (PKG / "preflight.sh").read_text()
    assert "--solver-profile formal_barrier" in run and 'REFUSED: --solver-profile is required' in run   # profile A written in, still required / no default
    for f in ("COUNTRY_COST_LEDGER.csv", "COUNTRY_COST_LEDGER_DETAIL.csv", "LEDGER_IDENTITY.json", "NODAL_PRICES.csv"):
        assert f in run
    assert "disconnected_gap" in run and "DISCONNECTED_MAIN_NON_OPTIMAL" in run   # diagnostic stays conditional
    assert "co2.extra_asean_cost_scale=0.5 | 1.5" in mk and "co2.ship_route_factor_scale=0.75 | 1.25" in mk and "s3.gas.lng_cap_factor" in mk
    assert "section 13" in pf and "S4D" in pf


def test_sensitivity_registry():
    R = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    for k in ("s4d6_sensitivity_extra_asean_cost", "s4d6_sensitivity_ship_route_factor", "s4d6_sensitivity_lng_cap"):
        assert R.at[k, "status"] == "REFERENCE_ONLY" and R.at[k, "decision_ref"]


present = (B / "integrated_extra150" / "integrated_2920_3h_unsolved.nc").exists()


@pytest.mark.skipif(not present, reason="S4D-6 sensitivity build not present")
def test_extra150_build():
    import pypsa
    n = pypsa.Network(str(B / "integrated_extra150" / "integrated_2920_3h_unsolved.nc"))
    price = float(pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id").at["co2_extra_asean_storage_cost", "value"])
    st = n.stores[n.stores.carrier == "co2 sequestered extra-ASEAN"]
    assert len(st) == 11 and (st.capital_cost - 1.5 * price).abs().max() < 1e-9
    assert n.meta["research_extra_asean_storage"]["cost_scale"] == 1.5
