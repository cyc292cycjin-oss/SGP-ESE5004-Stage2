"""X1b: what the APG LA-TH 955 MW consists of; the 9 lines in the network; every local trace of the figure. Read-only."""
import json, logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 240, "display.max_columns", 60, "display.max_rows", 100, "display.max_colwidth", 80)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); C = M / "research_inputs/corridors"
print(sorted(p.name for p in C.iterdir()))
a = pd.read_csv(C / "CORRIDOR_APG_CROSSCHECK_2024.csv"); print(a.to_string()[:2600])
n = pypsa.Network(M / "results_project/v3/builds/no_new_xb/no_new_xb_365_24h_unsolved.nc")
l = n.lines; b = n.buses.country
x = l[(l.bus0.map(b).isin(["LA", "TH"])) & (l.bus1.map(b).isin(["LA", "TH"])) & (l.bus0.map(b) != l.bus1.map(b))]
cols = [c for c in ("bus0", "bus1", "s_nom", "s_max_pu", "v_nom", "length", "num_parallel", "type", "x", "r", "stock", "source", "border_class", "s_nom_extendable", "name_source", "osm_id") if c in l]
print(x[cols].to_string())
print([c for c in l.columns][:50])
print("sum", x.s_nom.sum())
L = n.links; y = L[(L.bus0.map(b).isin(["LA"])) & (L.bus1.map(b).isin(["TH", "VN"])) & (L.carrier.astype(str).isin(["DC", "AC"]))]; print(y[["bus0", "bus1", "carrier", "p_nom"]])
