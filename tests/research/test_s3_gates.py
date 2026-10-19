"""S3-6: V5 group-B additions (B13-B16, B1/B11/B12 extensions) on the built S3-5 networks (solver-free)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
S35 = ROOT / "results_project" / "s3_5"
S35PC = ROOT / "results_project" / "s3_5_pc"


def built(base, sc):
    return (base / sc / f"{sc}_2920_3h_unsolved.nc").exists()


def test_gate_signatures():
    import inspect
    from v5 import v5_gates as G
    for name in ["gate_b13_imports_one_way", "gate_b14_terminal_caps", "gate_b15_domestic_production_caps", "gate_b16_import_prices_identical"]:
        assert hasattr(G, name)
    assert "overrides" in inspect.getsource(G.gate_b12_hash) and "s3_switches" in inspect.getsource(G.gate_b12_hash)
    assert "oil non-fossil" in inspect.getsource(G.gate_b11_supply_routes) and "ASEAN" in inspect.getsource(G.gate_b11_supply_routes)
    assert "IMPORT_CARRIERS" in inspect.getsource(G.gate_b1_country_net_zero)


@pytest.mark.skipif(not (built(S35, "integrated") and built(S35, "disconnected")), reason="S3-5 networks not built")
def test_static_b_gates():
    import pypsa
    from phase4_static import config
    from v5.v5_gates import gate_b11_supply_routes, gate_b12_hash, gate_b13_imports_one_way, gate_b14_terminal_caps, gate_b15_domestic_production_caps, gate_b16_import_prices_identical
    ni = pypsa.Network(str(S35 / "integrated" / "integrated_2920_3h_unsolved.nc")); nd = pypsa.Network(str(S35 / "disconnected" / "disconnected_2920_3h_unsolved.nc"))
    for n, sc in [(ni, "integrated"), (nd, "disconnected")]:
        cfg = config(ROOT, sc)
        b11 = gate_b11_supply_routes(n, cfg)
        assert b11["passed"], [r for r in b11["rows"] if r["count_short"]]
        rows = {r["carrier"]: r for r in b11["rows"]}
        assert rows["oil"]["count_short"] == 0 and rows["ammonia"]["load_bearing_buses"] == 1 and rows["methanol"]["load_bearing_buses"] == 1
        b12 = gate_b12_hash(n, cfg)   # S3-5 networks predate the S3B research.solver block: only the config-hash check is expected to differ
        assert all(v for k, v in b12["checks"].items() if k != "research_config_sha256_matches") and b12["s3_switches"]["fuel_carbon_mode"] == "origin_neutral" and b12["s3_switches"]["industry_ratio_source"] == "jrc_idees_2021"
        b13 = gate_b13_imports_one_way(n); assert b13["passed"], b13["checks"]
        b14 = gate_b14_terminal_caps(n); assert b14["passed"] and len(b14["terminals"]) == 16
        b15 = gate_b15_domestic_production_caps(n); assert b15["passed"] and b15["generators"] == 84 and b15["by_country"]["MY"]["cap_mwh"] == pytest.approx(849525174.4, rel=1e-6)
    b16 = gate_b16_import_prices_identical(ni, nd); assert b16["passed"] and all(v["identical"] for v in b16["carriers"].values())


@pytest.mark.skipif(not built(S35PC, "integrated"), reason="producer_credit network not built")
def test_b12_with_override():
    import pypsa
    from phase4_static import config
    from v5.v5_gates import gate_b12_hash
    n = pypsa.Network(str(S35PC / "integrated" / "integrated_2920_3h_unsolved.nc"))
    b12 = gate_b12_hash(n, config(ROOT, "integrated"))
    assert all(v for k, v in b12["checks"].items() if k != "research_config_sha256_matches") and b12["s3_switches"]["fuel_carbon_mode"] == "producer_credit" and b12["s3_switches"]["config_overrides"] == ["s3.fuel_carbon_mode=producer_credit"]


S3B_R4 = ROOT / "results_project" / "s3b" / "r4" / "integrated" / "integrated_2920_3h_unsolved.nc"


@pytest.mark.skipif(not S3B_R4.exists(), reason="S3B R4 network not built")
def test_b12_s3b_rebuilt():
    import pypsa
    from phase4_static import config
    from v5.v5_gates import gate_b12_hash
    n = pypsa.Network(str(S3B_R4)); cfg = config(ROOT, "integrated")
    b12 = gate_b12_hash(n, cfg)   # the R4 network predates the S3B R1 research.demand.growth_method key: only the config-hash check is expected to differ
    assert all(v for k, v in b12["checks"].items() if k != "research_config_sha256_matches") and cfg["research"]["solver"]["profile"] == "formal_barrier" and cfg["research"]["solver"]["profiles"]["formal_barrier"]["Crossover"] == 0   # decision 121: default profile A (again)
