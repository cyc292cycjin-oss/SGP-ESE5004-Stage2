"""X1b: how do the LA existing components of the network map to plants? integration_contract.json and the fleet tables. Read-only."""
import json
from pathlib import Path
import pandas as pd
pd.set_option("display.width", 240, "display.max_columns", 60, "display.max_rows", 300, "display.max_colwidth", 70)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); RI = M / "research_inputs"
c = json.loads((RI / "asset_survival/integration_contract.json").read_text()); print(list(c))
for k, v in c.items():
    print(k, type(v).__name__, (len(v) if hasattr(v, "__len__") else v))
ids = ("G100000602432", "G100000602431", "3c3734e2f61b", "3022facee600", "43a2880b71c0", "88cb7a2a95c2", "9973cb7f1d28", "cc3dfd083c77", "0d66b994afb2", "3b26fcde74e2", "G100001051364")


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, o


hits = {}
for p, v in walk(c):
    s = str(v)
    for i in ids:
        if i in s or i in p:
            hits.setdefault(i, []).append((p[:90], s[:120]))
for i, h in hits.items():
    print("==", i, len(h)); [print("  ", x) for x in h[:5]]
for f in ("FLEET_ADDITIONS_2050.csv", "FLEET_NETWORK_UNITS_NOT_OPERATING_IN_GIPT_2026.csv", "FLEET_REMOVED_NOT_OPERATING_GIPT2026.csv", "FLEET_S1_NOT_INHERITED_ITEM77.csv", "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv", "FLEET_UNRESOLVED_START_YEAR.csv", "FLEET_UNRESOLVED_OPERATING_NO_START_YEAR.csv"):
    d = pd.read_csv(RI / "fleet_v5" / f); cc = [x for x in d.columns if x.lower() in ("country", "node", "bus", "iso")]
    print("--", f, len(d), list(d.columns)[:14])
    mask = pd.Series(False, index=d.index)
    for x in cc:
        mask |= d[x].astype(str).str.startswith("LA") | d[x].astype(str).str.contains("Laos")
    if not cc:
        mask = d.astype(str).apply(lambda r: r.str.contains("LA2|Laos").any(), axis=1)
    print(d[mask].head(40).to_string(index=False)[:3000])
