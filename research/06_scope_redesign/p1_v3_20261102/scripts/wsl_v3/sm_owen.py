"""Owen benefit, freight and ledger items of the v3 smoke; sizes of the small result files. Read-only."""
import json
from pathlib import Path
import pandas as pd
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project")
R = M / "v3/smoke_r2"; B = R / "M12_BENEFIT"
print(sorted(p.name for p in B.iterdir()))
f = next(p for p in B.iterdir() if p.suffix == ".json")
b = json.loads(f.read_text())
print(list(b)[:30])
print("b6", b.get("b6_eur"), "main", b.get("main_form"), "usable", (b.get("owen") or {}).get("usable"), "bunker player", b.get("bunker_player_present"))
o = b.get("owen") or {}
pI, pD = o.get("allocation_integrated_eur") or {}, o.get("allocation_disconnected_eur") or {}
print("owen", {k: (round(pI[k] / 1e9, 3), round(pD[k] / 1e9, 3), round((pD[k] - pI[k]) / 1e9, 3)) for k in pI})
print("bunker", json.dumps(b.get("bunker") or b.get("bunker_benefit") or {}, default=str)[:600])
for sc in ("integrated", "no_new_xb"):
    l = pd.read_csv(R / sc / "COUNTRY_COST_LEDGER.csv", index_col=0)
    cols = [c for c in l.columns if c.startswith("liquid") or "freight" in c]
    print(sc, {c: round(float(l[c].sum()) / 1e9, 4) for c in cols})
    print("  ", sorted((str(p.name), p.stat().st_size) for p in (R / sc).iterdir() if p.is_file() and p.suffix == ".json")[:14])
    o2 = json.loads((R / sc / "m12_owen/OWEN.json").read_text()); print("  owen keys", list(o2)[:12])
s = R / "STATUS.txt"
