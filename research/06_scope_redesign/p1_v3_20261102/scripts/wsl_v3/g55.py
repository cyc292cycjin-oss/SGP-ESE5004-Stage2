"""Union of the failed gates over the earlier runs of the same kind (review section 1): 56 snapshots and 365x24h. Read-only."""
import json
from pathlib import Path
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
W = Path("/mnt/d/ResearchWorkspaces/ASEAN/work")
def failed(f):
    g = json.loads(Path(f).read_text()); return sorted(k for k, v in g.items() if isinstance(v, dict) and v.get("passed") is False)
for tag, root, pat in (("56 v2 T16", R / "dfx_v3/smoke_v2", "*/V5_GATES.json"), ("56 v3 A", R / "v3/smoke_r2", "*/V5_GATES.json"), ("56 v3 T16", R / "v3/smoke_s1", "*/V5_GATES.json"), ("365 DFX", W / "p1_dfx_20261026/cloud_results", "**/V5_GATES.json"), ("365 M10", W / "p1_m10p_20261022", "**/V5_GATES.json")):
    fs = sorted(root.glob(pat)); print(tag, len(fs))
    for f in fs[:8]:
        print("  ", str(f.relative_to(root))[:70], failed(f))
