"""V3 supplement 02: what separates the three steps of the revision bridge (365x24h, integrated). v3 against bridge 160-164: EV layer only. Bridge 160-164 against bridge 160-162: industry and process tables only. Read-only."""
import logging, sys
from pathlib import Path
import pandas as pd, pypsa
sys.path.insert(0, "/home/jin/wt_v3_20261102/scripts_project")
from v3_static import struct_diff
logging.disable(logging.WARNING)
o, e = Path(sys.argv[1]), Path(sys.argv[2])
f = lambda d: pypsa.Network(str(o / d / "integrated_365_24h_unsolved.nc"))
A, B, C = f("integrated"), f("bridge_160_164"), f("bridge_160_162")
rows = []
for lab, x, y in (("v3 vs bridge_160_164", B, A), ("bridge_160_164 vs bridge_160_162", C, B)):
    t, _ = struct_diff(x, y, "a", "b"); t.insert(0, "step", lab); rows.append(t)
    print(lab, len(t)); print(t.groupby(["type", "change"]).size().to_string()); print(sorted(set(t.carrier))[:40])
pd.concat(rows).to_csv(e / "BRIDGE_DIFF_V3.csv", index=False)
for k, n in (("integrated", A), ("bridge_160_164", B), ("bridge_160_162", C)):
    w = n.snapshot_weightings.generators; p = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum() / 1e6; led = n.meta.get("research_dedicated_lines", {})
    print(k, "load TWh", round(float(p.sum()), 3), "overrides", n.meta["research_config"].get("config_overrides"), "dedicated", led.get("links"), led.get("total_mw"), "EV stores", int((n.stores.carrier == "EV battery").sum()))
