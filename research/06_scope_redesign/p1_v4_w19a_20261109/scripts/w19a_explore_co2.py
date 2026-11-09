# W19a exploration: CO2 buses and links touching KH in the D2a extraction caches (read only)
import pandas as pd, sys
C = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2a_20261107/cache/"
for lab, key in (("F1", "7508ec72ddce9a9d_v1"), ("F2", "4cc51892d748805f_v1")):
    b = pd.read_csv(C + key + "/buses.csv", index_col=0)
    k = pd.read_csv(C + key + "/links.csv", index_col=0, low_memory=False)
    s = pd.read_csv(C + key + "/stores.csv", index_col=0)
    print("=====", lab)
    print(b[b.carrier.astype(str).str.contains("co2", case=False)].carrier.value_counts())
    kb = b[(b.country == "KH") & b.carrier.astype(str).str.contains("co2", case=False)]
    print(kb)
    kbs = set(kb.index)
    rows = []
    for j, (bc, ec) in enumerate((("bus0", None), ("bus1", "efficiency"), ("bus2", "efficiency2"), ("bus3", "efficiency3"), ("bus4", "efficiency4"))):
        m = k[bc].astype(str).isin(kbs)
        for name, r in k[m].iterrows():
            eff = -1.0 if ec is None else float(r[ec])
            rows.append(dict(link=name, carrier=r.carrier, port=bc, bus=r[bc], eff=eff, flow0=r.flow0, flow0_pos=r.flow0_pos, co2_into_bus=r.flow0 * eff, p_nom_opt=r.p_nom_opt))
    d = pd.DataFrame(rows)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    g = d.groupby(["carrier", "port"]).agg(n=("link", "size"), co2=("co2_into_bus", "sum"), eff=("eff", "mean")).sort_values("co2")
    print(g[g.co2.abs() > 1e-3])
    print(s[s.index.str.contains("KH") & s.carrier.astype(str).str.contains("co2", case=False)][["carrier", "bus", "e_nom", "e_nom_opt", "ext", "e_end", "capital_cost", "marginal_cost", "lam_bus_mean"]])
