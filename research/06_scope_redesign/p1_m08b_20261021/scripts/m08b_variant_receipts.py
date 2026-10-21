"""M08b 3.2: compare the run1 / run2 variant receipts field by field and tabulate input / output SHA256 (read-only, writes the evidence CSV / JSON)."""
import json
from pathlib import Path

import pandas as pd

V = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/m08b/variants")
EV = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence")


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{p}.{k}" if p else k))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flat(v, f"{p}[{i}]"))
    else:
        out[p] = d
    return out


rows, diffs = [], {}
for r1 in sorted((V / "run1").glob("*/*_VARIANT_RECEIPT.json")):
    r2 = V / "run2" / r1.parent.name / r1.name
    a, b = json.loads(r1.read_text()), json.loads(r2.read_text())
    fa, fb = flat(a), flat(b)
    d = sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k))
    diffs[r1.parent.name] = {k: [fa.get(k), fb.get(k)] for k in d}
    sh = {k: v for k, v in fa.items() if "sha256" in k.lower()}
    rows.append(dict(variant=r1.parent.name, receipt=r1.name, differing_fields=";".join(d), **{k: v for k, v in sh.items()}))
df = pd.DataFrame(rows)
df.to_csv(EV / "M08B_VARIANT_RECEIPTS.csv", index=False)
(EV / "M08B_VARIANT_RECEIPT_DIFFS.json").write_text(json.dumps(diffs, indent=1, default=str))
for v, d in diffs.items():
    print(v, "differing fields:", list(d)[:8])
print(df.columns.tolist())
