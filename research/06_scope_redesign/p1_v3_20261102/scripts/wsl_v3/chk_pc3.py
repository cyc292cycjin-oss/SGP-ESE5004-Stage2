"""Path check 3 read-out: only whether the chain handles the plant lines (ledger closure, Owen, G2 of the bridge network). 8 snapshots: no economic reading."""
import json
from pathlib import Path
import pandas as pd
R = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/path_check3")
for r in ("integrated", "no_new_xb", "bridge_160_162"):
    d = R / r; g = json.loads((d / "V5_GATES.json").read_text()); v = json.loads((d / "V6_ACCEPTANCE.json").read_text()); p = json.loads((d / "PRECISION.json").read_text()); o = json.loads((d / "m12_owen/OWEN.json").read_text())
    print(r, "B16", (p.get("c_prices") or {}).get("b16"), "B13", (g.get("B13") or {}).get("passed"), "B5", (g.get("B5") or {}).get("passed"), "B12", (g.get("B12") or {}).get("passed"), "owen usable", o.get("usable_for_allocation"), "label", v.get("label"))
    print("  G2", {k: (v["G2"].get(k) or {}).get("passed") for k in ("G2_1", "G2_2", "G2_3")}, "owen unresolved", o.get("unresolved") or (o.get("classes") or {}).get("unresolved"))
    f = pd.read_csv(d / "cross_border_flows.csv"); print("  flows cols", list(f.columns)[:8], len(f)); x = f[f.astype(str).apply(lambda s: s.str.contains("dedicated").any(), axis=1)]; print("  dedicated rows", len(x)); print(x.head(3).to_string()[:400])
    a = pd.read_csv(d / "ALLOCATION_LINES.csv"); y = a[a.astype(str).apply(lambda s: s.str.contains("dedicated").any(), axis=1)]; print("  allocation rows", len(y), list(a.columns)[:10])
print((R / "ID_LEDGER_DECOMPOSITION.csv").read_text()[:300]); print((R / "LA_EXPORT_UTILISATION.csv").read_text()[:900])
