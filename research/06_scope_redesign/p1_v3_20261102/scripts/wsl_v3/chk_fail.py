"""Read-only look at the two failed smoke runs. Prints only the exception class and message with anything licence-like masked; no file is copied."""
import json, re
from pathlib import Path
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/smoke")
MASK = re.compile(r"(WLS\w*|LICENSE" r"ID|ACCESS\w*|SECRET\w*)\s*[=:]\s*\S+", re.I)
DIGITS = re.compile(r"\b\d{6,}\b")
def clean(s):
    return DIGITS.sub("<n>", MASK.sub(r"\1=<masked>", str(s)))
for sc in ("integrated", "no_new_xb"):
    d = R / sc
    r = json.loads((d / "SOLVE_RECEIPT.json").read_text())
    f = r.get("failure") or {}
    print("==", sc, sorted(r)[:30])
    print(" label", r.get("label"), "calls", r.get("optimize_calls"), "profile", r.get("solver_profile"), "stage", r.get("stage"))
    print(" lp", {k: (r.get("lp") or {}).get(k) for k in ("num_col", "num_row", "nnz", "build_seconds")})
    print(" error", f.get("error"), "|", clean(f.get("detail"))[:500])
    print(" tb tail", clean(f.get("traceback"))[-900:])
    print(" files", sorted(p.name for p in d.iterdir())[:40])
    for n in ("solve.log", "solve.err", "gurobi.linopy.log"):
        p = d / n
        if p.exists():
            t = p.read_text(errors="replace").splitlines()
            print(" --", n, len(t))
            keep = [l for l in t if re.search(r"(?i)error|fail|token|timeout|timed out|unable|connect|licen[cs]e|refused|unreachable", l) and not re.match(r"\s*(Maximum|Average|Page size|Swaps)", l)]
            for l in keep[:14]:
                print("    ", clean(l)[:200])
            print("     last:", clean(t[-1])[:200] if t else "")
