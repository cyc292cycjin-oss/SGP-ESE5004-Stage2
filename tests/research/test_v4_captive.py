"""V4 W08 checklist sections 5 and 6: captive coal option (b) under reading I (decisions 204, 208) and the ID fuelwood outside the national balance
(decisions 206, 210 item 4 b, 211 item 2). The chain runs in a temporary folder; no solver."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
W08 = ROOT / "research/06_scope_redesign/p1_v4_w08_20261106"


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    import v4_industry as V
    from v4_common import V4_MAIN
    I = V.Inputs(); ch = V.Chain(tmp_path_factory.mktemp("chain"))
    s = dict(V4_MAIN, anchor_mode="ras"); case = {}; out = {}
    for code, _, f in V.build_steps(I, s)[:4]:
        case = f(case); out[code] = (dict(case), ch.run(case))
    return I, out


def test_captive_moves_are_tonnes_times_ncv():
    import v4_products as P
    it = P.load_items()["captive"]
    t = pd.read_csv(ROOT / "research_inputs/industry_v4/CAPTIVE_COAL_2019.csv", keep_default_na=False)
    idr = t[t.country == "ID"].iloc[0]
    assert float(idr.gj_per_t) == 20.29 and float(idr.coal_kt) == pytest.approx(10589.2, abs=0.1)
    assert it[0] == ("ID", "other", "coal", pytest.approx(float(idr.coal_kt) * 20.29 / 3.6 * 1e3, rel=1e-15))
    assert it[0][3] / 1e6 == pytest.approx(59.68, abs=0.01) and -it[1][3] / 1e6 == pytest.approx(19.21, abs=0.01)
    mm = [m for m in it if m[0] == "MM"]; ph = [m for m in it if m[0] == "PH"]
    assert mm[0][1] == "non-metallic minerals" and mm[0][3] == pytest.approx(66.09e3 * 23.26 / 3.6, rel=1e-3) and -mm[1][3] / 1e6 == pytest.approx(0.116, abs=1e-3)
    assert {m[1] for m in ph if m[2] == "coal"} == {"other", "paper pulp and print"} and [m for m in ph if m[2] == "electricity"][0][1] == "paper pulp and print"
    assert sum(m[3] for m in ph if m[2] == "coal") == pytest.approx((181.54 + 309.94) * 1e3 * 22.058 / 3.6, rel=1e-3)
    assert {m[0] for m in it} == {"ID", "MM", "PH"}


def test_multipliers_unchanged_and_s4_equals_reference(runs):
    I, out = runs
    a3, a4 = out["S3"][1], out["S4"][1]
    for c in a3["snap"]:
        assert a4["snap"][c]["ind_mult"] == a3["snap"][c]["ind_mult"]   # reading I: the ATS industry multiplier is not touched
    R = pd.read_csv(W08 / "REFERENCE_V4_MAIN.csv")
    for c, x in a4["snap"].items():
        assert abs(x["T"] / 1e6 - float(R[(R.step == "S4") & (R.country == c)].T_v2_2050_TWh.iloc[0])) <= 1e-6
    d = {c: (a4["snap"][c]["T"] - a3["snap"][c]["T"]) / 1e6 for c in ("ID", "PH", "MM")}
    assert d["ID"] < 0 and d["PH"] < 0 and d["MM"] < 0


def test_id_fuelwood_outside_the_balance(runs):
    """Decision 206 / 210 item 4 b: 2010-2017 mean 29,510 thousand m3 x 9.135 GJ/m3 = 74.88 TWh; decision 211 item 2: only the non-paper share
    stays (the paper-row fuelwood is a self-produced residue); grows at the v3 multiplier 2.6186 outside the anchor; the ID seed keeps only
    charcoal 0.80 and biodiesel 3.70 TWh of the industrial biomass."""
    I, out = runs
    assert I.fw["mean_mwh"] / 1e6 == pytest.approx(74.88, abs=0.005)
    case, res = out["S2"]
    add = [a for a in res["ats_add_info"] if a["country"] == "ID" and a["carrier"] == "biomass"][0]
    assert add["d_mwh"] == pytest.approx(I.fw["mean_mwh"] * I.fw["share_non_paper"], rel=1e-12)
    assert add["m_target"] == pytest.approx(2.6186, abs=5e-5)
    assert add["base_added_mwh"] * add["m_row"] == pytest.approx(add["d_mwh"] * add["m_target"], rel=1e-12)   # 2050 = true 2019 x v3 multiplier
    seed = float(case["d1"][("ID", "Industry", "biomass", "IndustryFinalEnergy")])
    assert seed / 1e6 == pytest.approx(0.80 + 3.70, abs=0.01)
    assert res["snap"]["ID"]["ind19_true"] - res["snap"]["ID"]["ind19"] == pytest.approx(add["d_mwh"] - add["base_added_mwh"], rel=1e-12)
