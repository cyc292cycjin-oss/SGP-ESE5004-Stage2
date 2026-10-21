import pandas as pd, io, subprocess
REG = "research_inputs/registry_v5/DATA_REGISTRY.csv"
old = pd.read_csv(io.BytesIO(subprocess.check_output(["git", "-C", "/home/jin/wt_m08a_20261021", "show", "30d281b8:" + REG])), dtype=str, keep_default_na=False).set_index("param_id")
new = pd.read_csv("/home/jin/wt_m08a_20261021/" + REG, dtype=str, keep_default_na=False).set_index("param_id")
d = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08a_20261021/evidence/M08A_REGISTRY_DIFF.csv", dtype=str, keep_default_na=False)
only = d[d.fields == "source_locator"]
print("only source_locator:", len(only), only.derivation_script.value_counts().to_dict())
for pid in only.param_id.head(4):
    print(pid, "|", old.at[pid, "source_locator"][:150], "=>", new.at[pid, "source_locator"][:150])
print(d[d.fields.str.contains("source_locator") & (d.fields != "source_locator")].param_id.head(5).tolist())
