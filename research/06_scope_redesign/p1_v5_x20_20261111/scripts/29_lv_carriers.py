"""X20 ③4：W14 F1 网络中负荷的 carrier（含母线类型）与 bus0 在高压 AC 节点上的链路 carrier（只读，xarray）。"""
import pandas as pd
import xarray as xr

NC = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc"
ds = xr.open_dataset(NC)
def comp(c, attrs):
    return pd.DataFrame({a: ds[f"{c}_{a}"].values.astype(str) for a in attrs if f"{c}_{a}" in ds}, index=ds[f"{c}_i"].values.astype(str))
b = comp("buses", ["carrier", "country", "location"]); L = comp("loads", ["bus", "carrier"]); K = comp("links", ["bus0", "bus1", "carrier"])
ds.close()
ac = set(b.index[(b.carrier == "AC") & ~b.index.str.contains("dedicated|EV|low voltage", regex=True)])
lv = b.index[b.carrier == "low voltage"]
print("AC nodes", len(ac), "LV buses", len(lv), "AC nodes without LV", sorted(x for x in ac if f"{x} low voltage" not in set(lv))[:10])
print("LV location sample", b.loc[lv[:3], "location"].tolist() if "location" in b else "no location column")
L["bus_carrier"] = L.bus.map(b.carrier)
print("\n== loads by carrier and bus carrier"); print(L.groupby(["carrier", "bus_carrier"]).size().to_string())
K["bus0_is_ac_node"] = K.bus0.isin(ac)
print("\n== links with bus0 on an AC node, by carrier"); print(K[K.bus0_is_ac_node].groupby("carrier").size().sort_values(ascending=False).to_string())
