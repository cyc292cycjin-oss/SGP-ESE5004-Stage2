"""V4 W08 checklist section 7: sub-sector products (decisions 204, 206, 208, 210 items 5 / 7). Each product's 2019 deduction log and 2050 vector
equal the reference engine; 'other' is non-negative; the parts add up to T_v2. The chain runs in a temporary folder; no solver."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
W08 = ROOT / "research/06_scope_redesign/p1_v4_w08_20261106"


@pytest.fixture(scope="module", params=["ras", "iid"])
def final(request, tmp_path_factory):
    import v4_industry as V
    from v4_common import V4_MAIN
    I = V.Inputs(); ch = V.Chain(tmp_path_factory.mktemp("chain"))
    s = dict(V4_MAIN, anchor_mode=request.param); case = {}
    for code, _, f in V.build_steps(I, s)[:14]:   # up to S6c
        case = f(case)
    return request.param, case, ch.run(case)


def test_deduction_log_equals_reference(final):
    mode, _, res = final
    ref = pd.read_csv(W08 / "tables/W08_REF_DEDUCTION_LOG.csv", keep_default_na=False)
    ref = ref[ref.run == ("main" if mode == "ras" else "iid")].drop(columns="run").reset_index(drop=True)
    mine = pd.DataFrame(res["dlog"]).reset_index(drop=True)
    assert list(mine.country) == list(ref.country) and list(mine["product"]) == list(ref["product"]) and list(mine.row) == list(ref.row)
    for col in ("fuel_wanted_mwh", "el_wanted_mwh", "fuel_from_row_mwh", "el_from_row_mwh", "fuel_from_other_mwh", "el_from_other_mwh", "not_found_mwh", "capped_mwh"):
        assert (mine[col].astype(float) - ref[col].astype(float)).abs().max() <= 1e-6, col


def test_product_vectors_other_and_conservation(final):
    import v4_products as P
    mode, case, res = final
    it = P.load_items()
    for cc, items in case["products"].items():
        for x in items:
            if x.get("v2050"):
                assert res["extra"][cc][x["name"]] == x["v2050"]
    for cc, s in res["snap"].items():
        L = s["L"]
        assert all(v >= -1e-9 for v in L["other"].values()), cc
        tot = sum(sum(v.values()) for v in L["parts"].values())
        assert abs(tot - L["T"]) <= 1e-9 * max(1.0, L["T"]), cc
    R = pd.read_csv(W08 / f"REFERENCE_V4_{'MAIN' if mode == 'ras' else 'IID'}.csv")
    for c, x in res["snap"].items():
        r = R[(R.step == "S6c") & (R.country == c)].iloc[0]
        assert abs(x["T"] / 1e6 - float(r.T_v2_2050_TWh)) <= 1e-6 and abs(x["other"] / 1e6 - float(r.other_2050_TWh)) <= 1e-6
    # checklist acceptance details that do not depend on the anchor mode
    assert it["bn_neu_methanol"]["gas_2019_mwh"] / 1e6 == pytest.approx(3.45, abs=0.005)
    assert res["snap"]["BN"]["L"]["by_sub"]["methanol"] > 0 and "ID" in case["meoh_drop"]
    assert P.HVC_C2 == pytest.approx(5.191, abs=5e-4) and sum(P.HVC_VEC_B.values()) == pytest.approx(4.627, abs=5e-4)


def test_pulp_paper_black_liquor_outside(final):
    import v4_products as P
    it = P.load_items()
    pp = it["pp"]["ID"]
    assert pp["closed_loop_bl50"] / 1e6 == pytest.approx(95.4, abs=0.05)
    assert pp["v2050"]["biomass"] == pytest.approx(0.0, abs=1e-6)   # ID: black liquor >= biomass part -> all biomass single-listed outside T_v2
    assert it["pp"]["TH"]["closed_loop_bl50"] / 1e6 == pytest.approx(10.1, abs=0.05) and it["pp"]["VN"]["closed_loop_bl50"] / 1e6 == pytest.approx(3.8, abs=0.05)
