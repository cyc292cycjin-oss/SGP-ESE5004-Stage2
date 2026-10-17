"""S4G-2 (decision 99 b): Thai national store for the Lao transit existing_port sensitivity; main run unchanged."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4e_layers import lao_transit_legs  # noqa: E402
from s4g_layers import lao_th_store_mode  # noqa: E402

CFG = yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())
REG = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
B = ROOT / "results_project/s4g/s4g2/builds"


def test_switch_and_registry():
    assert lao_th_store_mode(CFG) == "on" and CFG["research"]["co2"]["lao_transit_destination"] == "nearest_coast"
    c = copy.deepcopy(CFG); del c["research"]["co2"]["lao_transit_th_store"]
    assert lao_th_store_mode(c) == "off"
    assert REG.at["s4g2_lao_th_store", "value"] == "on|off" and REG.at["s4g2_apg_plans_rule_confirmed", "value"] == "confirmed"


def test_existing_port_destinations():
    c = copy.deepcopy(CFG); c["research"]["co2"]["lao_transit_destination"] = "existing_port"
    legs = lao_transit_legs(c, REG)
    th = sorted(k for k, g in legs.items() if g["coastal_node"].startswith("TH"))
    assert th == ["LA2 1", "LA2 2", "LA2 3", "LA2 5"]
    main = lao_transit_legs(CFG, REG)
    assert all(g["coastal_node"].startswith("VN") for g in main.values())   # main: every transit ends in Viet Nam


present = all((B / t).exists() for t in ("integrated", "integrated_existing_port", "disconnected_existing_port"))


@pytest.mark.skipif(not present, reason="S4G-2 builds not present")
def test_builds():
    import pypsa
    m = pypsa.Network(str(B / "integrated" / "integrated_2920_3h_unsolved.nc"))
    assert not (m.links.bus1 == "co2 sequestered TH").loc[m.links.carrier == "CO2 transit rail"].any()   # main unchanged
    for t, sc in (("integrated_existing_port", "integrated"), ("disconnected_existing_port", "disconnected")):
        n = pypsa.Network(str(B / t / f"{sc}_2920_3h_unsolved.nc"))
        rail = n.links[n.links.carrier == "CO2 transit rail"]
        th = rail[rail.bus1 == "co2 sequestered TH"]; vn = rail[rail.bus1 == "co2 sequestered VN"]
        assert sorted(x.split(" co2")[0] for x in th.index) == ["LA2 1", "LA2 2", "LA2 3", "LA2 5"] and len(vn) == 2
        assert (th.border_class == "maritime_trade").all()
