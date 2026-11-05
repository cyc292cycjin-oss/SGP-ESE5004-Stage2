"""W12: merge the per-item evidence files evidence/W12_*.json into EVIDENCE.json (one list, every entry with source, status and grade)
and add the file-level SHA256 of every table, script and SDMX response of the delivery folder. Nothing is solved."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w12_common as cm  # noqa: E402


def main():
    entries, items = [], []
    for f in sorted(cm.EVID.glob("W12_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "entries" not in d:
            continue
        items.append(dict(item=d["item"], file=f"evidence/{f.name}", n=d["n"]))
        entries.extend(d["entries"])
    files = []
    for sub in ("tables", "scripts", "sdmx"):
        for p in sorted((cm.W12 / sub).glob("*")):
            if p.is_file() and not p.name.startswith("_probe") and not p.name.startswith("_agg") and p.suffix != ".pyc":
                files.append(dict(path=f"{sub}/{p.name}", bytes=p.stat().st_size, sha256=cm.sha256(p)))
    for name in ("REPORT.md", "MISSING_DATA.csv", "DATA_REGISTRY_W12_SDMX.csv", "LEDGER_ENTRY_DRAFT.md"):
        p = cm.W12 / name
        if p.exists():
            files.append(dict(path=name, bytes=p.stat().st_size, sha256=cm.sha256(p)))
    out = dict(session="W12", instruction="work/p1_v4_w07_20261106/V4_W07_INSTRUCTION.md B-W12", instruction_sha256="20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf",
               branch="codex/v4-w07-w12-20261106", base_commit="07e08f387bcb5894384c008debc97d9e9c30ae4b", solver_calls=0,
               note="Read-only verification; the five issues also exist in the v3.1 networks running on HPC; registered before any v3.1 HPC result was read.",
               status_counts=dict(Counter(e["status"] for e in entries)), grade_counts=dict(Counter(e["grade"] for e in entries)),
               items=items, n_entries=len(entries), entries=entries, files=files)
    cm.write_json(out, cm.W12 / "EVIDENCE.json")
    print(len(entries), "entries;", out["status_counts"], out["grade_counts"], len(files), "files")


if __name__ == "__main__":
    main()
