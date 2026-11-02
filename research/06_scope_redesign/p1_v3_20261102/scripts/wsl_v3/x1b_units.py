"""X1b: which LA plants does the v3 network hold? Read-only. Lists the LA components with capacity, plus the columns that say where a unit comes from."""
import logging
from pathlib import Path
import pandas as pd, pypsa
logging.disable(logging.WARNING)
pd.set_option("display.width", 240, "display.max_columns", 60, "display.max_rows", 300, "display.max_colwidth", 60)
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/builds/integrated")
n = pypsa.Network(M / "integrated_365_24h_unsolved.nc")
b = n.buses
la = b.index[b.index.str.startswith("LA")]
print("LA buses", list(b.index[(b.country == "LA") & b.carrier.isin(["AC", "DC"])]) if "country" in b else list(la)[:30])
print("LA AC coords"); print(b[(b.country == "LA") & (b.carrier == "AC")][["x", "y"]].round(3).to_string())
print("TH AC coords"); print(b[(b.country == "TH") & (b.carrier == "AC")][["x", "y"]].round(3).to_string())
print("VN AC coords"); print(b[(b.country == "VN") & (b.carrier == "AC")][["x", "y"]].round(3).to_string())
for name, df, cap in (("generators", n.generators, "p_nom"), ("storage_units", n.storage_units, "p_nom"), ("links", n.links, "p_nom")):
    key = "bus" if "bus" in df else "bus1"
    x = df[df[key].astype(str).str.startswith("LA")]
    if name == "links":
        x = x[x.carrier.astype(str).isin(["coal", "lignite", "OCGT", "CCGT", "biomass", "oil", "nuclear", "H2 turbine"]) | x.carrier.astype(str).str.contains("existing|hydro", regex=True)]
    print("==", name, len(x), "columns", list(df.columns)[:40] if name == "generators" else "")
    print(x.groupby(x.carrier.astype(str))[cap].agg(["count", "sum", "max"]).round(1).to_string())
    h = x[x.carrier.astype(str).str.contains("hydro|ror|coal|lignite|PHS", regex=True)]
    print(h[[key, "carrier", cap] + [c for c in ("p_nom_extendable", "build_year", "lifetime", "p_nom_min", "research_role") if c in h]].sort_values(cap, ascending=False).head(40).round(2).to_string())
