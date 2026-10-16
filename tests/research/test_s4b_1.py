"""S4B-1 (decision 77): construction units counted (incl. those without a start year), operating units without a start year unresolved,
GIPT-2026 non-operating units removed from the stock."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
FV = ROOT / "research_inputs/fleet_v5"
NET = ROOT / "results_project/s4b/build_s4b1/integrated/integrated_2920_3h_unsolved.nc"


def test_tables():
    con = pd.read_csv(FV / "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv"); opr = pd.read_csv(FV / "FLEET_UNRESOLVED_OPERATING_NO_START_YEAR.csv")
    rem = pd.read_csv(FV / "FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv"); s4a = pd.read_csv(FV / "FLEET_ADDITIONS_2050.csv")
    assert len(con) == 74 and (con.Status == "construction").all() and con.start_year.isna().all() and (con.assumed_start_year == 2026).all() and (con.retire_year > 2050).all()
    assert len(opr) == 170 and (opr.Status == "operating").all()
    assert not set(con.gem_unit_id) & set(s4a.gem_unit_id) and con.node.notna().all() and con.node.str[:2].eq(con.country).all()
    assert len(rem) == 11 and rem.capacity_mw.sum() == pytest.approx(2854.4) and rem.removal_reason.str.contains("data correction").all()
    x = pd.read_csv(FV / "FLEET_S1_NOT_INHERITED_ITEM77.csv")
    assert x.s1_asset.nunique() == 45 and x[x.item77_treatment.str.startswith("counted")].gipt_2026_status.isin(["construction"]).all()   # only construction is counted
    t = pd.read_csv(FV / "FLEET_STOCK_2050_S4B1_BY_COUNTRY_CLASS.csv")
    assert (t.after_s4b1_mw - (t.before_s4a_mw + t.added_construction_no_start_mw - t.removed_not_operating_mw)).abs().max() < 1e-6


def test_config():
    from phase4_static import config
    F = config(ROOT, "integrated")["research"]["fleet"]
    assert F["include_construction"] is True and F["include_construction_no_start_year"] is True and F["remove_not_operating_gipt2026"] is True


@pytest.mark.skipif(not NET.exists(), reason="S4B-1 build not present")
def test_built_network_stock():
    import pypsa
    n = pypsa.Network(str(NET)); m = n.meta; ids = m["existing_unit_components"]; gone = m["existing_unit_removed_s4b1"]
    rem = pd.read_csv(FV / "FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv")
    assert set(gone) == set(rem.identity) and not set(gone) & set(ids)
    s4b1 = {k: v for k, v in ids.items() if v.get("s4b1_added")}
    assert sum(v["capacity_mw"] for v in s4b1.values()) == pytest.approx(9244.4)   # 74 units minus the 70 MW waste-to-energy
    for comp in ["existing_survivor::GPD:WRI1023893", "existing_survivor::PH_Mindanao6 1::Oil::77ba091e7217"]:
        assert comp not in n.links.index                                              # every unit removed -> component removed
    z = n.links.loc["existing_survivor::TH2 2::CCGT::1580dccb80c4"]
    left = sum(v["capacity_mw"] for v in ids.values() if v["component"] == z.name)
    assert z.p_nom * z.efficiency == pytest.approx(left)
    r = m["research_fleet_removed"]; assert r["mw"] == pytest.approx(2854.4) and r["fom_eur"] > 0
