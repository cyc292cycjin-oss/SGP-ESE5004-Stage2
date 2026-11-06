"""V4 W08 checklist section 4: (ii) corrections - ID household motor gasoline to road, rail parent out of the D1 seed and of the land-transport
accounts (decision 210 item 6; decision 209 F2 / F6 option b). The chain runs in a temporary folder; no solver."""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
W08 = ROOT / "research/06_scope_redesign/p1_v4_w08_20261106"


@pytest.fixture(scope="module")
def s3_runs(tmp_path_factory):
    import v4_industry as V
    from v4_common import V4_MAIN
    I = V.Inputs(); ch = V.Chain(tmp_path_factory.mktemp("chain"))
    out = {}
    for mode in ("ras", "iid"):
        s = dict(V4_MAIN, anchor_mode=mode); case = {}
        for code, _, f in V.build_steps(I, s)[:3]:
            case = f(case)
        out[mode] = (case, ch.run(case))
    return I, out


def test_no_parent_rows_and_id_household_gasoline(s3_runs):
    I, out = s3_runs
    case, res = out["ras"]
    d1 = case["d1"]
    par = d1[[k[3] == "TransportEmbeddedFuelParent" for k in d1.index]]
    assert len(par) > 0 and float(par.abs().max()) == 0.0
    ats = res["ats"]
    assert float(pd.to_numeric(ats[ats.account == "TransportEmbeddedFuelParent"].value_2050_mwh, errors="coerce").fillna(0).abs().sum()) == 0.0
    k = ("ID", "Residential", "oil", "ResidentialFuel")
    assert d1[k] == pytest.approx(I.B[k] - 197.0317686944e6, abs=1e-3)
    assert I.gas["ID"] == pytest.approx(196.94e6, rel=1e-3)   # checklist: 196.94 TWh (S5p, 2019) = 197.03 TWh after the SDMX base (I2 0.1 item 1)


@pytest.mark.parametrize("mode,ref", [("ras", "MAIN"), ("iid", "IID")])
def test_land_fuel_and_ev_equal_the_reference(s3_runs, mode, ref):
    _, out = s3_runs
    R = pd.read_csv(W08 / f"REFERENCE_V4_{ref}.csv")
    r = R[(R.step == "S3") & (R.country == "ID")].iloc[0]
    sec = out[mode][1]["ats_sectors"]["ID"]
    assert abs(sec["land"] / 1e6 - float(r.land_fuel_2050_TWh)) <= 1e-6
    import v4_industry as V   # V4 D1 (decision 214 item 9): the EV factor is the unrounded registry value; the W08 reference column used 0.30215
    assert abs(sec["ev"] / 1e6 - float(r.ev_electricity_2050_TWh) * V.EV_FACTOR / V.EV_FACTOR_W08) <= 1e-6
    assert sec["ev"] == pytest.approx(sec["land"] * V.EV_FACTOR, rel=1e-12)
    if mode == "iid":   # checklist section 4 acceptance (I2 S7 = S3 for transport under IId): ID land fuel 1,199.87, EV 362.54 TWh
        assert sec["land"] / 1e6 == pytest.approx(1199.87, abs=0.01) and sec["ev"] / 1e6 == pytest.approx(362.54, abs=0.01)


def test_land_transport_accounts_switch():
    import s2_layers as L
    off = {"research": {"demand": {}}}
    on = {"research": {"demand": {"v4": {"enabled": True, "rail_parent": "children_only"}}}}
    assert "TransportEmbeddedFuelParent" in L.land_transport_accounts(off)
    assert L.land_transport_accounts(on) == {"RoadResidualFuel", "TransportNEC"}
