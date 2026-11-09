import pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); pd.set_option('display.max_columns', 30)
C = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107/cache/"
for lab, key in (("F1", "7508ec72ddce9a9d_v1"), ("F2", "4cc51892d748805f_v1")):
    b = pd.read_csv(C + key + "/buses.csv", index_col=0)
    k = pd.read_csv(C + key + "/links.csv", index_col=0, low_memory=False)
    ctry = b.country.astype(str)
    k["c0"] = k.bus0.astype(str).map(ctry); k["c1"] = k.bus1.astype(str).map(ctry)
    tr = k[k.carrier.isin(["CO2 pipeline", "CO2 ship", "CO2 transit ship", "CO2 transit rail"])]
    x = tr[((tr.c0 == "KH") | (tr.c1 == "KH")) & (tr.c0 != tr.c1)].copy()
    x["cost_per_t_full_use"] = x.capital_cost / 8760.0 + x.marginal_cost
    print("=====", lab)
    print(x[["carrier", "bus0", "bus1", "c0", "c1", "length", "capital_cost", "marginal_cost", "cost_per_t_full_use", "p_nom_opt", "flow0", "ext"]].sort_values(["carrier", "c0", "c1", "cost_per_t_full_use"]).to_string())
    # VN / other exports by route, for comparison
    y = tr[(tr.c0 == "VN") & (tr.c1 != "VN") & (tr.flow0.abs() > 1e3)]
    print(y[["carrier", "bus0", "bus1", "marginal_cost", "capital_cost", "p_nom_opt", "flow0"]].to_string())
    y = tr[(tr.carrier == "CO2 ship") & (tr.flow0 > 1e3)]
    print(y[["bus0", "bus1", "c0", "c1", "marginal_cost", "flow0"]].to_string())
