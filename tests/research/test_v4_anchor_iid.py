"""V4 W08 checklist section 3: anchor modes (decision 210 item 3, decision 211 item 1) and the residue anchor alignment (210 item 4 a).
m08b_demand.py runs in temporary folders (--out-dir); nothing in research_inputs is written. No solver."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
SECTORS = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]


def m08b(tmp: Path, name: str, *args) -> pd.DataFrame:
    out = tmp / name
    r = subprocess.run([sys.executable, "scripts_project/m08b_demand.py", "--out-dir", str(out), *[str(a) for a in args]], cwd=ROOT, capture_output=True, text=True,
                       env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr[-2000:]
    return out


def anchors(out: Path) -> dict:
    d = json.loads((out / "dump.json").read_text())
    return d


def seed_file(tmp: Path, name: str, edits: dict | None = None) -> Path:
    import v4_industry as V
    I = V.Inputs()
    d = I.B.copy()
    for k, v in (edits or {}).items():
        d[k] = d.get(k, 0.0) + v
    p = tmp / f"{name}.csv"; p.write_bytes(V.write_d1(V.D1_TABLE.read_bytes(), d, I.S0))
    return p


def test_iid_on_the_v31_seed_reproduces_the_v3_anchors(tmp_path):
    a = m08b(tmp_path, "ras", "--dump-anchors", tmp_path / "ras.json")
    b = m08b(tmp_path, "iid", "--anchor-mode", "iid", "--dump-anchors", tmp_path / "iid_pre.json")
    ta = pd.read_csv(a / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country"); tb = pd.read_csv(b / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    dev = max(abs(float(ta.at[c, f"ras_sector_anchor_{s}_mwh"]) - float(tb.at[c, f"ras_sector_anchor_{s}_mwh"])) for c in ta.index for s in SECTORS)
    assert dev <= 1.0   # MWh = 1e-6 TWh (I1: 2e-8 TWh)
    f = pd.read_csv(ROOT / "research_inputs/demand_v5/DEMAND_ANCHOR_V3_SECTOR_FACTORS.csv").set_index("sector").factor
    assert f["Industry"] == pytest.approx(2.6186, abs=5e-5) and f["Transport"] == pytest.approx(2.8536, abs=5e-5) and f["Residential"] == pytest.approx(0.7260, abs=5e-5)
    assert f["Commercial"] == pytest.approx(2.1101, abs=5e-5) and f["AgricultureOthers"] == pytest.approx(3.2825, abs=5e-5)


@pytest.mark.parametrize("mode", ["iid", "ras"])
def test_residue_anchor_deduction(tmp_path, mode):
    """Residue still in the seed (no deduction) vs residue out of the seed + anchor deduction: every non-industry anchor and every multiplier
    unchanged; the industry anchor and the country total fall by R x m (decision 210 item 4 a, in every anchor mode: decision 211 item 1)."""
    import v4_industry as V
    I = V.Inputs()
    R = {c: v for c, v in I.a_tot.items() if I.balance_contains.get(c, True)}
    keep = seed_file(tmp_path, "keep")
    cut = seed_file(tmp_path, "cut", {V.IND_BIO(c): -v for c, v in R.items()})
    (tmp_path / "adj.json").write_text(json.dumps(R))
    a = m08b(tmp_path, f"keep_{mode}", "--table", keep, "--anchor-mode", mode)
    b = m08b(tmp_path, f"cut_{mode}", "--table", cut, "--anchor-mode", mode, "--residue-anchor-adj", tmp_path / "adj.json")
    ta = pd.read_csv(a / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country"); tb = pd.read_csv(b / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
    for c in ta.index:
        for s in SECTORS[1:]:
            assert float(tb.at[c, f"ras_sector_anchor_{s}_mwh"]) == pytest.approx(float(ta.at[c, f"ras_sector_anchor_{s}_mwh"]), rel=1e-11)
        assert float(tb.at[c, "industry_multiplier"]) == pytest.approx(float(ta.at[c, "industry_multiplier"]), rel=1e-11)
        r = R.get(c, 0.0); m = float(ta.at[c, "industry_multiplier"])
        assert float(tb.at[c, "industry_anchor_mwh"]) == pytest.approx(float(ta.at[c, "industry_anchor_mwh"]) - r * m, rel=1e-11, abs=1e-3)
    dv = pd.read_csv(b / "DEMAND_ANCHOR_C3_DEVIATION.csv").set_index("sector")
    assert set(dv.index) == set(SECTORS)
    tot_r = sum(R[c] * float(ta.at[c, "industry_multiplier"]) for c in R)
    assert float(dv.at["Industry", "deviation_mwh"]) == pytest.approx(-tot_r if mode == "ras" else float(dv.at["Industry", "deviation_mwh"]), rel=1e-9)
    if mode == "ras":   # RAS keeps the C.3 column targets except the deducted residues
        for s in SECTORS[1:]:
            assert abs(float(dv.at[s, "deviation_pct"])) < 1e-6


def test_external_mode_is_an_interface_stub(tmp_path):
    shutil.copyfile(ROOT / "research_inputs/demand_v5/DEMAND_ANCHOR_V3_FROZEN.csv", tmp_path / "ext.csv")   # exact strings (a pandas round trip loses 1 ulp)
    a = m08b(tmp_path, "ext", "--anchor-mode", "external", "--external-anchors", tmp_path / "ext.csv")
    b = m08b(tmp_path, "ras0")
    assert (a / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv").read_bytes() == (b / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv").read_bytes()
