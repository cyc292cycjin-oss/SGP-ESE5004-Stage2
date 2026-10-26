"""DFX phase 4: add the shutdown record to DFX_EVIDENCE.json (phase4.shutdown).
    python p4_shutdown_record.py"""
import json
from pathlib import Path

e = Path("/home/jin/wt_dfx_v3_20261026/research/06_scope_redesign/p1_dfx_20261026/DFX_EVIDENCE.json")
ev = json.loads(e.read_text())
ev["phase4"]["shutdown"] = dict(issued_sgt="2026-10-27 06:48:24", after_commit="0a09f252",
                                precheck="no solve / runner / post-processing process, licence absent, /root/.gurobi 0 entries",
                                verify_sgt="2026-10-27 06:50:07", verify="ssh login refused (connection refused): instance stopped",
                                scripts=["scripts/wsl_dfx4/r_shutdown.sh", "scripts/wsl_dfx4/verify_shutdown.sh"])
e.write_text(json.dumps(ev, indent=1, ensure_ascii=False) + "\n")
print("shutdown recorded")
