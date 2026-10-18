"""S4J-1 (decision 104): non-industrial electricity base load = demand-table sectors not modelled separately; Astar gives the shape only."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s2_layers import TABLE_BASE_SECTORS, nonindustrial_electricity_mode  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
T = pd.read_csv(ROOT / "research_inputs/demand_v5/NONINDUSTRIAL_ELECTRICITY_S4J1.csv").set_index("country")
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4j/s4j1/builds/integrated/integrated_2920_3h_unsolved.nc"


def test_switch():
    assert nonindustrial_electricity_mode(CFG) == "table_sectors"
    c = copy.deepcopy(CFG); del c["research"]["demand"]["nonindustrial_electricity"]
    assert nonindustrial_electricity_mode(c) == "astar_residual"
    c["research"]["demand"]["nonindustrial_electricity"] = "both"
    with pytest.raises(ValueError):
        nonindustrial_electricity_mode(c)
    assert TABLE_BASE_SECTORS == ("Residential", "Commercial", "AgricultureOthers", "Transport")


def test_table():
    c = T.drop(index="ASEAN")
    assert T.at["VN", "base_load_2050_twh"] == pytest.approx(197.159347, abs=1e-3)   # S4I A5 scheme (b), VN has no transport electricity
    s = c.residential_twh + c.commercial_twh + c.agriculture_others_twh + c.transport_twh
    assert (abs(s - c.base_load_2050_twh) < 1e-9).all() and (abs(c.network_table_sectors_twh - c.base_load_2050_twh) < 1e-6).all()
    assert (abs(c.minus_s4i_scheme_b_twh - c.transport_twh) < 1e-6).all()   # the only difference to scheme (b) is the transport electricity row
    assert T.at["ASEAN", "base_load_2050_twh"] == pytest.approx(c.base_load_2050_twh.sum())
    assert (abs(c.multiple_vs_2019 - c.base_load_2050_twh / c.base_2019_twh) < 1e-9).all() and (c.multiple_vs_2019 > 0.9).all()   # BN 0.99: the table's own projection
    assert REG.at["s4j1_nonindustrial_electricity_switch", "decision_ref"] == "104"


@pytest.mark.skipif(not B.exists(), reason="S4J-1 build not present")
def test_build():
    import pypsa
    n = pypsa.Network(str(B))
    L = n.loads[n.loads.account == "Astar"]; w = n.snapshot_weightings.generators
    tot = {c: float(sum((n.loads_t.p_set[l] * w).sum() for l in g.index)) / 1e6 for c, g in L.groupby("country")}
    for c, v in tot.items():
        assert v == pytest.approx(T.at[c, "base_load_2050_twh"], rel=1e-9)
    assert n.meta["s2_demand_ledger"]["parameters"]["nonindustrial_electricity"] == "table_sectors"
