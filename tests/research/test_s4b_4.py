"""S4B-4 (decision 76): IBTrACS typhoon exposure tables and the typhoon_premium switch (implemented only)."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
RV = ROOT / "research_inputs/renewable_v5"
B = ROOT / "results_project/s4b/build_s4b4"


def test_exposure_tables():
    import xarray as xr
    f = xr.open_dataset(RV / "TYPHOON_FREQ_0P3_IBTRACS_1980_2024.nc")["cat_ge50ms_passages_per_decade"]
    assert f.shape == (146, 175) and float(f.min()) >= 0 and 5 < float(f.max()) < 15
    # count per decade = integer storms x 10 / 45
    assert ((f.values * 4.5).round(6) % 1 == 0).all()
    n = pd.read_csv(RV / "TYPHOON_EXPOSURE_BY_NODE.csv")
    for th in ["0.5", "1", "2"]:
        assert (n[f"flag_ge_{th}"] == (n[f"potential_share_ge_{th}"] >= 0.5)).all()
    assert (n.flag_ge_2 <= n.flag_ge_1).all() and (n.flag_ge_1 <= n["flag_ge_0.5"]).all()
    flagged = set(map(tuple, n[n.flag_ge_1][["tech", "node"]].values))
    assert ("onwind", "PH_Luzon5 0") in flagged and all(node.startswith(("PH", "VN")) for _, node in flagged)
    ev = json.loads((RV / "TYPHOON_EXPOSURE_S4B4.json").read_text()); assert ev["threshold_kt"] == pytest.approx(97.19, abs=0.01)


def test_config_default_off():
    from phase4_static import config
    R = config(ROOT, "integrated")["research"]["renewable"]
    assert R["typhoon_premium"] == "off" and R["typhoon_premium_pct"] == 25.0 and R["typhoon_threshold_per_decade"] == 1.0


@pytest.mark.skipif(not (B / "typhoon_on/integrated_2920_3h_unsolved.nc").exists(), reason="S4B-4 builds not present")
def test_switch_on_build():
    import pypsa
    a = pypsa.Network(str(B / "integrated/integrated_2920_3h_unsolved.nc")); b = pypsa.Network(str(B / "typhoon_on/integrated_2920_3h_unsolved.nc"))
    assert a.meta["research_typhoon_premium"]["mode"] == "off" and b.meta["research_typhoon_premium"]["mode"] == "on"
    r = b.generators.capital_cost / a.generators.capital_cost.reindex(b.generators.index)
    ch = r[(r - 1).abs() > 1e-12]
    assert len(ch) == b.meta["research_typhoon_premium"]["generators"] > 0 and ((ch - 1.25).abs() < 1e-12).all()
    assert set(b.generators.loc[ch.index, "carrier"]) <= {"onwind", "offwind-ac", "offwind-dc"}
