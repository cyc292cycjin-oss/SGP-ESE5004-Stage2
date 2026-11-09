import pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); pd.set_option('display.max_columns', 30)
C = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107/cache/"
for lab, key in (("F1", "7508ec72ddce9a9d_v1"), ("F2", "4cc51892d748805f_v1")):
    b = pd.read_csv(C + key + "/buses.csv", index_col=0)
    k = pd.read_csv(C + key + "/links.csv", index_col=0, low_memory=False)
    co2b = set(b.index[b.carrier.astype(str).isin(["co2 stored", "co2 sequestered", "co2 sequestered extra-ASEAN"])])
    m = pd.Series(False, index=k.index)
    for j in range(5):
        if f"bus{j}" in k:
            m |= k[f"bus{j}"].astype(str).isin(co2b)
    print("=====", lab)
    print(k[m].carrier.value_counts().to_string())
    if lab == "F1":
        tr = k[m & k.carrier.astype(str).str.contains("transit|ship|pipeline|export|sequestration", case=False)]
        print(tr.groupby("carrier")[["capital_cost", "marginal_cost", "efficiency", "p_nom_opt", "flow0"]].describe().T.to_string()[:3000])
    # node prices for selected countries
    nb = b[(b.carrier.astype(str) == "co2 stored") & b.country.isin(["KH", "TH", "VN", "LA", "MM", "PH", "SG"])]
    print(nb.lam_mean.round(3).to_string())
