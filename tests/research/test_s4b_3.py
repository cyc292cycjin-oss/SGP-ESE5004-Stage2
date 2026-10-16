"""S4B-3 (decisions 74, 75): Ember observed CF, calibration factors, DEA 2050 turbine, calibrated_modern profiles with 3 resource classes."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
RV = ROOT / "research_inputs/renewable_v5"
NET = ROOT / "results_project/s4b/build_s4b3/integrated/integrated_2920_3h_unsolved.nc"


def test_observed_and_alpha():
    s = pd.read_csv(RV / "WIND_OBSERVED_CF_SUMMARY.csv").set_index("country"); a = pd.read_csv(RV / "WIND_CALIBRATION_ALPHA.csv").set_index("country")
    assert set(s.index[s.calibrate]) == {"PH", "TH", "VN"}                     # ID below 200 MW
    assert s.at["VN", "years_main"] == "2023;2024"                              # 2021 growth > 50 %, 2020-2022 curtailment period dropped
    assert a.alpha_main.between(0.8, 1.6).all()
    cal = a[a.calibrated_individually]
    w = s.loc[cal.index, "max_capacity_gw"]
    assert a.loc[~a.calibrated_individually, "alpha_main"].sub((cal.alpha_main * w).sum() / w.sum()).abs().max() < 1e-12
    o = pd.read_csv(RV / "WIND_OBSERVED_CF_EMBER_2019_2025.csv")
    r = o[(o.country == "TH") & (o.year == 2022)].iloc[0]
    assert r.cf == pytest.approx(r.generation_twh * 1e3 / (8760 * (r.capacity_gw + r.capacity_prev_gw) / 2))


def test_dea_turbine():
    from s4b_3_wind_calibration import dea2050_turbine
    t = dea2050_turbine()
    assert t["P"] == 6.0 and t["hub_height"] == 110.0 and t["rotor_m"] == 165.0 and t["specific_power_w_m2"] == pytest.approx(280.6, abs=0.1)
    assert t["V"][-2:] == [25.0, 25.0] and t["POW"][-1] == 0.0 and max(t["POW"]) == pytest.approx(6.0)
    assert np.all(np.diff(t["V"][:-1]) >= 0)


def test_profiles_and_check_table():
    import xarray as xr
    for N in (1, 3):
        ds = xr.open_dataset(RV / f"profiles_calibrated_modern_c{N}_3h.nc")
        pe = xr.open_dataset(RV / f"profiles_pypsa_eur_c{N}_3h.nc")
        for v in ["offwind_ac", "offwind_dc", "solar"]:
            assert np.allclose(ds[v].fillna(-1).values, pe[v].fillna(-1).values)   # offshore / solar unchanged
        assert float(ds["onwind"].mean()) > float(pe["onwind"].mean())
    c = pd.read_csv(RV / "ONWIND_CF_CHECK_S4B3.csv")
    assert not c.exceeds.any()


def test_config():
    from phase4_static import config
    R = config(ROOT, "integrated")["research"]["renewable"]
    assert R["profile_variant"] == "calibrated_modern" and R["resource_classes"] == 3 and R["clip_p_max_pu"] == 0.01


@pytest.mark.skipif(not NET.exists(), reason="S4B-3 build not present")
def test_built_network():
    import pypsa
    n = pypsa.Network(str(NET)); led = n.meta["research_renewable"]
    assert led["profile_variant"] == "calibrated_modern" and led["resource_classes"] == 3 and led["summary"]["added"] == 647
    g = n.generators[n.generators.carrier == "onwind"]
    assert g.p_nom_max.sum() == pytest.approx(8916.8e3, rel=1e-4)
    pm = n.generators_t.p_max_pu[g.index]; assert float(pm[pm > 0].min().min()) >= 0.01 - 1e-9
