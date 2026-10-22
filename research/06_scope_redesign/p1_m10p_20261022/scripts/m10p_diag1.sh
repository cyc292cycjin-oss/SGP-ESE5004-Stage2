#!/bin/bash
MAIN=/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model
N=$MAIN/results_project/m10p/builds; R=$MAIN/results_project/m08b/builds_s01
/home/jin/miniforge3/envs/pypsa-earth/bin/python - $N $R <<'P'
import json, sys
from pathlib import Path
N, R = Path(sys.argv[1]), Path(sys.argv[2])
def walk(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            out += walk(a.get(k), b.get(k), f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += walk(x, y, f"{path}[{i}]")
    elif a != b:
        out.append((path, str(b)[:150], str(a)[:150]))
    return out
for sc in ("integrated",):
    a = json.loads((N / sc / f"{sc}_BUILD_RECEIPT.json").read_text()); b = json.loads((R / sc / f"{sc}_BUILD_RECEIPT.json").read_text())
    for p, old, new in walk(a, b):
        if p.startswith(".build_seconds"): continue
        print("RECEIPT", p, "| ref:", old, "| new:", new)
    a = json.loads((N / sc / "S1_CARRIER_FRAGMENT_MANIFEST.json").read_text()); b = json.loads((R / sc / "S1_CARRIER_FRAGMENT_MANIFEST.json").read_text())
    for p, old, new in walk(a, b)[:30]:
        print("MANIFEST", p, "| ref:", old, "| new:", new)
P
