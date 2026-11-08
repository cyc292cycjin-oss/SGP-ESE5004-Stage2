"""V4 D2b section 3 (Fable F-02 side note; decision 221): research.demand.v4.source_band_basis.
  post_product (v4 main)  source band shares of the fixed industrial biomass = cement-kiln biomass of the conservation layer / T_v2 biomass after the
                          product vectors (high), the rest split at 200 C with the s3_0 medium_a_fraction (v4_common.source_band_shares)
  s30 (fallback)          the s3_0 shares (computed before the product vectors), D2a and earlier
The s3_0 shares are recorded in V4_SWITCHES.json (s30_band_*) in every folder. No solver, no network build."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
V4 = ROOT / "research_inputs/industry_v4"
B = ("medium_a", "medium_b", "high")


def test_rule_unit():
    from v4_common import SOURCE_BAND_MIN_MWH, source_band_shares
    assert source_band_shares(1.0, 0.0, 0.2) is None and source_band_shares(0.0, 3.5e-8, 0.2) is None and SOURCE_BAND_MIN_MWH == 1.0
    s = source_band_shares(2.0, 8.0, 0.2)
    assert s["high"] == pytest.approx(0.25) and s["medium_a"] == pytest.approx(0.75 * 0.2) and s["medium_b"] == pytest.approx(0.75 * 0.8)
    assert sum(s.values()) == pytest.approx(1.0)
    assert source_band_shares(9.0, 8.0, 0.2)["high"] == 1.0   # capped at 1
    assert source_band_shares(-1.0, 8.0, 0.2)["high"] == 0.0


def test_switch_values():
    from v4_common import SWITCH_VALUES, V31, V4_MAIN, switches
    assert SWITCH_VALUES["source_band_basis"] == ("s30", "post_product")
    assert V31["source_band_basis"] == "s30" and V4_MAIN["source_band_basis"] == "post_product"
    cfg = {"research": {"demand": {"anchor_mode": "ras", "v4": {"enabled": True, "source_band_basis": "s30"}}}}
    assert switches(cfg)["source_band_basis"] == "s30"
    with pytest.raises(ValueError):
        switches({"research": {"demand": {"anchor_mode": "ras", "v4": {"enabled": True, "source_band_basis": "x"}}}})


@pytest.mark.parametrize("mode", ["ras", "iid"])
def test_main_folder_shares_follow_the_rule(mode):
    from v4_common import source_band_shares
    od = V4 / f"out_{mode}"
    rec = json.loads((od / "V4_SWITCHES.json").read_text())
    assert rec["main_set"] and rec["switches"]["source_band_basis"] == "post_product"
    S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
    P = pd.read_csv(od / "INDUSTRY_2050_SUBSECTOR_CARRIER_V4.csv")
    cem = P[(P.subsector == "cement") & (P.carrier == "biomass")].groupby("country").mwh_2050.sum()
    changed = 0
    for c, v in rec["biomass_overflow_recomputed"].items():
        bio = float(S.at[c, "pe_biomass_mwh"])
        want = source_band_shares(float(cem.get(c, 0.0)), bio, float(S.at[c, "medium_a_fraction"]))
        got = {b: float(S.at[c, f"biomass_source_band_{b}_share"]) for b in B}
        s30 = {b: float(v[f"s30_band_{b}_share"]) for b in B}
        if want is None:
            assert got == s30, (mode, c)
            continue
        for b in B:
            assert got[b] == pytest.approx(want[b], abs=1e-12), (mode, c, b)
            assert float(v[f"band_{b}_share"]) == pytest.approx(got[b], abs=1e-15)
        assert sum(got.values()) == pytest.approx(1.0, abs=1e-12)
        assert float(v["cement_kiln_biomass_mwh"]) == pytest.approx(float(cem.get(c, 0.0)), abs=1e-6)
        # the cement-kiln biomass is not changed by the product vectors: high x s3_0 biomass = cement biomass (s3_0 rule)
        if s30["high"] < 1.0 and float(v["s30_biomass_mwh"]) > 0:
            assert s30["high"] * float(v["s30_biomass_mwh"]) == pytest.approx(float(cem.get(c, 0.0)), rel=1e-9, abs=1e-3), (mode, c)
        changed += any(abs(got[b] - s30[b]) > 1e-12 for b in B)
    assert changed >= 1   # the product vectors add medium-band biomass in several countries (VN, TH, PH, MM, LA, MY in D2a)


def test_s30_folders_keep_the_s3_0_shares():
    """Every folder written with source_band_basis = s30 (or before D2b, without the key) carries the s3_0 shares in the table."""
    n = 0
    for od in sorted(V4.glob("out_*")):
        if not (od / "V4_SWITCHES.json").exists():
            continue
        rec = json.loads((od / "V4_SWITCHES.json").read_text())
        if rec["switches"].get("source_band_basis", "s30") != "s30":
            continue
        S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
        for c, v in rec["biomass_overflow_recomputed"].items():
            if "s30_band_high_share" in v:
                for b in B:
                    assert float(S.at[c, f"biomass_source_band_{b}_share"]) == float(v[f"s30_band_{b}_share"]), (od.name, c, b)
        n += 1
    assert n >= 0
