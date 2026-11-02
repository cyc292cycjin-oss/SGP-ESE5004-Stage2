import pandas as pd, re
from pathlib import Path
pd.set_option("display.width",230); pd.set_option("display.max_columns",30); pd.set_option("display.max_rows",60); pd.set_option("display.max_colwidth",48)
OUT=Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v3/phase1"); W=Path("/home/jin/wt_v3_20261102")
t=(OUT/"mmc1.pdf.txt").read_text().split("=====PAGE ")
s=t[11]; print(s[s.find("Table S8 below")-200:][:900]); print("---p12"); print(t[12][:3600])
t2=(OUT/"pgaf389_supplementary_data.pdf.txt").read_text().split("=====PAGE ")
s=t2[11]; print("---PNAS p11"); print(s[s.find("The transmission capacity")-260:][:2200])
x=pd.read_csv(W/"research_inputs/corridors/APG_STOCK_CHECK_S4E1.csv"); print(x[["apg_no","connection","apg_existing_mw","model_2025_mw","difference_mw","verdict"]].iloc[12:].to_string())
y=pd.read_csv(W/"research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv"); print(y.columns.tolist()); print(y[["apg_no","connection","apg_existing_mw","apg_ongoing_to_2024_mw","apg_future_mw","apg_total_mw"]].to_string())
