"""S4A-1 (L14): rebuilt renewable profiles, the research.renewable switch and the resource-class split."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
RV = ROOT / "research_inputs" / "renewable_v5"
EB = ROOT / "results_project" / "assembly_v1" / "final_assets" / "electric_base_2050_unsolved.nc"


def test_profile_files_and_manifest():
    import xarray as xr
    man = json.loads((RV / "MANIFEST.json").read_text())
    for var in ["fork", "pypsa_eur"]:
        for c in [1, 3]:
            f = RV / f"profiles_{var}_c{c}_3h.nc"
            assert f.exists() and f.name in man
            ds = xr.open_dataset(f)
            assert set(ds.data_vars) == {"onwind", "offwind_ac", "offwind_dc", "solar"} and ds.sizes["time"] == 2920
            for v in ds.data_vars:
                a = ds[v].values; assert np.nanmin(a) >= 0 and np.nanmax(a) <= 1.0 + 1e-9
    cls = pd.read_csv(RV / "S4A_PROFILE_CLASSES_c3.csv")
    s = cls.groupby(["tech", "variant", "node"]).potential_share.sum()
    assert (s.round(9) == 1.0).all()   # class potentials partition the node potential


def test_config_default_and_switch_validation():
    from phase4_static import config
    from s4a_layers import apply_renewable_profiles, VARIANTS
    cfg = config(ROOT, "integrated")
    RN = cfg["research"]["renewable"]
    # S4B-3 (decisions 74, 75): main = calibrated_modern with 3 resource classes; the S4A variants stay available
    assert RN["profile_variant"] == "calibrated_modern" and RN["resource_classes"] == 3 and set(VARIANTS) == {"original", "fork", "pypsa_eur", "calibrated_modern"}


@pytest.mark.skipif(not EB.exists(), reason="electric base not available")
def test_apply_profiles_on_electric_base():
    import pypsa
    from phase4_static import config
    from s4a_layers import apply_renewable_profiles
    cfg = config(ROOT, "integrated")
    cfg["research"]["renewable"].update(profile_variant="pypsa_eur", resource_classes=1, offshore_rules="author_pypsa_earth")   # the S4A variant tested explicitly (S4B-3 changed the main setting; M08a A6.2 the offshore rule)
    n0 = pypsa.Network(str(EB)); base_pm = n0.generators_t.p_max_pu.copy(); base_pmax = n0.generators.p_nom_max.copy()
    sd = cfg["research"]["renewable"]["solar_density"]; k_solar = sd["target_mw_per_km2"] / sd["built_mw_per_km2"]   # M08a A6.1: ground PV x 5.1 / 4.6
    base_pmax = base_pmax.where(n0.generators.carrier != "solar", base_pmax * k_solar)
    # original: untouched
    c = copy.deepcopy(cfg); c["research"]["renewable"]["profile_variant"] = "original"
    n = pypsa.Network(str(EB)); led = apply_renewable_profiles(n, c, ROOT)
    assert led["profile_variant"] == "original" and n.generators_t.p_max_pu.equals(base_pm)
    # pypsa_eur, one class: series replaced, p_nom_max unchanged, solar rooftop follows solar
    n = pypsa.Network(str(EB)); led = apply_renewable_profiles(n, cfg, ROOT)
    assert led["summary"]["replaced"] >= 96 * 2 and led["summary"]["added"] == 0
    assert np.allclose(n.generators.p_nom_max.replace(np.inf, 1e30), base_pmax.replace(np.inf, 1e30), rtol=1e-12, atol=0)
    g = n.generators; w = n.snapshot_weightings.generators
    sol = g.index[g.carrier == "solar"][0]; node = str(g.at[sol, "bus"])
    roof = [r for r in g.index[g.carrier == "solar rooftop"] if str(r).startswith(node + " solar rooftop")][0]   # rooftop sits on the node low-voltage bus
    assert np.allclose(n.generators_t.p_max_pu[sol].values, n.generators_t.p_max_pu[roof].values)
    cf_new = (n.generators_t.p_max_pu[sol] * w).sum() / w.sum(); cf_old = (base_pm[sol] * w).sum() / w.sum()
    assert cf_new > cf_old * 1.05   # solar without the 0.854 correction
    rep = [k for k in led["replaced"]]; v = n.generators_t.p_max_pu[rep].values
    assert led["clip_p_max_pu"] == 0.01 and v[v > 0].min() >= 0.01   # clip_p_max_pu as in the original chain / PyPSA-Eur
    # three classes: p_nom_max split conserved
    c3 = copy.deepcopy(cfg); c3["research"]["renewable"]["resource_classes"] = 3
    n = pypsa.Network(str(EB)); led = apply_renewable_profiles(n, c3, ROOT)
    assert led["summary"]["added"] > 0
    for tech in ["onwind", "solar", "offwind-dc"]:
        for name in g.index[g.carrier == tech][:5]:
            parts = [name] + [k for k in n.generators.index if k.startswith(name + " c")]
            assert n.generators.loc[parts, "p_nom_max"].sum() == pytest.approx(float(base_pmax[name]), rel=1e-9)


@pytest.mark.skipif(not EB.exists(), reason="electric base not available")
def test_offshore_rules_on_electric_base():
    """M08a A6.2: main configuration (calibrated_modern, 3 classes, offshore_rules pypsa_eur_v2025_07) on the electric base - every extendable
    offwind-ac / -dc candidate replaced by the class table, offwind-float added, onshore / solar classes as before."""
    import pypsa
    from phase4_static import config
    from s4a_layers import apply_renewable_profiles
    cfg = config(ROOT, "integrated"); RN = cfg["research"]["renewable"]
    t = pd.read_csv(ROOT / RN["offshore_dir"] / "OFFSHORE_CLASSES_pypsa_eur_v2025_07.csv"); t = t[(t.classes == 3) & (t.potential_mw > 0)]
    n0 = pypsa.Network(str(EB)); n = pypsa.Network(str(EB)); led = apply_renewable_profiles(n, cfg, ROOT)
    g = n.generators
    for tech in ("offwind-ac", "offwind-dc", "offwind-float"):
        sel = g[(g.carrier == tech) & g.p_nom_extendable]
        assert len(sel) == (t.tech == tech).sum() and sel.p_nom_max.sum() == pytest.approx(t[t.tech == tech].potential_mw.sum(), rel=1e-12)
        assert set(sel.bus) <= set(n0.buses.index)
    assert led["offshore"]["removed"]["offwind-ac"]["generators"] == int((n0.generators.carrier.eq("offwind-ac") & n0.generators.p_nom_extendable).sum())
    assert g[g.carrier == "offwind existing"].p_nom.sum() == pytest.approx(n0.generators[n0.generators.carrier == "offwind existing"].p_nom.sum())
    for tech in ("onwind", "solar"):   # not touched by the offshore rule
        assert g[(g.carrier == tech) & g.p_nom_extendable].p_nom_max.sum() == pytest.approx(
            n0.generators[(n0.generators.carrier == tech) & n0.generators.p_nom_extendable].p_nom_max.sum() * (5.1 / 4.6 if tech == "solar" else 1.0), rel=1e-9)
