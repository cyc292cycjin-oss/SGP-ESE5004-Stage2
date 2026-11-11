"""X20 ②6：核对后的坐标 -> 同国最近 AC 节点（大圆距离，同 s4a_2_fleet_data.nearest_node）。只读 W14 网络的 buses（xarray）。"""
import math
import xarray as xr
import pandas as pd

NC = "/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model/results_project/v4w14/builds/main/integrated/integrated_2920_3h_unsolved.nc"
ds = xr.open_dataset(NC)
b = pd.DataFrame({k: ds[f"buses_{k}"].values for k in ("x", "y", "country", "carrier")}, index=ds["buses_i"].values.astype(str))
ds.close()
b = b[(b.carrier.astype(str) == "AC") & ~b.index.str.contains("dedicated|EV|low voltage", regex=True)]


def hav(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


cases = [("New Kapar (GEM, kept)", "MY", 3.124999, 101.325455), ("Thai Binh CCGT (GEM)", "VN", 20.447935, 106.356951),
         ("Thai Binh CCGT (inferred site)", "VN", 20.483, 106.590), ("Thai Binh: Con Den node (OSM 5507106741)", "VN", 20.4862, 106.6037),
         ("Thai Binh: Tra Ly 2 bridge (OSM)", "VN", 20.4765, 106.5768), ("Thai Binh coal power centre (GEM exact)", "VN", 20.481, 106.560),
         ("Truong Son 2 (GEM placeholder)", "LA", 19.001, 103.001), ("Truong Son turbines (OSM, phase 1)", "LA", 18.303, 105.139),
         ("Truong Son office (Hobo Maps)", "LA", 18.313861, 105.102083), ("Upper Yeywa (GEM)", "MM", 22.6243, 97.3011), ("Upper Yeywa dam (OSM 487090340)", "MM", 22.2421, 97.1017)]
for name, c, la, lo in cases:
    d = sorted((hav(la, lo, float(r.y), float(r.x)), i) for i, r in b[b.country.astype(str) == c].iterrows())
    print(f"{name:45s} {c} nearest {d[0][1]:>18s} {d[0][0]:7.1f} km | second {d[1][1]:>18s} {d[1][0]:7.1f} km")
