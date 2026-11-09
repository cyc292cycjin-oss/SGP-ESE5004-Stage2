import pandas as pd, re
D = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109/"
c = pd.read_csv(D + "evidence/REGISTRY_C462_CLASSES.csv", dtype=str, keep_default_na=False)
new = pd.read_csv(D + "cache/DATA_REGISTRY_26c2e47d.csv", dtype=str, keep_default_na=False)
old = pd.read_csv(D + "cache/DATA_REGISTRY_aad8e476.csv", dtype=str, keep_default_na=False)
added = new[~new.param_id.isin(old.param_id)]
txt = (added.description + " " + added.source + " " + added.source_locator).tolist()
for _, r in c[c.cls.isin(["u", "x"])].iterrows():
    p = r.param_id
    hits = [added.param_id.iloc[i] + "(" + added.status.iloc[i] + "/" + added.tier.iloc[i] + ")" for i, t in enumerate(txt) if re.search(r"\b" + re.escape(p) + r"\b", t)]
    if hits:
        print(p, r.cls, "<-", hits)
# rule-name mentions
for key in ["offwind_alpha", "transport_ice", "PHS_per_country", "replanting", "gas_production", "fugitive", "share_MWh_MeOH_per_MWh_e"]:
    m = c[c.param_id.str.contains(key, case=False)]
    print(key, m[["param_id", "cls"]].values.tolist()[:6])
