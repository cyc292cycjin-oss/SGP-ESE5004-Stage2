"""V4 W08 checklist section 1 (decision 210 item 1): SDMX 2019 base year. No solver; nothing is written (in-memory rebuild)."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
I1 = ROOT / "research/06_scope_redesign/p1_v4_w07_20261106/I1/BASE2019_SDMX/BASE2019_SDMX_D1_ROWS.csv"
KEY = ["country", "sector", "carrier", "account"]


@pytest.fixture(scope="module")
def base():
    import v4_base_sdmx as B
    return B, B.compute()


def test_capsule_records_and_response_hashes(base):
    B, x = base
    assert len(x["recs"]) == 2752
    reg = pd.read_csv(B.SDMX_DIR / "SDMX_RESPONSES_REGISTRY_W12.csv").set_index("path")
    assert len(x["T"]) == 11 and x["T"].ok.all()
    for r in x["T"].itertuples():
        assert r.sha256 == reg.loc[f"sdmx/{r.file}", "sha256"]
    # the committed capsule is the one the code writes (same records, same file hashes)
    committed = json.loads(B.CAPSULE.read_text())
    assert committed == json.loads(json.dumps(B.capsule_obj(x), default=float))


def test_old_capsule_gates_g1_g3(base):
    B, _ = base
    g = B.gates()
    assert g["G1"] and g["G1_accounts"] == 273
    assert g["G2"] and g["G2_rows"] == 375 and g["G2_unmatched"] == 0
    assert g["G3"] and g["G3_max_abs_mwh"] <= 1e-6


def test_new_base_equals_i1_s5_except_id_coke(base):
    B, x = base
    new = x["DR"].groupby(KEY).base_2019_mwh.sum()
    i1 = pd.read_csv(I1).set_index(KEY).S5
    m = pd.concat([new.rename("new"), i1.rename("i1")], axis=1).fillna(0.0)
    d = m.new - m.i1
    coke = ("ID", "NonEnergyUse", "coal", "NonEnergy:Coke-oven coke")
    assert abs(d.loc[coke] - 791.0 * 1000.0 * (28.20 - 20.1947) / 3.6) < 1e-3   # +1,758,943 MWh, outside T_v2
    rest = d.drop(index=[coke]); ref = m.i1.drop(index=[coke]).abs()
    assert bool((rest.abs() <= 1e-9 * ref + 1e-6).all())   # the I1 table is written with 9 significant digits (i1_common.write_csv)
    # the committed base file = the in-memory rebuild
    f = pd.read_csv(B.BASE_CSV, float_precision="round_trip").groupby(KEY).base_2019_mwh.sum()
    assert float((f - new.reindex(f.index)).abs().max()) == 0.0 and len(f) == len(new)


def test_household_gasoline_and_exceptions(base):
    B, x = base
    g = pd.read_csv(B.GASOLINE_CSV).set_index("country").base_2019_mwh
    assert g["ID"] == pytest.approx(197.0317686944e6, rel=1e-12) and g["ID"] == x["gas"]["ID"]
    e = B.ncv_exceptions()
    assert e == {("ID", "Hard coal"): "20.29", ("ID", "Coke-oven coke"): "28.20"}


def test_factor_modes():
    import reconstruct_base_accounts as rba
    import v4_base_sdmx as B
    src = ROOT / "research_inputs/assembly_v1/sources"
    conv = json.loads((src / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())
    row = {"Commodity": "Hard coal", "Unit": "Metric tons,  thousand", "Quantity": "1", "Country": "ID", "CONVERSION_FACTOR": "26.1"}
    v_repo = rba.Reconstruction(dict(records=[]), conv).convert(row)[0]
    assert B.Recon(dict(records=[]), conv, "frozen").convert(row)[0] == v_repo                       # frozen factor kept
    assert float(B.Recon(dict(records=[]), conv, "sdmx").convert(row)[0]) == pytest.approx(26.1 * 1000 / 3.6)
    assert float(B.Recon(dict(records=[]), conv, "d207", {("ID", "Hard coal"): "20.29"}).convert(row)[0]) == pytest.approx(20.29 * 1000 / 3.6)
