"""M08a A5 / M08-4 (decision 131): CO2 storage unified to ERIA-GCCSI 2024 P50, annual cap = potential / 50 (no build, no solve)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
from s2_layers import co2_storage_caps   # noqa: E402

REG = ROOT / "research_inputs" / "registry_v5" / "DATA_REGISTRY.csv"
TABLE = ROOT / "research_inputs" / "co2_v5" / "CO2_STORAGE_POTENTIAL_UNIFIED.csv"


@pytest.fixture(scope="module")
def setup():
    from phase4_static import config
    cfg = config(ROOT, "integrated")
    reg = pd.read_csv(REG, dtype=str, keep_default_na=False).set_index("param_id")
    return cfg["research"]["s2"]["co2"], reg


def test_table_values():
    t = pd.read_csv(TABLE, keep_default_na=False).set_index("country")
    exp = {"VN": 5.30, "PH": 0.067, "MY": 128.8, "ID": 51.3, "BN": 18.6, "TH": 16.0}
    for c, v in exp.items():
        assert float(t.at[c, "potential_gt"]) == pytest.approx(v, abs=0.05 if v > 1 else 0.001), c
    assert float(t.at["KH", "potential_gt"]) == 0.09 and float(t.at["KH", "high_gt"]) == 45.0
    for c in ("TL", "LA", "MM", "SG"):
        assert float(t.at[c, "potential_gt"]) == 0.0
    assert t.at["LA", "status"] == "UNASSESSED" and t.at["MM", "status"] == "UNASSESSED" and t.at["SG", "status"] == "SOURCE_ZERO"


def test_annual_caps_vn_ph(setup):
    R, reg = setup
    assert R["storage_potential_source"] == "eria_gccsi_2024_unified" and R["storage_potential_case"] == "p50" and R["storage_years"] == 50
    caps, pots, info = co2_storage_caps(R, reg)
    assert caps["VN"] / 1e6 == pytest.approx(106.068, abs=1e-3)    # instruction: VN 106 Mt/a
    assert caps["PH"] / 1e6 == pytest.approx(1.344, abs=1e-6)      # instruction: PH 1.34 Mt/a
    assert caps["KH"] / 1e6 == pytest.approx(1.8) and caps["MY"] == pytest.approx(pots["MY"] * 1e9 / 50)
    assert all(caps[c] == 0 for c in ("TL", "LA", "MM", "SG"))
    assert info["status"]["LA"] == "UNASSESSED" and len(info["table_sha256"]) == 64
    R2 = dict(R, storage_years=25)   # the cap follows the configured horizon (no hard-coded /50)
    assert co2_storage_caps(R2, reg)[0]["VN"] == pytest.approx(2 * caps["VN"])


def test_cases_and_former_source(setup):
    R, reg = setup
    lo = co2_storage_caps(dict(R, storage_potential_case="low"), reg)[1]
    hi = co2_storage_caps(dict(R, storage_potential_case="high"), reg)[1]
    assert lo["VN"] == pytest.approx(3.3034) and hi["VN"] == pytest.approx(9.3034) and hi["KH"] == 45.0
    old_caps, old_pots, old = co2_storage_caps(dict(R, storage_potential_source="registry_d1"), reg)
    assert old_caps["VN"] == 236e6 and old_pots["PH"] == 22.3 and old["source"] == "registry_d1"
    with pytest.raises(ValueError):
        co2_storage_caps(dict(R, storage_potential_case="p90"), reg)


def test_ship_routes_to_receivers_without_store_dropped(tmp_path, monkeypatch):
    """A5 follow-up: CO2_SHIP_ROUTES_S4D2.csv still lists 70 routes into TL (store gone with potential 0); the shipping layer drops the routes
    into receivers without a national store (recorded) and still refuses a missing pair or an extra route into an existing store."""
    import pypsa
    from phase4_static import config
    import s4d_layers
    from s4d_layers import apply_intra_asean_shipping
    monkeypatch.setattr(s4d_layers, "ROOT", tmp_path)   # the toy route / coastal tables live in tmp_path (ledger paths are relative to ROOT)
    routes_real = pd.read_csv(ROOT / "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv")
    assert (routes_real.receiver == "TL").sum() == 70
    reg = pd.read_csv(REG, keep_default_na=False).set_index("param_id")
    cfg = copy.deepcopy(config(ROOT, "disconnected"))
    pd.DataFrame(dict(node=["A1", "B1", "C1"], coastal=[True, True, True])).to_csv(tmp_path / "coast.csv", index=False)
    def run(rows):
        pd.DataFrame(rows, columns=["origin", "receiver", "landing", "gc_km", "sea_km"]).to_csv(tmp_path / "routes.csv", index=False)
        cfg["research"]["co2"].update(coastal_nodes_table="coast.csv", ship_routes_table="routes.csv")
        n = pypsa.Network()
        for node, c in (("A1", "ID"), ("B1", "TL"), ("C1", "VN")):
            n.add("Bus", node); n.buses.loc[node, "country"] = c
            n.add("Bus", f"{node} co2 stored", carrier="co2 stored"); n.buses.loc[f"{node} co2 stored", "country"] = c
            n.add("Store", f"{node} co2 stored", bus=f"{node} co2 stored", e_nom_extendable=True); n.stores.loc[f"{node} co2 stored", "research_role"] = "CO2_BUFFER"
        for c in ("ID", "VN"):   # TL has no national store (unified table: potential 0)
            n.add("Bus", f"co2 sequestered {c}", carrier="co2 sequestered"); n.buses.loc[f"co2 sequestered {c}", "country"] = c
            n.add("Store", f"co2 sequestered {c}", bus=f"co2 sequestered {c}", carrier="co2 sequestered", e_nom_extendable=True, e_nom_max=1e6)
            n.stores.loc[f"co2 sequestered {c}", "country"] = c
        return n, apply_intra_asean_shipping(n, cfg, reg)
    ok = [("A1", "VN", "C1", 500, 600), ("A1", "TL", "B1", 400, 450), ("B1", "ID", "A1", 400, 450), ("B1", "VN", "C1", 300, 350),
          ("C1", "ID", "A1", 500, 600), ("C1", "TL", "B1", 300, 350)]
    n, led = run(ok)
    assert led["links"] == 4 and led["dropped_routes_no_national_store"] == {"TL": 2} and led["receivers"] == ["ID", "VN"]
    assert set(n.links.index) == {"A1 co2 ship to VN", "B1 co2 ship to ID", "B1 co2 ship to VN", "C1 co2 ship to ID"}
    with pytest.raises(ValueError, match=r"missing \[\('B1', 'VN'\)\]"):
        run([r for r in ok if r[:2] != ("B1", "VN")])
    with pytest.raises(ValueError, match=r"extra \[\('D9', 'VN'\)\]"):
        run(ok + [("D9", "VN", "C1", 100, 120)])


def test_registry_rows(setup):
    _, r = setup
    assert r.loc["co2_storage_unified_table", "value"] == "research_inputs/co2_v5/CO2_STORAGE_POTENTIAL_UNIFIED.csv"
    for c in ("LA", "MM"):
        assert r.loc[f"co2_storage_potential_unassessed_{c}", "value"] == "0" and r.loc[f"co2_storage_potential_unassessed_{c}", "status"] == "REGISTERED"
        assert "UNASSESSED" in r.loc[f"co2_storage_potential_{c}", "description"]
    assert "历史：已被 co2_injection_cap_unified_VN 替代" in r.loc["co2_injection_cap_VN", "description"]
    assert r.loc["co2_storage_potential_KH", "tier"] == "C" and r.loc["co2_storage_potential_VN", "tier"] == "B"
