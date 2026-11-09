import pandas as pd, re
D = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/cache/"
old = pd.read_csv(D + "DATA_REGISTRY_aad8e476.csv", dtype=str, keep_default_na=False).set_index("param_id")
new = pd.read_csv(D + "DATA_REGISTRY_26c2e47d.csv", dtype=str, keep_default_na=False).set_index("param_id")
add = new.loc[sorted(set(new.index) - set(old.index))]
print(add.groupby(["tier", "status"]).size().to_string())
for p, r in add.iterrows():
    print(f"{p} | {r.tier} | {r.status} | {r.value[:30]} {r.unit[:20]} | {r.decision_ref} | {r.description[:230]}")
