import pandas as pd
p = pd.read_csv("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m080_20261020/REGISTRY_ROWS_PROPOSED_v2.csv", dtype=str, keep_default_na=False)
print(len(p), p.columns.tolist())
print(p.action.value_counts().to_dict(), p.status.value_counts().to_dict())
r = pd.read_csv("/home/jin/wt_m08a_20261021/research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
for _, x in p.iterrows():
    have = x.param_id in r.index
    print(("OK " if have else "-- ") + x.param_id.ljust(46), x.action.ljust(7), (r.at[x.param_id, "status"] if have else "").ljust(15), x.decision_ref.ljust(9), x.supersedes[:40].ljust(40), x.m08_write_note[:60])
