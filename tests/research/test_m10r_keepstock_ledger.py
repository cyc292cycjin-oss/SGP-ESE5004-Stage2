"""M10R (third-batch close-out): the country cost ledger on a network that keeps the cross-border stock (cross_border.stock_mode =
keep_stock_no_new; R9). Defect (R9, 2026-10-24): the existing_cross_border_fom_ledger meta of an integrated build lists every corridor of the
corridor table, 50 of 67 rows being zero-capacity candidates with annual_fom_eur 0; the keep-stock variant removes those candidate lines / links
but keeps the meta, and s4d_ledger.country_cost_ledger / m12_rhs_audit.objective_constants looked the row's component up in the owner table
before checking the amount -> KeyError '59'. Fix: rows whose component is in the network are booked to its owner (corridor entity of the two end
countries, as in the integrated run); absent rows with 0 EUR are skipped and counted; an absent row with a non-zero amount is an error (the
objective constant would have no owner). Toy tests here; the 56x3h end-to-end test uses the M10R B1.3 solve (skipped when absent)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4d_ledger import country_cost_ledger, ledger_gate, ledger_table, load_length_shares  # noqa: E402

KEEPSTOCK = Path(os.environ.get("M10R_KEEPSTOCK_DIR", ROOT / "results_project/m10r/keepstock_v5"))


def toy(absent_fom: float = 0.0, with_absent: bool = True):
    """Hand-made 'solved' keep-stock network (as tests/research/test_s4d_3.py toy): TH exports 5 MW over the kept TH-LA stock line AB (s_nom =
    min = max = opt = 3 -> no new capacity), LA buys ammonia from the pool. Meta FOM ledger: AB (7 EUR, kept) and the removed zero-capacity
    candidate line 59 (0 EUR, absent) - and optionally an absent row with a non-zero amount."""
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=2, freq="3h")); n.snapshot_weightings.loc[:, :] = 3.0
    for b, car, c in [("A", "AC", "TH"), ("B", "AC", "LA"), ("ASEAN ammonia", "ammonia", "ASEAN")]:
        n.add("Bus", b, carrier=car); n.buses.loc[b, "country"] = c
    n.add("Generator", "gA", bus="A", p_nom=10, marginal_cost=10.0, carrier="gas")
    n.add("Generator", "ASEAN ammonia import", bus="ASEAN ammonia", p_nom=10, marginal_cost=20.0, carrier="ammonia import")
    n.generators["existing_annual_fixed_om_eur"] = [7.0, 0.0]; n.generators.loc[:, "country"] = ["TH", "ASEAN"]
    n.add("Load", "lB", bus="B", carrier="AC"); n.add("Load", "LA ammonia demand", bus="ASEAN ammonia", carrier="ammonia")
    n.loads.loc[:, "country"] = ["LA", "LA"]
    n.add("Line", "AB", bus0="A", bus1="B", x=0.1, s_nom=3, s_nom_min=3, s_nom_max=3, s_nom_extendable=True, capital_cost=2.0, carrier="AC")
    n.lines["s_nom_opt"] = 3.0; n.lines["border_class"] = "cross_border"
    n.generators["p_nom_opt"] = n.generators.p_nom
    idx = n.snapshots
    n.generators_t.p = pd.DataFrame({"gA": [5.0, 5.0], "ASEAN ammonia import": [1.0, 1.0]}, index=idx)
    n.loads_t.p = pd.DataFrame({"lB": [5.0, 5.0], "LA ammonia demand": [1.0, 1.0]}, index=idx)
    n.lines_t.p0 = pd.DataFrame({"AB": [5.0, 5.0]}, index=idx); n.lines_t.p1 = pd.DataFrame({"AB": [-5.0, -5.0]}, index=idx)
    n.buses_t.marginal_price = pd.DataFrame({"A": [10.0, 10.0], "B": [12.0, 12.0], "ASEAN ammonia": [20.0, 20.0]}, index=idx)
    rows = [dict(component_type="Line", component="AB", capacity_2025_mw=3.0, length_km=100.0, annual_fom_eur=7.0, cost_rows=["HVAC overhead"])]
    if with_absent:
        rows.append(dict(component_type="Line", component="59", capacity_2025_mw=0.0, length_km=515.0, annual_fom_eur=absent_fom, cost_rows=["HVAC overhead"]))
    n.meta["existing_cross_border_fom_ledger"] = rows; n.meta["existing_cross_border_fom_eur"] = float(sum(r["annual_fom_eur"] for r in rows))
    n.meta["existing_annual_fixed_om_eur"] = 7.0
    n.objective = 300.0 + 7.0 + 7.0 + 120.0   # gas + existing generator FOM + kept-line FOM (meta ledger) + ammonia import; no new capacity
    return n


def test_toy_keep_stock_ledger_books_kept_line_and_skips_absent_zero_rows():
    n = toy()
    L, ident, diag = country_cost_ledger(n)
    T = ledger_table(L)
    # the kept stock line keeps the corridor rules of the integrated run: FOM 7 to XB:LA|TH, half / half -> 3.5 each; congestion rent (12 - 10) x 5 x 6 = 60 -> -30 each
    assert T.at["TH", "xb_share_infrastructure_cost"] == pytest.approx(3.5) and T.at["LA", "xb_share_infrastructure_cost"] == pytest.approx(3.5)
    assert T.at["TH", "xb_share_congestion_rent"] == pytest.approx(-30.0) and T.at["LA", "xb_share_congestion_rent"] == pytest.approx(-30.0)
    assert T.at["TH", "total"] == pytest.approx(300.0 + 7.0 - 300.0 + 3.5 - 30.0) and T.at["LA", "total"] == pytest.approx(360.0 + 120.0 + 3.5 - 30.0)
    assert ident["relative_error"] < 1e-12 and ledger_gate(ident)["passed"] and ident["difference"] == pytest.approx(0.0)
    x = diag["existing_cross_border_fom_ledger"]
    assert x == dict(rows=2, booked=1, booked_eur=7.0, absent_zero=1, absent_zero_components=["Line:59"])
    # the same network without the absent row gives the same numbers
    L2, ident2, diag2 = country_cost_ledger(toy(with_absent=False))
    assert ledger_table(L2).equals(T) and ident2["countries_plus_bunker"] == ident["countries_plus_bunker"] and diag2["existing_cross_border_fom_ledger"]["absent_zero"] == 0
    # length split as in the integrated run
    sh = pd.DataFrame([dict(component_type="Line", component="AB", country_a="LA", country_b="TH", share_a=0.7, share_b=0.3)])
    L3, ident3, _ = country_cost_ledger(n, sh)
    T3 = ledger_table(L3)
    assert T3.at["TH", "total_length_split"] == pytest.approx(7.0 + 0.3 * (7.0 - 60.0)) and ident3["relative_error_length_split"] < 1e-12


def test_toy_absent_row_with_non_zero_fom_is_an_error():
    with pytest.raises(ValueError, match="not in the network"):
        country_cost_ledger(toy(absent_fom=5.0))


def test_toy_objective_constants_of_the_owen_audit():
    from m12_rhs_audit import Owners, objective_constants
    n = toy(); O = Owners(n); c = objective_constants(n, O)
    # TH: generator FOM 7 (p_nom 10, capital_cost 0); LA|TH: kept line FOM 7 minus PyPSA's constant s_nom x capital_cost = 3 x 2 = 6
    assert c["by_owner"]["TH"] == pytest.approx(7.0) and c["by_owner"]["LA|TH"] == pytest.approx(7.0 - 6.0)
    assert c["pair_components"] == {"Line:AB": dict(pair="LA|TH", eur=pytest.approx(1.0))}
    assert c["total"] == pytest.approx(8.0) and c["fom_ledger"] == dict(rows=2, booked=1, absent_zero=1)
    with pytest.raises(ValueError, match="not in the network"):
        objective_constants(toy(absent_fom=5.0), Owners(toy(absent_fom=5.0)))


def test_toy_ledger_redo_rewrites_the_exports_and_b16_only(tmp_path):
    """s4d_ledger_redo.py: the S4D-3 export block of s2_solve.py on a solved network, into a new folder; the run folder stays read only."""
    from s4d_ledger_redo import FILES, redo
    n = toy(); src = tmp_path / "run"; src.mkdir()
    n.export_to_netcdf(src / "disconnected_T_solved.nc")
    (src / "SOLVE_RECEIPT.json").write_text(json.dumps(dict(objective=float(n.objective), termination_condition="optimal")))
    gates = dict(B16_LEDGER=dict(gate="B16_LEDGER", passed=False, error="'59'"), A4=dict(passed=True, status="EXACT_SEMANTIC_ROUNDTRIP"),
                 acceptance_basis="barconvtol", all_passed_barconvtol=False, all_passed_solver_tolerances=False, all_passed=False)
    (src / "V5_GATES.json").write_text(json.dumps(gates))
    before = {p.name: p.read_bytes() for p in src.iterdir()}
    r = redo(src, tmp_path / "new")
    assert r["b16_before"] == dict(passed=False, relative_error=None, error="'59'") and r["b16_after"]["passed"] and r["b16_after"]["relative_error"] < 1e-12
    assert r["objective"]["equal"] and r["solver_runs"] == 0 and set(r["files"]) == set(FILES)
    new = tmp_path / "new"
    assert all((new / f).exists() for f in FILES) and (new / "LEDGER_REDO.json").exists()
    g = json.loads((new / "V5_GATES.json").read_text())
    assert g["B16_LEDGER"]["passed"] and g["A4"] == gates["A4"] and g["all_passed_barconvtol"] is True and g["all_passed"] is True
    T = pd.read_csv(new / "COUNTRY_COST_LEDGER.csv", index_col=0)
    assert T.at["TH", "xb_share_infrastructure_cost"] == pytest.approx(3.5) and json.loads((new / "LEDGER_IDENTITY.json").read_text())["identity"]["relative_error"] < 1e-12
    assert {p.name: p.read_bytes() for p in src.iterdir()} == before                      # the run folder is untouched
    with pytest.raises(SystemExit):
        redo(src, src)                                                                        # never into the run folder


@pytest.mark.skipif(not (KEEPSTOCK / "SOLVE_RECEIPT.json").exists(), reason="M10R 56x3h keep-stock solve not available locally")
def test_keep_stock_56x3h_ledger_identity_holds_after_the_fix():
    """M10R B1.3 / B2.2: the real keep-stock variant (16 stock lines, 9 stock links kept; 46 lines / 283 links removed; 67 meta rows, 50 absent
    with 0 EUR): B16 holds within 0.01 bn and 1e-6, the Owen audit constants and the M12 allocation compute."""
    import pypsa
    from m12_allocation import allocation_from_network
    from m12_rhs_audit import Owners, objective_constants
    nc = next(iter(sorted(KEEPSTOCK.glob("*_solved.nc"))))
    n = pypsa.Network(str(nc)); rec = json.loads((KEEPSTOCK / "SOLVE_RECEIPT.json").read_text())
    L, ident, diag = country_cost_ledger(n, load_length_shares())
    x = diag["existing_cross_border_fom_ledger"]
    assert x["rows"] == 67 and x["booked"] == 17 and x["absent_zero"] == 50 and x["booked_eur"] == pytest.approx(n.meta["existing_cross_border_fom_eur"])
    assert abs(ident["difference"]) <= 0.01e9 and ident["relative_error"] <= 1e-6 and ident["objective"] == pytest.approx(rec["objective"])
    c = objective_constants(n, Owners(n))
    assert c["fom_ledger"] == dict(rows=67, booked=17, absent_zero=50) and np.isfinite(c["total"])
    A = allocation_from_network(n, load_length_shares())
    assert A["identity"]["passed"] and abs(A["identity"]["difference"]) <= 0.01e9
