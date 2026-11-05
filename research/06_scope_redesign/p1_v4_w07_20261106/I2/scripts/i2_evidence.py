"""I2: merge the per-item evidence files evidence/I2_*.json into EVIDENCE.json (every entry with source, status and data grade), add the final
numbers by country and step, the rule differences against the session main paths, and the file-level SHA256 of every deliverable. Read only.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_evidence.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402
import i2_items as IT    # noqa: E402

TOP = ("REPORT.md", "W08_IMPLEMENTATION_SPEC.md", "W08_VALIDATION_PLAN.md", "ASEAN_V4_SUMMARY.csv", "BIOMASS_POTENTIAL_ADJ.csv", "SENSITIVITY_TOP10.csv",
       "MISSING_DATA_ALL.csv", "PROGRESS.md", "LEDGER_ENTRY_DRAFT.md") + tuple(f"{c}_V4_FINAL.csv" for c in cm.ASEAN)


def main():
    entries, items = [], []
    for f in sorted(cm.EVID.glob("I2_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if "entries" not in d:
            continue
        items.append(dict(item=d["item"], file=f"evidence/{f.name}", n=d["n"]))
        entries.extend(d["entries"])
    L = pd.read_csv(cm.TABLES / "I2_STEPS_LONG.csv")
    for r in L.itertuples():
        st, gr = (r.status, r.grade)
        entries.append(dict(id=f"I2_steps.{r.country}.{r.step}", value=dict(T_v2=round(r.T_v2_2050_TWh, 6), other=round(r.other_2050_TWh, 6), other_share=round(r.other_share, 6),
                                                                             delta_T=round(r.delta_T_TWh, 6), industry_fe=round(r.implied_industry_fe_2050_TWh, 6)),
                            unit="TWh (2050)", status=("EXACT" if r.step == "S0" else "PROPOSED"), grade=str(gr).split("/")[0], source="tables/I2_STEPS_LONG.csv (scratch chain run)",
                            locator=f"step {r.step}: {r.label}", note=str(st)))
    files = []
    for name in TOP:
        p = cm.I2 / name
        if p.exists():
            files.append(dict(path=name, bytes=p.stat().st_size, sha256=cm.sha256(p)))
    for sub in ("tables", "scripts", "figures"):
        for p in sorted((cm.I2 / sub).glob("*")):
            if p.is_file() and p.suffix != ".pyc":
                files.append(dict(path=f"{sub}/{p.name}", bytes=p.stat().st_size, sha256=cm.sha256(p)))
    out = dict(session="I2", instruction="work/p1_v4_w07_20261106/V4_I2_INSTRUCTION.md v1",
               instruction_sha256="36c3a2bd9b77ee76f08e1bd20759d4efb388889775285d944b3f0ee9dd02fdd5",
               branch="codex/v4-i2-20261106", base_commit="07e08f387bcb5894384c008debc97d9e9c30ae4b",
               merges=dict(ncv="7c23e456", g0="80961534", g1="ed9f967b", g2="ac05af91", g3="bdb04eab", g4="913d86b6", g5="c49531a0", w12="a180b8b0", i1="a2daeaca"),
               solver_calls=0,
               note=("Merge and quantification. No model code / config / network / registry / T_v2 change in the repository. Scratch copies outside the "
                     "repository: /home/jin/v4i2 (i1code: I1 rebuild code with path / coke edits; chain: m08b + s3_0 with env-gated patches, byte-identical "
                     "without the variables; results: one JSON per case; g5: G5 peak script inputs). SDMX: W12 responses, not re-downloaded."),
               rule_differences=IT.RULE_DIFFERENCES,
               status_counts=dict(Counter(e["status"] for e in entries)), grade_counts=dict(Counter(e["grade"] for e in entries)),
               items=items, n_entries=len(entries), entries=entries, files=files)
    cm.write_json(out, cm.I2 / "EVIDENCE.json")
    print(len(entries), "entries;", out["status_counts"], out["grade_counts"], len(files), "files")


if __name__ == "__main__":
    main()
