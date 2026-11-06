"""V4 W08 acceptance A2: with every v4 switch off (the scripts called without options) m08b_demand.py and s3_0_industry.py reproduce the eight
v3.1 outputs byte for byte. The scripts run in a copy of research_inputs + scripts_project (temporary folder); the repository is not written.
Also: the v4 chain with every switch off (empty case) gives the v3.1 T_v2 of v3_industry (S0). No solver."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))
DV = "research_inputs/demand_v5"
M08B_OUT = ["DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", "DEMAND_ANCHOR_AEO8_ATS.csv", "INDUSTRY_OUTPUT_2050_M08B.csv", "INDUSTRY_OUTPUT_BASE_M08B.csv"]
S30_OUT = ["INDUSTRY_2050_SUMMARY_aeo8_ats_anchor.csv", "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv", "INDUSTRY_2050_OTHER_BUCKET.csv",
           "INDUSTRY_2050_PYPSA_EUR_aeo8_ats_anchor.csv"]


@pytest.fixture(scope="module")
def copy_root(tmp_path_factory):
    t = tmp_path_factory.mktemp("a2")
    shutil.copytree(ROOT / "research_inputs", t / "research_inputs")
    shutil.copytree(ROOT / "scripts_project", t / "scripts_project", ignore=shutil.ignore_patterns("__pycache__", "retired"))
    (t / "scripts_project/retired").mkdir(exist_ok=True)
    return t


def run(root: Path, script: str):
    r = subprocess.run([sys.executable, script], cwd=root / "scripts_project", capture_output=True, text=True, env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr[-2000:]


def test_a2_eight_outputs_byte_identical(copy_root):
    run(copy_root, "m08b_demand.py"); run(copy_root, "s3_0_industry.py")
    diff = [f for f in M08B_OUT + S30_OUT if (copy_root / DV / f).read_bytes() != (ROOT / DV / f).read_bytes()]
    assert not diff, diff
    # the default runs leave no v4 file behind
    assert not (copy_root / DV / "DEMAND_ANCHOR_C3_DEVIATION.csv").exists()


def test_v4_chain_all_switches_off_is_v31(tmp_path):
    import pandas as pd
    import v4_industry as V
    snap = V.run_case({}, V.Chain(tmp_path / "chain"))
    v3 = pd.read_csv(ROOT / "research_inputs/industry_v3/INDUSTRY_2050_SUMMARY_V3.csv").set_index("country")
    import v3_industry as v3m
    for c, x in snap["countries"].items():
        t = float(sum(v3[v3m.col(k)].get(c, 0.0) for k in v3m.CARRIERS)) if c in v3.index else 0.0
        assert abs(x["T"] - t) <= 1e-3, (c, x["T"], t)
