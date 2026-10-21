"""M08a A6 / M08-7 (decisions 129, 131): renewable layout - A6.1 ground PV density 4.6 -> 5.1 MW/km2 (no build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import pypsa
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s4a_layers import apply_renewable_profiles, apply_solar_density   # noqa: E402


def toy():
    n = pypsa.Network(); n.set_snapshots(range(2))
    for i, c in enumerate(["ID", "VN", "SG"]):
        b = f"{c}1"; n.add("Bus", b, carrier="AC"); n.buses.loc[b, "country"] = c
        n.add("Generator", f"{b} solar", bus=b, carrier="solar", p_nom_extendable=True, p_nom_max=1000.0 * (i + 1))
        n.add("Generator", f"{b} solar rooftop", bus=b, carrier="solar rooftop", p_nom_extendable=True, p_nom_max=500.0)
        n.add("Generator", f"{b} onwind", bus=b, carrier="onwind", p_nom_extendable=True, p_nom_max=700.0)
        n.add("Generator", f"{b} solar existing", bus=b, carrier="solar existing", p_nom=50.0)
    return n


@pytest.fixture(scope="module")
def cfg():
    from phase4_static import config
    return config(ROOT, "integrated")


def test_density_config(cfg):
    sd = cfg["research"]["renewable"]["solar_density"]
    assert (sd["built_mw_per_km2"], sd["target_mw_per_km2"]) == (4.6, 5.1)


def test_ground_pv_scaled_only(cfg):
    n = toy(); before = n.generators.p_nom_max.copy()
    led = apply_solar_density(n, cfg["research"]["renewable"])
    k = 5.1 / 4.6
    assert led["scale"] == pytest.approx(1.108696, abs=1e-6) and led["generators"] == 3
    g = n.generators
    sol = g.carrier == "solar"
    assert np.allclose(g.p_nom_max[sol], before[sol] * k, rtol=1e-12)                        # same factor in every country
    assert g.p_nom_max[~sol].equals(before[~sol])                                             # rooftop, onwind, existing unchanged
    assert led["p_nom_max_after_mw"] == pytest.approx(led["p_nom_max_before_mw"] * k, rel=1e-12)


def test_applied_by_the_profile_layer_even_for_original(cfg):
    c = copy.deepcopy(cfg); c["research"]["renewable"]["profile_variant"] = "original"
    with pytest.raises(ValueError, match="offshore_rules"):                                     # A6.2: the new offshore rule needs a rebuilt variant
        apply_renewable_profiles(toy(), c, ROOT)
    c["research"]["renewable"]["offshore_rules"] = "author_pypsa_earth"
    n = toy(); led = apply_renewable_profiles(n, c, ROOT)
    assert led["solar_density"]["scale"] == pytest.approx(5.1 / 4.6) and n.generators.at["ID1 solar", "p_nom_max"] == pytest.approx(1000 * 5.1 / 4.6)
    c["research"]["renewable"]["solar_density"] = {"built_mw_per_km2": 4.6, "target_mw_per_km2": 4.6}   # former state = factor 1
    n = toy(); apply_renewable_profiles(n, c, ROOT)
    assert n.generators.at["ID1 solar", "p_nom_max"] == 1000.0


# --------------------------------------------------------------------------------------------- A6.2 offshore area rules
OFF = ROOT / "research_inputs/renewable_v5/offshore_m08a"


@pytest.fixture(scope="module")
def classes():
    import pandas as pd
    return pd.read_csv(OFF / "OFFSHORE_CLASSES_pypsa_eur_v2025_07.csv")


def test_offshore_rule_config(cfg):
    RN = cfg["research"]["renewable"]
    assert RN["offshore_rules"] == "pypsa_eur_v2025_07" and RN["offshore_dir"] == "research_inputs/renewable_v5/offshore_m08a"
    from m08a_offshore_profiles import RULES
    r = RULES["pypsa_eur_v2025_07"]   # PyPSA-Eur v2025.07.0 config lines 201-260
    assert {t: (v["capacity_per_sqkm"], v.get("max_depth"), v.get("min_depth"), v.get("max_shore_distance"), v.get("min_shore_distance"), v["landfall_km"]) for t, v in r.items()} == {
        "offwind-ac": (2.0, 60.0, None, 30000.0, None, 20.0), "offwind-dc": (2.0, 60.0, None, None, 30000.0, 30.0), "offwind-float": (2.0, 1000.0, 60.0, None, None, 40.0)}
    assert all(v["ship_threshold"] == 400.0 and v["excluder_resolution"] == 200 and v["natura"] and v["landcover_codes"] == [80, 200] for v in r.values())


def test_offshore_classes_table(classes):
    import pandas as pd
    import xarray as xr
    t = classes[classes.rules == "pypsa_eur_v2025_07"]
    assert set(t.tech) == {"offwind-ac", "offwind-dc", "offwind-float"} and set(t.classes) == {1, 3} and not t.average_distance_km.isna().any()
    assert t.groupby("tech").landfall_km.unique().map(lambda v: list(v)).to_dict() == {"offwind-ac": [20.0], "offwind-dc": [30.0], "offwind-float": [40.0]}
    p1 = t[t.classes == 1].groupby(["tech", "node"]).potential_mw.sum(); p3 = t[t.classes == 3].groupby(["tech", "node"]).potential_mw.sum()
    assert np.allclose(p1.sort_index(), p3.reindex(p1.index).values, rtol=1e-9)                     # the 3 classes partition the node potential
    tot = t[t.classes == 3].groupby("tech").potential_mw.sum() / 1e3
    assert tot["offwind-ac"] == pytest.approx(1783.2, abs=0.1) and tot["offwind-dc"] == pytest.approx(2714.3, abs=0.1) and tot["offwind-float"] == pytest.approx(4435.8, abs=0.1)
    for k in (1, 3):
        ds = xr.open_dataset(OFF / f"profiles_offshore_pypsa_eur_v2025_07_c{k}_3h.nc")
        assert ds.sizes["time"] == 2920
        for tech in ("offwind-ac", "offwind-dc", "offwind-float"):
            keys = set(t[(t.classes == k) & (t.tech == tech) & (t.potential_mw > 0)].generator_key)
            v = ds[tech.replace("-", "_")].to_pandas().dropna(axis=1, how="all")
            assert keys <= set(v.columns) and float(v.min().min()) >= 0.0 and float(v.max().max()) <= 1.0


def toy_offshore(classes):
    import xarray as xr
    ds = xr.open_dataset(OFF / "profiles_offshore_pypsa_eur_v2025_07_c3_3h.nc")
    n = pypsa.Network(); n.set_snapshots(ds.time.values)
    for node, c in classes[["node", "country"]].drop_duplicates().itertuples(index=False):
        n.add("Bus", node, carrier="AC"); n.buses.loc[node, "country"] = c
    b = classes.node.iloc[0]
    for car, cc in (("offwind-ac", 230000.0), ("offwind-dc", 250000.0)):
        n.add("Generator", f"{b} {car}-2025", bus=b, carrier=car, p_nom_extendable=True, p_nom_max=1000.0, capital_cost=cc, marginal_cost=0.015, lifetime=30.0)
        n.add("Generator", f"{b} {car}-2025 c1", bus=b, carrier=car, p_nom_extendable=True, p_nom_max=500.0, capital_cost=cc, marginal_cost=0.015, lifetime=30.0)
    n.add("Generator", "existing VN2 offwind", bus=b, carrier="offwind existing", p_nom=171.0)
    n.generators["country"] = n.generators.bus.map(n.buses.country)
    n.add("Carrier", "offwind-dc", color="#74c6f2", nice_name="Offshore Wind (DC)")
    return n


def test_apply_offshore_rules(cfg, classes):
    from s4a_layers import apply_offshore_rules
    n = toy_offshore(classes); led = apply_offshore_rules(n, cfg, ROOT)
    t = classes[(classes.classes == 3) & (classes.potential_mw > 0)]
    g = n.generators
    assert led["removed"] == {"offwind-ac": dict(generators=2, p_nom_max_mw=1500.0), "offwind-dc": dict(generators=2, p_nom_max_mw=1500.0)}
    for tech in ("offwind-ac", "offwind-dc", "offwind-float"):
        sel = g[g.carrier == tech]
        assert len(sel) == (t.tech == tech).sum() and sel.p_nom_max.sum() == pytest.approx(t[t.tech == tech].potential_mw.sum(), rel=1e-12)
        assert sel.p_nom_extendable.all() and (sel.p_nom == 0).all() and (sel.marginal_cost == 0.015).all()
    r = t[t.tech == "offwind-float"].iloc[0]
    name = f"{r.node} offwind-float-2025" + (f" c{int(r.cls)}" if int(r.cls) else "")
    assert g.at[name, "bus"] == r.node and g.at[name, "p_nom_max"] == pytest.approx(r.potential_mw)
    pm = n.generators_t.p_max_pu
    assert ((pm > 0) & (pm < 0.01)).sum().sum() == 0                                                 # clip_p_max_pu 0.01
    assert g.at["existing VN2 offwind", "p_nom"] == 171.0 and "offwind-float" in n.carriers.index      # existing untouched; carrier added
    c = copy.deepcopy(cfg); c["research"]["renewable"]["offshore_rules"] = "author_pypsa_earth"
    n2 = toy_offshore(classes); assert apply_offshore_rules(n2, c, ROOT) == dict(rule="author_pypsa_earth") and len(n2.generators) == 5
    c["research"]["renewable"]["offshore_rules"] = "x"
    with pytest.raises(ValueError):
        apply_offshore_rules(toy_offshore(classes), c, ROOT)


def test_cost_layer_prices_offshore_classes(cfg, classes):
    """Cost layer: technology-data v0.15.0 offwind(-float) + station + 1.25 x (distance x submarine + landfall x underground) per node x class."""
    from s2_costs import build_research_costs
    from s4a_layers import apply_offshore_rules
    from s4c_layers import apply_cost_layer_s4c1
    costs, _ = build_research_costs(ROOT, cfg, ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv")
    n = toy_offshore(classes); apply_offshore_rules(n, cfg, ROOT)
    led = apply_cost_layer_s4c1(n, costs, cfg, ROOT)
    assert led["offwind_distance_table"]["rule"] == "pypsa_eur_v2025_07" and led["offwind_missing_distance"] == []
    d = classes[classes.classes == 3].set_index(["tech", "node", "cls"])
    fx = lambda r: float(costs.at[r, "fixed"])
    for tech, turbine, land in (("offwind-ac", "offwind", 20.0), ("offwind-dc", "offwind", 30.0), ("offwind-float", "offwind-float", 40.0)):
        r = classes[(classes.classes == 3) & (classes.tech == tech) & (classes.potential_mw > 0)].iloc[0]
        name = f"{r.node} {tech}-2025" + (f" c{int(r.cls)}" if int(r.cls) else "")
        z = d.loc[(tech, r.node, int(r.cls))]
        exp = fx(turbine) + fx(f"{tech}-station") + 1.25 * (float(z.average_distance_km) * fx(f"{tech}-connection-submarine") + land * fx(f"{tech}-connection-underground"))
        assert n.generators.at[name, "capital_cost"] == pytest.approx(exp, rel=1e-12) and float(z.landfall_km) == land
