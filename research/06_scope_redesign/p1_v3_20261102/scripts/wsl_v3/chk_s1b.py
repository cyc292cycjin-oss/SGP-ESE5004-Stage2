import logging, sys
from pathlib import Path
W = Path("/home/jin/wt_v3_20261102"); sys.path.insert(0, str(W / "scripts_project"))
import pypsa
from phase4_static import config
logging.disable(logging.WARNING)
for s in ("integrated", "disconnected"):
    n = pypsa.Network(str(W / f"results_project/s1/{s}/{s}_2920_3h_unsolved.nc"))
    c = config(W, s)["research"]["cross_border"]
    print(s, "meta", n.meta.get("research_cross_border"))
    print(s, "cfg", c)
