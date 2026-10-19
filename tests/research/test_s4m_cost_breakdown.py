"""S4M supplement 01 (S1 item 3): the capital-cost breakdown export must reconstruct every extendable component exactly (<= 1e-6), including the layer composites."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


def _costs(ann):
    rows = {"onwind": dict(investment=600.0, FOM=1.0, lifetime=25.0), "offwind": dict(fixed=100.0), "offwind-ac-station": dict(fixed=10.0),
            "offwind-ac-connection-submarine": dict(fixed=2.0), "offwind-ac-connection-underground": dict(fixed=1.0),
            "HVAC overhead": dict(fixed=3.0), "HVAC submarine": dict(fixed=7.0), "HVDC overhead": dict(fixed=4.0), "HVDC submarine": dict(fixed=9.0), "HVDC inverter pair": dict(fixed=50.0),
            "H2 (g) pipeline": dict(fixed=1.5), "H2 (g) submarine pipeline": dict(fixed=2.5), "CCGT": dict(fixed=200.0, efficiency=0.6), "biomass CHP capture": dict(fixed=300.0),
            "BtL": {"fixed": 500.0, "efficiency": 0.4, "C stored": 0.7}, "Fischer-Tropsch": dict(fixed=800.0, efficiency=0.9)}
    c = pd.DataFrame.from_dict(rows, orient="index").rename_axis("technology")
    c.loc["onwind", "fixed"] = (ann(0.07, 25.0) + 0.01) * 600.0
    return c


def _network(tmp_path):
    n = pypsa.Network(); n.set_snapshots(pd.RangeIndex(2))
    for b, car in [("N1", "AC"), ("N2", "AC"), ("N1 H2", "H2"), ("N2 H2", "H2"), ("N1 gas", "gas"), ("co2 atm", "co2"), ("N1 co2 stored", "co2 stored"), ("solid biomass", "solid biomass"), ("N1 oil", "oil")]:
        n.add("Bus", b, carrier=car)
    from s4m_cost_breakdown import annuity
    n.add("Generator", "N1 onwind-2025", bus="N1", carrier="onwind", p_nom_extendable=True, capital_cost=(annuity(0.07, 25.0) + 0.01) * 600.0)
    n.add("Generator", "N1 offwind-ac-2025 c1", bus="N1", carrier="offwind-ac", p_nom_extendable=True, capital_cost=100.0 + 10.0 + 1.25 * (8.0 * 2.0 + 20.0 * 1.0))
    n.add("Line", "L1", bus0="N1", bus1="N2", carrier="AC", length=100.0, s_nom_extendable=True, x=1.0, r=0.1, capital_cost=100.0 * (0.7 * 3.0 + 0.3 * 7.0))   # carrier as in the research network (PyPSA default is empty)
    n.lines["underwater_fraction"] = 0.3
    n.add("Link", "D1", bus0="N1", bus1="N2", carrier="DC", length=50.0, p_nom_extendable=True, capital_cost=50.0 * (0.5 * 4.0 + 0.5 * 9.0) + 50.0)
    n.add("Link", "D1-reversed", bus0="N2", bus1="N1", carrier="DC", length=0.0, p_nom_extendable=True, capital_cost=0.0)
    n.add("Link", "H2 pipeline N1 -> N2", bus0="N1 H2", bus1="N2 H2", carrier="H2 pipeline", length=80.0, p_nom_extendable=True, capital_cost=80.0 * (0.75 * 1.5 + 0.25 * 2.5))
    n.add("Link", "N1 CCGT CC", bus0="N1 gas", bus1="N1", bus2="co2 atm", bus3="N1 co2 stored", carrier="CCGT CC", efficiency=0.55, efficiency2=0.02, efficiency3=0.18,
          p_nom_extendable=True, capital_cost=200.0 * 0.6 + 300.0 * 0.18)
    n.add("Link", "N1 electrobiofuels", bus0="solid biomass", bus1="N1 oil", bus2="N1 H2", carrier="electrobiofuels", efficiency=1.3, efficiency2=-1.1, p_nom_extendable=True,
          capital_cost=500.0 * 0.4 + 0.7 * 800.0 * 0.9)
    n.links["underwater_fraction"] = 0.0; n.links.loc["D1", "underwater_fraction"] = 0.5; n.links.loc["H2 pipeline N1 -> N2", "underwater_fraction"] = 0.25
    n.links["twin_of"] = ""; n.links.loc["D1-reversed", "twin_of"] = "D1"
    n.links["capture_cost_row"] = ""; n.links.loc["N1 CCGT CC", "capture_cost_row"] = "biomass CHP capture (generic post-combustion, PyPSA-Eur practice)"
    rel = "research_inputs/renewable_v5/OFFWIND_CONNECTION_DISTANCE_S4C1.csv"; p = tmp_path / rel; p.parent.mkdir(parents=True)
    p.write_text("tech,node,cls,average_distance_km,landfall_km,line_length_factor\noffwind-ac,N1,1,8.0,20.0,1.25\n")
    n.meta["research_cost_layer_s4c1"] = dict(offwind_distance_table=dict(file=rel, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    n.meta["research_finance"] = dict(uniform_rate=0.07, rates_by_carrier={"Generator:onwind": dict(cost_row="onwind", discount_rate=0.07), "Generator:offwind-ac": dict(cost_row="offwind"),
                                                                           "Link:DC": dict(cost_row="HVDC overhead"), "Link:H2 pipeline": dict(cost_row="H2 (g) pipeline"),
                                                                           "Link:CCGT CC": dict(cost_row="CCGT"), "Link:electrobiofuels": dict(cost_row="electrobiofuels")})
    return n


def test_breakdown_reconstructs_every_extendable_component(tmp_path):
    from s4m_cost_breakdown import annuity, breakdown, write_breakdown
    n = _network(tmp_path); costs = _costs(annuity)
    T, s = breakdown(n, costs, repo=tmp_path)
    assert s["extendable"] == 8 and s["matched"] == 8 and s["matched_share"] == 1.0 and s["unmatched_by_carrier"] == {}
    assert s["offwind_distance_table"]["status"] == "ok"
    rules = dict(zip(T.name, T.match_rule))
    assert rules["N1 onwind-2025"] == "plain" and rules["N1 offwind-ac-2025 c1"] == "composite:offwind_connection"
    assert rules["L1"] == "composite:length_x_subsea_mix" and rules["D1"] == "composite:length_x_subsea_mix_plus_inverter_pair" and rules["D1-reversed"] == "composite:zero_cost_reversed_twin"
    assert rules["H2 pipeline N1 -> N2"] == "composite:length_x_subsea_mix" and rules["N1 CCGT CC"] == "composite:base_x_efficiency_plus_capture_x_co2"
    assert rules["N1 electrobiofuels"] == "composite:btl_plus_scaled_fischer_tropsch"
    assert float(T.residual_eur.abs().max()) == 0.0 and s["table_fixed_inconsistent"] == 0
    # every composite term is written out, so the split can be redone from the row values
    import json
    terms = json.loads(T.set_index("name").loc["N1 offwind-ac-2025 c1", "composite_terms"])
    assert terms["distance_km"] == 8.0 and abs(sum(v for k, v in terms.items() if k in ("offwind", "offwind-ac-station") or "connection" in k) - 155.0) < 1e-9
    # without the repo the offshore connection cost cannot be rebuilt: reported, not forced
    T2, s2 = breakdown(n, costs, repo=None)
    assert s2["matched"] == 7 and s2["unmatched_by_carrier"] == {"Generator:offwind-ac": 1} and s2["offwind_distance_table"]["status"] == "not_resolved"
    # a tampered table is refused by the SHA256 check
    (tmp_path / "research_inputs/renewable_v5/OFFWIND_CONNECTION_DISTANCE_S4C1.csv").write_text("tech,node,cls,average_distance_km,landfall_km,line_length_factor\noffwind-ac,N1,1,9.0,20.0,1.25\n")
    _, s3 = breakdown(n, costs, repo=tmp_path); assert s3["offwind_distance_table"]["status"] == "sha_mismatch" and s3["matched"] == 7
    out = tmp_path / "out"; out.mkdir(); (out / "EXPORTS.json").write_text("{}")
    write_breakdown(n, costs, out, repo=None)
    ex = json.loads((out / "EXPORTS.json").read_text()); assert set(ex) == {"COMPONENT_COST_BREAKDOWN.csv", "COMPONENT_COST_BREAKDOWN_SUMMARY.json"} and ex["COMPONENT_COST_BREAKDOWN.csv"]["bytes"] > 0
