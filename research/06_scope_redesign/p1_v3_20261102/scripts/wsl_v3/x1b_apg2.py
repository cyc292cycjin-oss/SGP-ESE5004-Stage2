"""X1b: the APG row of LA-TH and LA-VN with all notes, the stock check table, how the source is cited. Read-only."""
from pathlib import Path
import pandas as pd
M = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); C = M / "research_inputs/corridors"
a = pd.read_csv(C / "CORRIDOR_APG_CROSSCHECK_2024.csv"); print(list(a.columns))
for _, r in a[a.country_pair.astype(str).str.contains("LA")].iterrows():
    print({k: v for k, v in r.items() if pd.notna(v)})
c = pd.read_csv(C / "APG_STOCK_CHECK_S4E1.csv"); print(list(c.columns))
for _, r in c[c.astype(str).apply(lambda s: s.str.contains("LA").any(), axis=1)].head(8).iterrows():
    print({k: v for k, v in r.items() if pd.notna(v)})
