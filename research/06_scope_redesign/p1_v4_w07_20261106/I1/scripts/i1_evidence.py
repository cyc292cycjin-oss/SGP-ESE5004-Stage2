"""I1: merge the per-item evidence files evidence/I1_*.json into EVIDENCE.json (one list; every entry with source, status and data grade) and
add the file-level SHA256 of every deliverable, table, script and BASE2019_SDMX file. Nothing is solved; the repository is not written.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_evidence.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

TOP = ("REPORT.md", "RAS_MECHANISM.md", "BASE2019_DIFF.csv", "EXPORT_TRUNCATION_SCAN.csv", "CORRECTION_CLASSIFICATION.csv", "HVC_VECTOR_CHECK.csv",
       "ID_GASOLINE_CHECK.csv", "MISSING_DATA.csv", "PROGRESS.md", "LEDGER_ENTRY_DRAFT.md")


def main():
    entries, items = [], []
    for f in sorted(cm.EVID.glob("I1_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "entries" not in d:
            continue
        items.append(dict(item=d["item"], file=f"evidence/{f.name}", n=d["n"]))
        entries.extend(d["entries"])
    files = []
    for name in TOP:
        p = cm.I1 / name
        if p.exists():
            files.append(dict(path=name, bytes=p.stat().st_size, sha256=cm.sha256(p)))
    for sub in ("BASE2019_SDMX", "tables", "scripts"):
        for p in sorted((cm.I1 / sub).glob("*")):
            if p.is_file() and p.suffix != ".pyc":
                files.append(dict(path=f"{sub}/{p.name}", bytes=p.stat().st_size, sha256=cm.sha256(p)))
    out = dict(session="I1", instruction="work/p1_v4_w07_20261106/V4_I1_INSTRUCTION.md v1",
               instruction_sha256="be5687e203fb7710c5985fffd31a8933b46ea39a6d71d13d1280d1f1539963d0",
               branch="codex/v4-i1-20261106", base_commit="07e08f387bcb5894384c008debc97d9e9c30ae4b", solver_calls=0,
               note=("Read-only analysis. SDMX raw responses: W12 retrieval (work/p1_v4_w07_20261106/W12/sdmx, 11 files, SHA256 verified, not re-downloaded). "
                     "Scratch copies outside the repository: /home/jin/v4i1 (chain reproduces the repository m08b + s3_0 outputs byte for byte when unmodified)."),
               status_counts=dict(Counter(e["status"] for e in entries)), grade_counts=dict(Counter(e["grade"] for e in entries)),
               items=items, n_entries=len(entries), entries=entries, files=files)
    cm.write_json(out, cm.I1 / "EVIDENCE.json")
    print(len(entries), "entries;", out["status_counts"], out["grade_counts"], len(files), "files")


if __name__ == "__main__":
    main()
