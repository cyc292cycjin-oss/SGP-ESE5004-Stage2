"""S4B-2 (decisions 78, 79): geothermal / new hydro / new PHS caps, proxies, inflow tie, nuclear plan caps."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
PV = ROOT / "research_inputs/potentials_v5"
B = ROOT / "results_project/s4b/build_s4b2"


def test_caps_tables():
    c = pd.read_csv(PV / "CANDIDATE_CAPS_S4B2_BY_COUNTRY.csv"); nd = pd.read_csv(PV / "CANDIDATE_CAPS_S4B2_BY_NODE.csv")
    main = c[(c["mode"] == "national_potential") & (c.variant == "announced_preconstruction")].set_index(["country", "tech"]).cap_mw
    assert main[("VN", "hydro_all")] == pytest.approx(40000 - 17962, abs=1) and main[("ID", "geothermal")] == pytest.approx(23590 - 1168.5, abs=1)
    assert main[("MY", "hydro_reservoir_only")] > 0 and main[("MY", "hydro_ror_only")] > 0 and main[("MY", "geothermal")] == 229
    assert main[("TH", "hydro_all")] == 0 and main[("TL", "hydro_all")] == 0 and main[("BN", "hydro_all")] == 0
    assert (c.cap_mw >= 0).all()
    la = c[(c["mode"] == "national_potential_la_mem_18gw") & (c.variant == "announced_preconstruction") & (c.country == "LA") & (c.tech == "hydro_all")].cap_mw.iloc[0]
    assert la == pytest.approx(main[("LA", "hydro_all")] - 8000)
    for (m, v), d in c.groupby(["mode", "variant"]):   # every country cap is allocated to nodes
        assert nd[(nd["mode"] == m) & (nd.variant == v)].p_nom_max_mw.sum() == pytest.approx(d.cap_mw.sum(), rel=1e-9, abs=1e-6)
    lit = c[(c["mode"] == "national_potential") & (c.variant == "announced_preconstruction_construction")].groupby("tech").cap_mw.sum()
    assert lit["PHS"] > main.xs("PHS", level="tech").sum()   # literal variant includes the construction units (already stock)
    nuc = pd.read_csv(PV / "NUCLEAR_NATIONAL_PLAN_CAPS_S4B2.csv").set_index("country").cap_mw
    assert nuc.to_dict() == {**{c_: 0.0 for c_ in nuc.index}, "PH": 4800.0, "VN": 14400.0, "ID": 10000.0, "TH": 600.0}


def test_config():
    from phase4_static import config
    C = config(ROOT, "integrated")["research"]["candidates"]
    assert C["hydro_geothermal_cap"] == "national_potential" and C["pipeline_cap_statuses"] == "announced_preconstruction" and C["nuclear_cap"] == "none"


@pytest.mark.skipif(not (B / "integrated/integrated_2920_3h_unsolved.nc").exists(), reason="S4B-2 build not present")
def test_built_network_candidates():
    import pypsa
    n = pypsa.Network(str(B / "integrated/integrated_2920_3h_unsolved.nc")); su, g = n.storage_units, n.generators
    h = su[(su.carrier == "hydro") & (su.p_nom_max > 0)]; p = su[(su.carrier == "PHS") & (su.p_nom_max > 0)]
    assert (h.p_min_pu == 0).all() and (h.efficiency_store == 0).all() and (h.max_hours > 0).all() and h.index.isin(n.storage_units_t.inflow.columns).all()
    assert set(n.meta["research_new_hydro_inflow_tie"]) == set(h.index)
    assert np.allclose(p.efficiency_store * p.efficiency_dispatch, 0.75) and (p.max_hours == 6).all()
    geo = g[(g.carrier == "geothermal") & (g.p_nom_max > 0)]; assert np.allclose(geo.p_max_pu, 0.719443559520017)
    ror = g[(g.carrier == "ror") & (g.p_nom_max > 0)]; assert ror.index.isin(n.generators_t.p_max_pu.columns).all()
    assert not (g.s1_candidate_status == "DATA_PENDING").any() and not (su.s1_candidate_status == "DATA_PENDING").any()
    tot = su.loc[su.carrier.isin(["hydro", "PHS"]), "p_nom_max"].sum() + g.loc[g.carrier.isin(["ror", "geothermal"]), "p_nom_max"].sum()
    c = pd.read_csv(PV / "CANDIDATE_CAPS_S4B2_BY_COUNTRY.csv"); c = c[(c["mode"] == "national_potential") & (c.variant == "announced_preconstruction")]
    assert tot == pytest.approx(c.cap_mw.sum(), rel=1e-9)
    assert (g.loc[g.carrier.isin(["nuclear", "nuclear SMR"]), "p_nom_max"] == np.inf).all()   # main: no nuclear cap (decision 38)


@pytest.mark.skipif(not (B / "nuclear_plans/integrated_2920_3h_unsolved.nc").exists(), reason="S4B-2 nuclear_plans build not present")
def test_nuclear_plans_build():
    import pypsa
    n = pypsa.Network(str(B / "nuclear_plans/integrated_2920_3h_unsolved.nc")); g = n.generators
    caps = n.meta["research_nuclear_caps"]; assert {c: v["cap_mw"] for c, v in caps.items()} == {"PH": 4800.0, "VN": 14400.0, "ID": 10000.0, "TH": 600.0}
    nuc = g[g.carrier.isin(["nuclear", "nuclear SMR"])]
    assert (nuc[~nuc.bus.map(n.buses.country).isin(list(caps))].p_nom_max == 0).all()
    assert "research_nuclear_national_cap" in n.meta["required_constraint_hooks"]
