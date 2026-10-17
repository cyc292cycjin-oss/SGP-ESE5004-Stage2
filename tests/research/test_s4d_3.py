"""S4D-3 (decision 91a): country cost ledger, identity gate B16_LEDGER, nodal prices."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4b_acceptance import S3B_SET, S4B_MAIN_SET  # noqa: E402
from s4d_ledger import POOL, country_cost_ledger, ledger_gate, ledger_table, nodal_prices  # noqa: E402

SHARES = ROOT / "research_inputs/corridors/XB_LENGTH_SHARES_S4D3.csv"
TRIAL = ROOT / "results_project/s4d/ledger_trial_s4c/S4D3_LEDGER_TRIAL.json"


def toy():
    """Hand-made 'solved' network: TH exports 5 MW over a congested TH-LA line (duals 10 / 12), LA buys ammonia from the regional pool
    (dual 20) through a national load on the regional bus; two 3-hour snapshots."""
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h")); n.snapshot_weightings.loc[:, :] = 3.0
    for b, car, c in [("A", "AC", "TH"), ("B", "AC", "LA"), ("ASEAN ammonia", "ammonia", "ASEAN")]:
        n.add("Bus", b, carrier=car); n.buses.loc[b, "country"] = c
    n.add("Generator", "gA", bus="A", p_nom=10, marginal_cost=10.0, carrier="gas")
    n.add("Generator", "ASEAN ammonia import", bus="ASEAN ammonia", p_nom=10, marginal_cost=20.0, carrier="ammonia import")
    n.generators["existing_annual_fixed_om_eur"] = [7.0, 0.0]
    n.generators.loc[:, "country"] = ["TH", "ASEAN"]
    n.add("Load", "lB", bus="B", carrier="AC"); n.add("Load", "LA ammonia demand", bus="ASEAN ammonia", carrier="ammonia")
    n.loads.loc[:, "country"] = ["LA", "LA"]
    n.add("Line", "AB", bus0="A", bus1="B", x=0.1, s_nom=3, s_nom_extendable=True, capital_cost=2.0, carrier="AC")
    n.lines["s_nom_opt"] = 5.0; n.lines["border_class"] = "cross_border"
    n.generators["p_nom_opt"] = n.generators.p_nom
    idx = n.snapshots
    n.generators_t.p = pd.DataFrame({"gA": [5.0, 5.0], "ASEAN ammonia import": [1.0, 1.0]}, index=idx)
    n.loads_t.p = pd.DataFrame({"lB": [5.0, 5.0], "LA ammonia demand": [1.0, 1.0]}, index=idx)
    n.lines_t.p0 = pd.DataFrame({"AB": [5.0, 5.0]}, index=idx); n.lines_t.p1 = pd.DataFrame({"AB": [-5.0, -5.0]}, index=idx)
    n.buses_t.marginal_price = pd.DataFrame({"A": [10.0, 10.0], "B": [12.0, 12.0], "ASEAN ammonia": [20.0, 20.0]}, index=idx)
    n.objective = 300.0 + 7.0 + 4.0 + 120.0   # gas + existing FOM + line capex (5 - 3) x 2 + ammonia import
    return n


def test_toy_ledger():
    n = toy()
    L, ident, diag = country_cost_ledger(n)
    T = ledger_table(L)
    # TH: gas 300 + FOM 7 - export revenue 10 x 5 x 6 = 300, half of the corridor (capex 4 - congestion rent (12 - 10) x 5 x 6 = 60) = -28
    assert T.at["TH", "total"] == pytest.approx(7.0 - 28.0)
    # LA: import 12 x 5 x 6 = 360, ammonia from the pool 20 x 6 = 120 (load on the regional bus booked to LA), corridor half -28
    assert T.at["LA", "total"] == pytest.approx(360.0 + 120.0 - 28.0)
    assert T.at["LA", "liquid_pool_ammonia"] == pytest.approx(120.0)
    assert T.at[POOL, "total"] == pytest.approx(0.0)
    assert T.at["TH", "xb_share_congestion_rent"] == pytest.approx(-30.0) and T.at["TH", "xb_share_infrastructure_cost"] == pytest.approx(2.0)
    assert ident["relative_error"] < 1e-12 and ledger_gate(ident)["passed"]
    # length split: 30 % / 70 % of the corridor
    sh = pd.DataFrame([dict(component_type="Line", component="AB", country_a="LA", country_b="TH", share_a=0.7, share_b=0.3)])
    L2, ident2, _ = country_cost_ledger(n, sh)
    T2 = ledger_table(L2)
    assert T2.at["TH", "total_length_split"] == pytest.approx(7.0 - 0.3 * 56.0) and T2.at["LA", "total_length_split"] == pytest.approx(480.0 - 0.7 * 56.0)
    assert ident2["relative_error_length_split"] < 1e-12
    # an objective term without a component breaks the identity (difference reported)
    n.objective += 50.0
    _, ident3, _ = country_cost_ledger(n)
    assert not ledger_gate(ident3)["passed"] and ident3["difference"] == pytest.approx(-50.0)
    _, ident4, _ = country_cost_ledger(n, extra_terms={"gap_co2_slack_x_penalty_eur": 50.0})
    assert ledger_gate(ident4)["passed"]


def test_nodal_prices_layout():
    p = nodal_prices(toy())
    assert list(p.columns[:6]) == ["node", "carrier", "country", "mean", "min", "max"] and p.loc["B", "mean"] == pytest.approx(12.0)
    assert p.shape == (3, 7) and p.loc["ASEAN ammonia", "2013-01-01"] == pytest.approx(20.0)


def test_gate_in_both_sets():
    assert "B16_LEDGER" in S4B_MAIN_SET and "B16_LEDGER" in S3B_SET


@pytest.mark.skipif(not SHARES.exists(), reason="length shares not built")
def test_length_shares():
    s = pd.read_csv(SHARES)
    assert len(s) == 95 and ((s.share_a + s.share_b - 1.0).abs() < 1e-3).all() and (s.share_a.between(0, 1)).all()
    assert (s.samples_other < 50).all()   # every segment mostly inside the two end countries (land + EEZ)
    assert s.component.is_unique or s.groupby(["component_type", "component"]).size().max() == 1


@pytest.mark.skipif(not TRIAL.exists(), reason="ledger trial not run")
def test_trial_on_s4c_smokes():
    t = json.loads(TRIAL.read_text())
    assert set(t) == {"integrated", "disconnected", "integrated_nze"}
    for s, v in t.items():
        assert v["gate"]["passed"] and v["identity"]["relative_error"] < 1e-9 and v["identity"]["relative_error_length_split"] < 1e-9
        assert abs(v["identity"]["difference_sources"]["asean_pool_surplus"]) < 1e3 and v["length_shares_missing"] == []
        assert v["one_port_owned_by_country_column"]["Load"] == 77
