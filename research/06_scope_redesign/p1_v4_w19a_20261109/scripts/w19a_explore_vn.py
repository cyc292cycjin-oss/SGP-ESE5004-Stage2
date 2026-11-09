import pandas as pd
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); pd.set_option('display.max_columns', 30)
C = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107/cache/"
for lab, key in (("F1", "7508ec72ddce9a9d_v1"), ("F2", "4cc51892d748805f_v1")):
    b = pd.read_csv(C + key + "/buses.csv", index_col=0)
    k = pd.read_csv(C + key + "/links.csv", index_col=0, low_memory=False)
    ctry = b.country.astype(str)
    k["c0"] = k.bus0.astype(str).map(ctry); k["c1"] = k.bus1.astype(str).map(ctry)
    print("=====", lab)
    dom = k[(k.carrier == "CO2 pipeline") & (k.c0 == "KH") & (k.c1 == "KH")]
    dom = dom.assign(annuity=dom.capital_cost * dom.p_nom_opt)
    print(dom[["bus0", "bus1", "length", "capital_cost", "p_nom_opt", "flow0", "flow0_pos", "annuity"]].to_string())
    print("KH domestic pipeline annuity total", dom.annuity.sum())
    sq = k[(k.carrier == "CO2 sequestration") & (k.c0.isin(["KH", "VN", "TH"]))]
    print(sq[["bus0", "bus1", "p_nom", "p_nom_opt", "ext", "capital_cost", "marginal_cost", "flow0"]].to_string())
    vn = k[(k.c0 == "VN") & (k.carrier.isin(["CO2 ship", "CO2 pipeline"])) & (k.flow0.abs() > 1e3)]
    print(vn[["carrier", "bus0", "bus1", "c1", "marginal_cost", "capital_cost", "p_nom_opt", "flow0"]].to_string())
    vnd = k[(k.carrier == "CO2 pipeline") & (k.c0 == "VN") & (k.c1 == "VN")]
    print("VN domestic pipelines with flow", (vnd.flow0.abs() > 1e3).sum(), "of", len(vnd))
    la = k[(k.c0 == "LA") & (k.carrier.isin(["CO2 ship", "CO2 pipeline", "CO2 transit ship", "CO2 transit rail"])) & (k.flow0.abs() > 1e3)]
    print(la[["carrier", "bus0", "bus1", "c1", "marginal_cost", "capital_cost", "p_nom_opt", "flow0"]].to_string())
