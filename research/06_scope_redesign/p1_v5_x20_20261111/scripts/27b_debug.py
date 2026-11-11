import sys
from pathlib import Path
sys.path.insert(0, "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/x20_src/scripts_project")
import pandas as pd
import v5_ac_dedup_data as m
buses, lines = m.model_tables(Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc"))
print(buses.head(3)); print(buses.carrier.value_counts().head(5)); print(lines.head(3)); print(len(lines), (lines.s_nom_min.astype(float) > 0).sum())
B = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x03_renew_20261111/cache/code/data/osm-plus-prebuilt/0.1.1/all_buses_build_network.csv", index_col=0)
print(B.head(2)); print(B.country.value_counts().head(5))
