"""S3-4 (decision 10): shipping demand on the regional methanol bus in the built S3-4 networks (results_project/s3_4)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
S34 = ROOT / "results_project" / "s3_4"
SHIP = ROOT / "research_inputs" / "shipping_v5"
REG = ROOT / "research_inputs" / "registry_v5"


def test_shipping_table():
    t = pd.read_csv(SHIP / "SHIPPING_DEMAND_2050.csv")
    tot = t.groupby("account").oil_equivalent_mwh.sum()
    assert tot["DomesticShippingFuel"] == pytest.approx(63.570e6, rel=1e-3) and tot["InternationalShippingBunker"] == pytest.approx(558.423e6, rel=1e-3)   # S3B R1 ratio method (level: 92.764e6)
    assert (t.methanol_mwh == pytest.approx(t.oil_equivalent_mwh * 0.40 / 0.46, rel=1e-9)).all() if False else all(abs(m - o * 0.40 / 0.46) < 1e-6 * max(o, 1) for m, o in zip(t.methanol_mwh, t.oil_equivalent_mwh))
    assert (t.hydrogen_mwh == 0).all() and (t.oil_mwh == 0).all()
    r = pd.read_csv(REG / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert float(r.loc["shipping_methanol_conversion", "value"]) == pytest.approx(0.40 / 0.46) and float(r.loc["shipping_share_methanol_2050_applied", "value"]) == 1.0


def built(sc):
    return (S34 / sc / f"{sc}_2920_3h_unsolved.nc").exists() and (S34 / sc / f"{sc}_BUILD_RECEIPT.json").exists()


@pytest.mark.skipif(not (built("integrated") and built("disconnected")), reason="S3-4 networks not built")
def test_s3_4_networks():
    import pypsa
    lvl = pd.read_csv(ROOT / "research_inputs" / "demand_v5" / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_LEVEL_SENSITIVITY.csv", keep_default_na=False)   # S3-4 networks predate S3B R1
    oil_eq = float(pd.to_numeric(lvl[lvl.account.isin(["DomesticShippingFuel", "InternationalShippingBunker"])].value_2050_mwh, errors="coerce").fillna(0).sum())
    for sc in ["integrated", "disconnected"]:
        n = pypsa.Network(str(S34 / sc / f"{sc}_2920_3h_unsolved.nc"))
        w = n.snapshot_weightings.generators; L = n.links
        loads = n.loads[n.loads.carrier == "shipping methanol"]
        assert len(loads) > 0
        ts = [i for i in loads.index if i in n.loads_t.p_set.columns]; st = [i for i in loads.index if i not in n.loads_t.p_set.columns]
        total = float(n.loads_t.p_set[ts].mul(w, axis=0).sum().sum()) + float((n.loads.loc[st, "p_set"] * w.sum()).sum())
        assert total == pytest.approx(oil_eq * 0.40 / 0.46, rel=1e-6)   # level method: 651.19 TWh oil-eq x 0.40/0.46 = 566.3 TWh methanol
        links = L[L.carrier == "shipping methanol"]
        assert (links.bus0 == "ASEAN methanol").all() and all(abs(float(v) - 0.2482) < 1e-6 for v in links.efficiency2) and (links.bus2.str.startswith("co2 atmosphere")).all()
        # no shipping demand left in the deferred ledger
        deferred = n.meta["s2_demand_ledger"].get("deferred", []) if "deferred" in n.meta.get("s2_demand_ledger", {}) else []
        assert not [d for d in deferred if "Shipping" in d["account"]]
        # per-country ownership: the SG bunker load sits at SG2 0 and books in the SG atmosphere
        sg = links[links.index.str.startswith("SG2 0")]
        assert len(sg) == 1 and sg.bus2.iloc[0] == "co2 atmosphere SG"
