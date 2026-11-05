"""V3.1 (decision 195, V3_FIX_INSTRUCTION.md sections 2-4): the bunker net-zero written per metering flow, the premises of validate_bunker_account,
the static zero-slack check and the downstream shape adaptations. No solver is called (models are built, never solved)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4c_layers import (BUNKER_CO2_BUS, BUNKER_PRICE_NOTE, BUNKER_ROW, bunker_account_premises, bunker_metering_links,   # noqa: E402
                        install_bunker_net_zero, validate_bunker_account)

AIRPORTS = ("AA", "BB")


def _toy(n_snap=3, removal=None, pmin=0.0, pmin_t=None, e_initial=0.0, standing=0.0, coef=0.2571, weights=None):
    """two airports, each: fossil meter (bus0 national oil, bus1 final, bus2 bunker account) + non-fossil twin; the account Store."""
    import pypsa
    n = pypsa.Network(); n.set_snapshots(pd.date_range("2013-01-01", periods=n_snap, freq="3h"))   # datetime snapshots as in the research networks (linopy coords are datetime64)
    if weights is not None:
        n.snapshot_weightings.loc[:, :] = np.asarray(weights, dtype=float)[:, None]
    n.add("Bus", BUNKER_CO2_BUS, carrier="co2 bunkers"); n.add("Bus", "X", carrier="co2 stored")
    for a in AIRPORTS:
        fb = f"{a} aviation international oil final"
        for b, car in [(f"{a} oil", "oil"), (f"{a} oil non-fossil", "oil non-fossil"), (fb, "oil final energy")]:
            n.add("Bus", b, carrier=car)
        n.add("Generator", f"{a} fossil", bus=f"{a} oil", p_nom=1e3, marginal_cost=10.0)
        n.add("Generator", f"{a} non-fossil", bus=f"{a} oil non-fossil", p_nom=1e3, marginal_cost=100.0)
        n.add("Link", f"{a} aviation international oil meter", bus0=f"{a} oil", bus1=fb, bus2=BUNKER_CO2_BUS, efficiency=1.0, efficiency2=coef,
              p_nom_extendable=True, p_min_pu=pmin)
        n.add("Link", f"{a} aviation international oil meter non-fossil", bus0=f"{a} oil non-fossil", bus1=fb, efficiency=1.0, p_nom_extendable=True)
        n.add("Load", f"{a} bunker", bus=fb, p_set=5.0)
    n.add("Store", BUNKER_CO2_BUS, bus=BUNKER_CO2_BUS, carrier="co2 bunkers", e_nom_extendable=True, e_min_pu=-1.0, e_initial=e_initial, e_cyclic=False,
          standing_loss=standing)
    if pmin_t is not None:
        n.links_t.p_min_pu[f"{AIRPORTS[0]} aviation international oil meter"] = pd.Series(pmin_t, index=n.snapshots, dtype=float)
    if removal == "dac":   # a removal routed into the account (efficiency < 0)
        n.add("Generator", "dac power", bus="X", p_nom=1e3)
        n.add("Link", "foreign DAC", bus0="X", bus1=BUNKER_CO2_BUS, efficiency=-1.0, p_nom=1e3)
    elif removal == "bus0":   # a withdrawal from the account
        n.add("Link", "account outlet", bus0=BUNKER_CO2_BUS, bus1="X", efficiency=1.0, p_nom=1e3)
    return n


def _model(n):
    n.optimize.create_model()
    return n.model


# ----------------------------------------------------------------------------------------------------------- (a) the per-variable rows
def test_hook_writes_one_zero_row_per_snapshot_and_metering_link():
    n = _toy(n_snap=4); m = _model(n)
    install_bunker_net_zero(n)
    assert BUNKER_ROW in m.constraints
    con = m.constraints[BUNKER_ROW]
    meters = [f"{a} aviation international oil meter" for a in AIRPORTS]
    assert dict(con.labels.sizes) == {"snapshot": 4, "Link": 2} and list(map(str, con.labels.coords["Link"].values)) == meters
    assert (np.asarray(con.labels.values) >= 0).all() and set(np.asarray(con.sign.values).ravel()) == {"="} and float(np.abs(np.asarray(con.rhs.values)).max()) == 0.0
    v = np.asarray(con.vars.values); c = np.asarray(con.coeffs.values)
    assert v.shape[-1] == 1 and (c == 1.0).all()   # one term per row, coefficient 1
    p = np.asarray(m.variables["Link-p"].labels.sel(Link=meters).transpose("snapshot", "Link").values)
    assert (v[..., 0] == p).all()   # the rows are exactly Link-p(meter, t) == 0
    assert "Store-e" not in {m.variables.get_label_position(int(x))[0] for x in v.ravel()}   # no final-level row on the account any more
    with pytest.raises(ValueError, match="already installed"):
        install_bunker_net_zero(n)


def test_premises_measured_on_the_toy():
    n = _toy()
    acc = validate_bunker_account(n)
    assert bunker_metering_links(acc) == [f"{a} aviation international oil meter" for a in AIRPORTS]
    pre = bunker_account_premises(n, acc["store"], acc["ports"])
    assert pre["passed"] and pre["ports"] == 2 and pre["metering_links"] == 2 and pre["removal_ports"] == 0
    assert pre["coefficient_min"] == pytest.approx(0.2571) and pre["p_min_pu_static_min"] == 0.0 and pre["e_initial"] == 0.0 and not pre["e_cyclic"]
    assert pre["stores_weighting_min"] > 0 and pre["objective_weighting_min"] > 0


# ----------------------------------------------------------------------------------------------------------- (b) refusals
@pytest.mark.parametrize("kw, match", [
    (dict(removal="dac"), "removal port"),
    (dict(removal="bus0"), "not a Link emission port"),
    (dict(pmin=-0.5), r"\(ii\) metering link p_min_pu < 0"),
    (dict(pmin_t=[0.0, -0.1, 0.0]), r"\(ii\) metering link time-varying p_min_pu < 0"),
    (dict(e_initial=5.0), "Store contract broken"),
    (dict(coef=0.0), r"\(i\) port coefficient <= 0"),
    (dict(standing=0.01), r"\(iii\) account standing_loss"),
    (dict(weights=[3.0, 0.0, 3.0]), r"\(iv\) stores weighting <= 0"),
])
def test_validate_refuses_every_failed_premise(kw, match):
    with pytest.raises(ValueError, match=match):
        validate_bunker_account(_toy(**kw))


def test_hook_refuses_a_network_failing_a_premise():
    n = _toy(pmin=-0.5); _model(n)
    with pytest.raises(ValueError, match="premise failed"):
        install_bunker_net_zero(n)


# ----------------------------------------------------------------------------------------------------------- (c) zero-slack check
def _old_form(n):
    """the pre-V3.1 hook: final-snapshot account level <= 0 (the zero-slack row)."""
    m = n.model
    m.add_constraints(m["Store-e"].sel(snapshot=n.snapshots[-1], Store=BUNKER_CO2_BUS) <= 0.0, name=BUNKER_ROW)


def test_zero_slack_check_refuses_the_old_form_and_passes_the_fix():
    from zero_slack_check import bunker_check, scan_hooks
    n = _toy(); n.meta["required_constraint_hooks"] = ["research_bunker_net_zero"]; m = _model(n); _old_form(n)
    rows = {r["name"]: r for r in scan_hooks(n, m, n)}
    r = rows[BUNKER_ROW]
    assert r["form"] == "final_store_level" and r["verdict"] == "zero_slack_forcing_row"
    assert r["cap_max"] == 0.0 and r["inflow_ports"] == 2 and r["removal_or_two_way_ports"] == 0
    assert not bunker_check(n, m, n)["passed"]
    n = _toy(); n.meta["required_constraint_hooks"] = ["research_bunker_net_zero"]; m = _model(n); install_bunker_net_zero(n)
    r = {r["name"]: r for r in scan_hooks(n, m, n)}[BUNKER_ROW]
    assert r["form"] == "per_variable_zero" and r["verdict"] == "explicit_per_variable_zero" and r["rows"] == 3 * 2
    b = bunker_check(n, m, n)
    assert b["passed"] and b["covers_every_metering_flow"] and b["rows"] == b["expected_rows"] == 6 and b["premises_full_network"]["passed"]


def test_zero_slack_check_final_level_with_a_removal_port_or_positive_cap_passes():
    from zero_slack_check import scan_hooks
    n = _toy(removal="bus0"); m = _model(n)
    m.add_constraints(m["Store-e"].sel(snapshot=n.snapshots[-1], Store=BUNKER_CO2_BUS) <= 0.0, name="research_test_limit")
    assert {r["name"]: r for r in scan_hooks(n, m, n)}["research_test_limit"]["verdict"] == "removal_ports_present"
    n = _toy(); m = _model(n)
    m.add_constraints(m["Store-e"].sel(snapshot=n.snapshots[-1], Store=BUNKER_CO2_BUS) <= 7.0, name="research_test_limit")
    assert {r["name"]: r for r in scan_hooks(n, m, n)}["research_test_limit"]["verdict"] == "positive_cap"


def test_zero_slack_check_annual_sum_with_zero_cap_is_refused():
    from zero_slack_check import scan_hooks
    n = _toy(); m = _model(n); w = xr.DataArray(n.snapshot_weightings.generators, coords={"snapshot": n.snapshots}, dims="snapshot")
    m.add_constraints((m["Generator-p"].sel(Generator="AA fossil") * w).sum() <= 0.0, name="ResearchImportAnnual-AA fossil")
    m.add_constraints((m["Generator-p"].sel(Generator="BB fossil") * w).sum() <= 1e6, name="ResearchImportAnnual-BB fossil")
    rows = {r["name"]: r for r in scan_hooks(n, m, n)}
    assert rows["ResearchImportAnnual-AA fossil"]["form"] == "annual_weighted_sum" and rows["ResearchImportAnnual-AA fossil"]["verdict"] == "zero_slack_forcing_row"
    assert rows["ResearchImportAnnual-BB fossil"]["verdict"] == "positive_cap"


# ----------------------------------------------------------------------------------------------------------- downstream shape adaptations
def _labels(n_snap=3, links=("AA aviation international oil meter", "BB aviation international oil meter"), start=100):
    return xr.DataArray(np.arange(start, start + n_snap * len(links)).reshape(n_snap, len(links)), coords={"snapshot": range(n_snap), "Link": list(links)}, dims=("snapshot", "Link"))


def test_owen_audit_keeps_the_bunker_owner_for_every_row():
    from m12_allocation import BUNKER
    from m12_rhs_audit import Owners
    O = Owners.__new__(Owners); O.codes = {"-": 0}; O.comp = {}
    O.maps = {"Link": pd.Series({"AA aviation international oil meter": "ID", "BB aviation international oil meter": "TH"})}
    lab = _labels()
    got = O.array(BUNKER_ROW, lab)
    assert got.shape == (3, 2) and (got == O.codes[BUNKER]).all()   # the former single row was BUNKER (by_name); every new row stays BUNKER
    other = O.array("research_other_rows", lab)   # any other constraint on the same links keeps the component owners
    inv = O.inv()
    assert [inv[int(x)] for x in other[0]] == ["ID", "TH"]


def test_c1_and_violation_attribution_keep_the_name_rule():
    from l23_violation_analysis import country_of
    from s4o_c1_precision import country_lookup
    lab = _labels(); lab2 = _labels(start=200)
    store = {BUNKER_ROW: SimpleNamespace(labels=lab), "research_other_rows": SimpleNamespace(labels=lab2)}
    maps = {"Link": pd.Series({"AA aviation international oil meter": "ASEAN|ID", "BB aviation international oil meter": "ASEAN|TH"})}
    codes = {}; exported = np.concatenate([np.asarray(lab.values).ravel(), np.asarray(lab2.values).ravel()])
    got = country_lookup(store, exported, maps, codes); inv = {v: k for k, v in codes.items()}
    assert {inv[int(x)] for x in got[:6]} == {"-"}   # as the former single row (no country suffix)
    assert [inv[int(x)] for x in got[6:8]] == ["ASEAN|ID", "ASEAN|TH"]
    assert country_of(None, {"snapshot": "0", "Link": "AA aviation international oil meter"}, BUNKER_ROW) == "-"


def test_price_tables_blank_the_bunker_account_with_a_note():
    from s4d_ledger import nodal_prices
    from v5.v5_gates import nodal_prices as v5_nodal_prices
    n = _toy(); n.buses["country"] = "ASEAN"
    mp = pd.DataFrame(1.5, index=n.snapshots, columns=n.buses.index); mp[BUNKER_CO2_BUS] = 420.0
    n.buses_t.marginal_price = mp
    t = nodal_prices(n)
    assert t.loc[BUNKER_CO2_BUS, ["mean", "min", "max"]].isna().all() and t.loc[BUNKER_CO2_BUS, "note"] == BUNKER_PRICE_NOTE
    assert t.loc["AA oil", "mean"] == pytest.approx(1.5) and t.loc["AA oil", "note"] == "" and len(t) == len(n.buses)
    s, full = v5_nodal_prices(n)
    s = s.set_index("bus")
    assert s.loc[BUNKER_CO2_BUS, ["time_weighted_mean", "minimum", "maximum"]].isna().all() and s.loc[BUNKER_CO2_BUS, "note"] == BUNKER_PRICE_NOTE
    assert s.loc["AA oil", "time_weighted_mean"] == pytest.approx(1.5) and float(full[BUNKER_CO2_BUS].iloc[0]) == 420.0   # the raw duals are not touched
    n2 = _toy(); n2.remove("Store", BUNKER_CO2_BUS); n2.remove("Bus", BUNKER_CO2_BUS)
    n2.mremove("Link", [f"{a} aviation international oil meter" for a in AIRPORTS]); n2.buses["country"] = "ID"
    n2.buses_t.marginal_price = pd.DataFrame(2.0, index=n2.snapshots, columns=n2.buses.index)
    assert "note" not in nodal_prices(n2).columns   # tables without the account keep their columns
