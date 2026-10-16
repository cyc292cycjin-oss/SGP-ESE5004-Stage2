"""S3-3 (decision 44): regional ammonia / methanol buses and the PyPSA-Eur default conversions in the built S3-3 networks (results_project/s3_3)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
S33 = ROOT / "results_project" / "s3_3"
DEM = ROOT / "research_inputs" / "demand_v5"


def built(sc):
    return (S33 / sc / f"{sc}_2920_3h_unsolved.nc").exists() and (S33 / sc / f"{sc}_BUILD_RECEIPT.json").exists()


@pytest.mark.skipif(not (built("integrated") and built("disconnected")), reason="S3-3 networks not built")
def test_s3_3_networks():
    import pypsa
    summary = pd.read_csv(DEM / "INDUSTRY_2050_SUMMARY_aeo8_ats_relative_level.csv").set_index("country")   # S3-3 networks predate S3B R1: level method = the pre-R1 main table
    for sc in ["integrated", "disconnected"]:
        n = pypsa.Network(str(S33 / sc / f"{sc}_2920_3h_unsolved.nc"))
        L = n.links; w = n.snapshot_weightings.generators
        for b, car in [("ASEAN ammonia", "ammonia"), ("ASEAN methanol", "methanol")]:
            assert n.buses.at[b, "carrier"] == car and n.buses.at[b, "country"] == "ASEAN"
        n_h2 = 97   # spatial AC nodes with the S2 candidate structure (the 3 DC converter nodes carry no conversion candidates)
        hb = L[L.carrier == "Haber-Bosch"]
        assert len(hb) == n_h2 and (hb.bus1 == "ASEAN ammonia").all() and (hb.bus2.str.endswith(" H2")).all()
        assert hb.efficiency.iloc[0] == pytest.approx(1 / 0.2473, rel=1e-6) and hb.efficiency2.iloc[0] == pytest.approx(-1.1484 / 0.2473, rel=1e-6)   # technology-data Haber-Bosch inputs
        cr = L[L.carrier == "ammonia cracker"]
        assert len(cr) == n_h2 and (cr.bus0 == "ASEAN ammonia").all() and cr.efficiency.iloc[0] == pytest.approx(1 / 1.46, rel=1e-9)
        me = L[L.carrier == "methanolisation"]
        assert len(me) == n_h2 and (me.bus1 == "ASEAN methanol").all() and (me.bus3.str.endswith(" co2 stored")).all() and (me.p_min_pu == 0.3).all()
        assert me.efficiency.iloc[0] == pytest.approx(0.8787) and me.efficiency2.iloc[0] == pytest.approx(-0.8787 / 3.6907) and me.efficiency3.iloc[0] == pytest.approx(-0.8787 / 4.0321)
        btm = L[L.carrier == "biomass-to-methanol"]
        assert len(btm) >= 90 and (btm.bus1 == "ASEAN methanol").all() and (btm.efficiency2 < 0).all()   # fuel carbon credited at production (PyPSA-Eur add_biomass_to_methanol)
        oc = L[L.carrier == "OCGT methanol"]
        assert len(oc) == n_h2 and (oc.bus0 == "ASEAN methanol").all() and (oc.efficiency2 > 0).all()
        assert set(n.stores.index) >= {"ASEAN ammonia store", "ASEAN methanol store"}
        # industrial demands on the regional buses (regional_buses mode): ammonia loads sum to the S3-0 table; methanol via node use links with an atmosphere port
        amm = n.loads[n.loads.carrier == "industry ammonia"]
        assert len(amm) > 0 and (amm.bus == "ASEAN ammonia").all()
        total = float((n.loads_t.p_set[amm.index].mul(w, axis=0)).sum().sum()) if any(i in n.loads_t.p_set.columns for i in amm.index) else float((amm.p_set * w.sum()).sum())
        assert total == pytest.approx(float(summary.pe_ammonia_mwh.sum()), rel=1e-6)
        use = L[L.carrier == "industry methanol"]
        assert len(use) > 0 and (use.bus0 == "ASEAN methanol").all() and all(abs(float(v) - 0.2482) < 1e-6 for v in use.efficiency2)   # technology-data methanol CO2 intensity
        # the S3-0 interim conversion (ammonia -> H2 + electricity) is off: industry meta says regional_buses
        assert n.meta["research_ammonia_methanol"]["components"]["haber_bosch"] == n_h2
