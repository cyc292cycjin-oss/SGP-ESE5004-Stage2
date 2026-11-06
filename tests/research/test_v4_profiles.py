"""V4 W08 checklist section 9: G5 MAIN composite curves of the industrial loads. No solver; the I2 comparison runs the chain in a temporary folder."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
I2T = ROOT / "research/06_scope_redesign/p1_v4_w07_20261106/I2/tables"
G5 = ROOT / "research/06_scope_redesign/p1_v4_w07_20261106/G5"


@pytest.fixture(scope="module")
def weights():
    return pd.read_csv(ROOT / "research_inputs/industry_v4/out_ras/INDUSTRY_CURVE_WEIGHTS_V4.csv")


def test_composites_mean_one_and_energy_preserved(weights):
    import v4_profiles as PR
    S = PR.Shapes(weights, "MAIN")
    for (c, z, et), _ in weights.groupby(["country", "zone", "etype"]):
        y = S.composite(c, z, et)
        if y is None:
            continue
        assert abs(y.mean() - 1.0) <= 1e-9
        y3 = y.reshape(2920, 3).mean(1)
        annual = 123456.789
        assert abs((annual / 8760.0 * y3).sum() * 3.0 - annual) <= 1e-6
    assert S.composite("ID", "UTC+7", "elec").max() > 1.0   # not flat ('other' mix shape)


def test_node_time_zones():
    tz = pd.read_csv(ROOT / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv").set_index("node").utc_offset_h
    g5 = pd.read_csv(G5 / "TIMEZONE_NODES.csv")
    col = [c for c in g5.columns if "offset" in c or c.startswith("utc")][0]
    g5 = g5.set_index("node")[col]
    idn = [n for n in tz.index if n.startswith("ID")]
    assert all(float(tz[n]) == float(g5[n]) for n in idn if n in g5.index)
    assert float(tz["ID_Java-Bali1 2"]) == 7.0   # East Java: legal UTC+7 (longitude would say +8; G5 note)


def test_weights_reproduce_i2(tmp_path):
    """I2 original case (IId, paper fuelwood purchased): the repository composition = I2 tables/I2_CURVE_WEIGHTS.csv (I2 rounded its dispersed rows
    to 1e-6 TWh, hence the tolerance)."""
    import v4_industry as V
    import v4_outputs as O
    import v4_profiles as PR
    from v4_common import V4_MAIN
    I = V.Inputs(); ch = V.Chain(tmp_path)
    res = ch.run(V.final_case(I, dict(V4_MAIN, anchor_mode="iid", id_paper_fuelwood="purchased")))
    parts = {c: v["L"]["parts"] for c, v in res["snap"].items() if v["L"]["T"] > 0}
    W = PR.composition(parts, PR.dispersed_rows(res["pz"]), O.Nodes())
    ref = pd.read_csv(I2T / "I2_CURVE_WEIGHTS.csv")
    m = W.merge(ref, on=["country", "zone", "key", "etype"], how="outer", suffixes=("", "_i2")).fillna(0.0)
    m = m[(m.mwh > 5e-4) | (m.mwh_i2 > 5e-4)]
    assert float((m.mwh - m.mwh_i2).abs().max()) <= 1.0   # MWh
