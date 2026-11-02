"""Records the first smoke round in the deliverable folder: facts only, no log lines (solve.log / solve.err hold licence lines and stay in results_project)."""
import json, re, shutil
from pathlib import Path
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke")
E = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/evidence")
old = E / "smoke"; new = E / "smoke_attempt1"
if old.exists():
    shutil.move(str(old), str(new))
out = dict(summary="both runs stopped at gurobipy.Env(): no WLS token, no solver session, no solve; the LP was built", status_lines=[l for l in (R / "STATUS.txt").read_text().splitlines()])
for sc in ("integrated", "no_new_xb"):
    r = json.loads((R / sc / "SOLVE_RECEIPT.json").read_text()); f = r.get("failure") or {}
    d = re.sub(r"after \d+ ms", "after <n> ms", str(f.get("detail")))
    out[sc] = dict(error=f.get("error"), detail=d, input_network_sha256=(r.get("input_network") or {}).get("sha256"), truncated_to=(r.get("input_network") or {}).get("truncated_to"), profile=r.get("solver_profile"), lp=r.get("lp"),
                   optimize_calls=r.get("optimize_calls"), peak_rss_gib=(r.get("peak_rss_bytes") or 0) / 2**30, termination_condition=r.get("termination_condition"))
(new / "SMOKE_ATTEMPT1_FAILURE.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps({k: {x: (v[x] if x != "lp" else {y: v["lp"].get(y) for y in ("num_col", "num_row", "nnz", "build_seconds")}) for x in ("error", "detail", "truncated_to", "profile", "lp", "optimize_calls")} for k, v in out.items() if k in ("integrated", "no_new_xb")}, indent=0)[:1200])
txt = (new / "SMOKE_ATTEMPT1_FAILURE.json").read_text() + (new / "V3_SMOKE_RESULT.json").read_text()
print("licence-like", bool(re.search("WLS" + "ACCESS|WLS" + "SECRET|LICENSE" + "ID", txt, re.I)))
