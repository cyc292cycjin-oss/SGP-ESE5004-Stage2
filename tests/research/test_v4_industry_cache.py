"""V4 W08 checklist section 2: industry sub-sector cache from the SDMX records (decision 210 items 1 / 4; decision 211 item 2). No solver."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
W08 = ROOT / "research/06_scope_redesign/p1_v4_w08_20261106"
I2T = ROOT / "research/06_scope_redesign/p1_v4_w07_20261106/I2/tables"
KEY = ["country", "sector", "carrier", "account"]


@pytest.fixture(scope="module")
def mods():
    import v4_industry_cache as C
    from v4_common import V4_MAIN
    return C, C.load_cells(), dict(V4_MAIN, anchor_mode="ras"), json.loads((W08 / "tables/W08_REF_INPUTS.json").read_text())


def test_cells_file_equals_rebuild_and_reference(mods):
    C, cells, _, ref = mods
    mem = C.compute_cells()
    assert len(cells) == len(mem) == len(ref["cells"]) == 393
    assert (cells.mwh.values == mem.mwh.values).all() and (cells.mwh.values == pd.DataFrame(ref["cells"]).mwh.values).all()


def test_cache_equals_reference_for_three_switch_sets(mods):
    C, cells, s, ref = mods
    assert C.cache_for(cells, s)["records"] == ref["cache_a_paper"]["records"]                                   # v4 main (decision 211 item 2)
    assert C.cache_for(cells, dict(s, id_paper_fuelwood="purchased"))["records"] == ref["cache_a"]["records"]  # I2 main
    assert C.cache_for(cells, dict(s, residue_boundary=False))["records"] == ref["cache_full"]["records"]      # S1 (no residue boundary)
    assert json.loads(C.CACHE_JSON.read_text())["records"] == ref["cache_a_paper"]["records"]


def test_cache_sums_equal_d1_industry_rows_after_residues(mods):
    """Every country x carrier: cache total = SDMX D1 industry row - residues (a) (+-1 MWh); ID biomass: the fuelwood is outside the seed and
    enters at the 2010-2017 mean, non-paper share (decision 210 item 4 b, 211 item 2)."""
    C, cells, s, _ = mods
    base = pd.read_csv(C.V4_DIR / "D1_BASE2019_SDMX.csv", float_precision="round_trip")
    ind = base[base.account.isin(["IndustryFinalEnergy", "UNSD_electricity_Industry"])].groupby(["country", "carrier"]).base_2019_mwh.sum()
    res = C.residues(cells); ra = res[res.cls == "a"].groupby(["country", "carrier"]).mwh.sum()
    fw = C.fuelwood_mean(cells)
    # the D1 seed carries the blend cut (biofuel overlap removed from the petroleum row, v4_base_sdmx.blend); the cache holds the raw records
    # (shares only in s3_0), so the cut is added back on the industry oil rows
    blog = json.loads((C.V4_DIR / "BASE2019_SDMX_EVIDENCE.json").read_text())["blend_log"]
    cut = {}
    for b in blog:
        if b["account"] == "IndustryFinalEnergy":
            cut[b["country"]] = cut.get(b["country"], 0.0) + float(b["petroleum_mwh_cut"])
    cache = C.cache_for(cells, s)
    bad = []
    for r in cache["records"]:
        tot = sum(float(v) for k, v in r.items() if k not in ("country", "carrier"))
        want = float(ind.get((r["country"], r["carrier"]), 0.0)) - float(ra.get((r["country"], r["carrier"]), 0.0))
        if r["carrier"] == "oil":
            want += cut.get(r["country"], 0.0)
        if (r["country"], r["carrier"]) == ("ID", "biomass"):
            want += -fw["sdmx_mwh"] + fw["mean_mwh"] * fw["share_non_paper"]
        if abs(tot - want) > 1.0:
            bad.append((r["country"], r["carrier"], tot, want))
    assert not bad, bad


def test_id_biomass_composition_and_residue_records(mods):
    C, cells, s, _ = mods
    drop = C.drop_set(cells, s)
    idb = cells[(cells.country == "ID") & (cells.carrier == "biomass") & (cells.tx != "121")]
    kept = {r.commodity for r in idb.itertuples() if (r.country, r.code, r.tx) not in drop}
    assert kept == {"Fuelwood", "Charcoal", "Biodiesel"}   # fuelwood of the n.e.s. row; charcoal 0.80 and biodiesel 3.70 TWh are in HEESI (seed)
    assert ("ID", "5110", "1214G") in drop
    mine = C.residues(cells)[["country", "tx", "code", "cls"]].sort_values(["country", "tx", "code"]).reset_index(drop=True)
    i2 = pd.read_csv(I2T / "I2_RESIDUE_A_RECORDS.csv", dtype={"tx": str, "code": str})[["country", "tx", "code", "cls"]].sort_values(["country", "tx", "code"]).reset_index(drop=True)
    assert mine.equals(i2)
    assert len(mine[mine.cls == "a"]) == 15
