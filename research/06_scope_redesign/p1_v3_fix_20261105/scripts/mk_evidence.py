"""V3.1: light evidence JSON (V3_FIX_EVIDENCE.json) assembled from the session evidence files. Read-only except the output.
    python mk_evidence.py <work dir> <package dir> <out json>"""
import hashlib
import json
import sys
import time
from pathlib import Path

W, P, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
E = W / "evidence"


def jl(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).exists() else None


zsc = jl(E / "ZERO_SLACK_CHECK_F1_F4.json") or {}
calls = (E / "GUROBI_CALLS.csv").read_text(encoding="utf-8").splitlines() if (E / "GUROBI_CALLS.csv").exists() else []
reg = jl(E / "REGRESSION_56.json") or {}
man = jl(P / "HPC_PACKAGE_MANIFEST.json") or {}
res = dict(
    instruction=dict(file="V3_FIX_INSTRUCTION.md", sha256=sha(W / "V3_FIX_INSTRUCTION.md"), registered=(W / "V3_FIX_SHA256.txt").read_text().split()[0] if (W / "V3_FIX_SHA256.txt").exists() else None),
    premises={x["label"]: x["bunker"].get("premises_full_network") for x in zsc.get("networks", [])},
    zero_slack_check=dict(passed=zsc.get("passed"), per_network={x["label"]: dict(network_sha256=x["network_sha256"], passed=x["passed"], verdicts=x["verdicts"], forcing=x["zero_slack_forcing_rows"],
                                                                                   bunker_rows=x["bunker"].get("rows"), bunker_expected_rows=x["bunker"].get("expected_rows"),
                                                                                   caps_without_row=sorted(x["configured_caps_without_row"])) for x in zsc.get("networks", [])}),
    gurobi_calls=[dict(zip(calls[0].split(","), l.split(",", 11))) for l in calls[1:]] if calls else [],
    window_recheck=[l for l in (E / "FIX_STATUS.txt").read_text(encoding="utf-8").splitlines() if l.startswith("VERDICT:")] if (E / "FIX_STATUS.txt").exists() else [],
    regression_56=dict(passed=reg.get("passed"), stop=reg.get("stop"), objective_relative_difference={k: v.get("objective_relative_difference") for k, v in (reg.get("runs") or {}).items()},
                       b6=reg.get("b6"), owen_max_abs_difference_eur=max((abs(v["difference"]) for v in (reg.get("owen_benefit") or {}).values()), default=None),
                       owen_signs_same=all(v["sign_same"] for v in (reg.get("owen_benefit") or {}).values()) if reg.get("owen_benefit") else None),
    package=dict(dir=str(P), commit=man.get("commit"), sha256sums_sha256=man.get("sha256sums_sha256"), files=len(man.get("files", [])), bytes=man.get("upload_total_bytes_excluding_this_manifest"),
                 consistency=man.get("consistency"), zero_slack_check=(man.get("zero_slack_check") or {}).get("passed"), run_dirs=(man.get("run") or {}).get("run_dirs")),
    tests=sorted(str(p.name) for p in (E / "tests").glob("*.txt")) if (E / "tests").exists() else [],
    leak_scans=sorted(str(p.name) for p in (E / "leak").glob("LEAK_SCAN_*.json")) if (E / "leak").exists() else [],
    written_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
print("written", OUT)
