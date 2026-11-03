"""Diagnosis of the test_s3_gates failures of the full suite: which B12 check is False on the S3-5 networks, and the cross_border switch keys (no solve)."""
import sys
from pathlib import Path
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT / "scripts_project"))
import pypsa
from phase4_static import config
from v5.v5_gates import gate_b12_hash, replay_research_config
S35 = ROOT / "results_project" / "s3_5"
print("s3_5 path", S35, "resolved", S35.resolve())
for sc in ("integrated", "disconnected"):
    f = S35 / sc / f"{sc}_2920_3h_unsolved.nc"
    n = pypsa.Network(str(f)); cfg = config(ROOT, sc)
    b = gate_b12_hash(n, cfg)
    print(sc, {k: v for k, v in b["checks"].items()})
    R, ov = replay_research_config(n, cfg)
    have = n.meta.get("research_cross_border", {}).get("switches")
    want = {k: bool(v) for k, v in R["cross_border"].items()}
    print("  switches only in config:", sorted(set(want) - set(have or {})), " only in network:", sorted(set(have or {}) - set(want)),
          " differing:", sorted(k for k in set(want) & set(have or {}) if want[k] != have[k]))
    print("  cross_border config keys/values:", {k: R["cross_border"][k] for k in sorted(R["cross_border"])})
