"""V4 W08 checklist section 10 / acceptance A3: registry fragment v4_w08 (file SHA256 = registry), registry assembly, configuration switches
(default off = v3.1; B12 hashes the new keys), v4 table set identity. No solver, no build."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts_project"))


def test_fragment_file_hashes_and_assembly():
    from v4_common import sha256
    frag = pd.read_csv(ROOT / "research_inputs/registry_v5/fragments/v4_w08.csv", dtype=str, keep_default_na=False)
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    assert len(frag) >= 60 and set(frag.param_id) <= set(reg.index)
    files = frag[frag.source_locator.str.startswith("file: ")]
    assert len(files) >= 45
    for r in files.itertuples():
        p = ROOT / r.source_locator[len("file: "):].split(" ")[0]
        assert sha256(p) == r.source_sha256, r.param_id
    sdmx = frag[frag.param_id.str.startswith("v4_sdmx_2019_response_")]
    assert len(sdmx) == 11 and all("Prepared" in d and "retrieved" in d for d in sdmx.description)
    lic = " ".join(frag.description)
    assert "CC BY 4.0" in lic and "eXtremOS" in lic and "10.7799/1570008" in lic and "DOE/NREL/ALLIANCE" in lic


def test_switches_default_off_and_config_hash():
    from phase4_static import config
    from v4_common import switches, v4_tables, V31
    cfg = config(ROOT, "integrated")
    s = switches(cfg)
    assert s["enabled"] is False and s["anchor_mode"] == "ras" and {k: s[k] for k in V31} == V31
    assert v4_tables(cfg) is None
    d = cfg["research"]["demand"]
    assert d["v4"]["enabled"] is False and d["anchor_mode"] == "ras"
    from v5.v5_gates import config_sha
    a = config_sha(cfg["research"])
    cfg["research"]["demand"]["v4"]["enabled"] = True
    assert config_sha(cfg["research"]) != a   # B12: a v4 network carries a different configuration hash


def test_v4_table_sets_match_their_switches():
    from phase4_static import config
    from v4_common import switch_sha, v4_tables
    for mode in ("ras", "iid"):
        cfg = config(ROOT, "integrated")
        cfg["research"]["demand"]["v4"]["enabled"] = True; cfg["research"]["demand"]["anchor_mode"] = mode
        t = v4_tables(cfg)
        assert t is not None and t["record"]["switch_sha256"] == switch_sha(t["switches"])
        rec = json.loads((t["dir"] / "V4_SWITCHES.json").read_text())
        from v4_common import sha256
        for f, h in rec["files"].items():
            assert sha256(t["dir"] / f) == h, (mode, f)
