"""V5 X20 revision 2-6 (decision 244; X20_SPEC.md 1.13): GEM approximate coordinates of the five 2050-stock units whose nearest and second nearest
node differ by < 50 km (X10 GEM_APPROX_COORDS.csv). Each unit was checked against public sources (web reading only, X20 B); the table records the
checked coordinate, its basis and the nearest same-country AC node with the rule of the GEM additions (s4a_2_fleet_data.nearest_node on the AC buses
of the electric base, which reproduces FLEET_ADDITIONS_2050.csv byte for byte). The build moves a unit only when the node changes
(s4a_fleet.add_gem_fleet -> v5_layers.gem_node_override, research.demand.v5.gem_coord_fix = verified):
  New Kapar 2,100 MW (MY): no source more precise than GEM (TNB: north of the existing Kapar station) -> GEM kept, node unchanged.
  Thai Binh CCGT 2 x 750 MW (VN): GEM point in Thai Binh city; the site is coastal in Thai Do commune (sources give the commune and the boundaries,
    no coordinate). Every point of the commune area tested (inferred site, Con Den, Tra Ly 2 bridge, the Thai Binh coal centre) has the same nearest
    node as GEM (VN2 6) -> node unchanged, coordinate not used.
  Truong Son wind phase 2 350 MW (LA): GEM 19.001, 103.001 is a placeholder; phase 1 turbines (OSM nodes operator=Truong Son Wind Power Project,
    18.296-18.312 N / 105.121-105.159 E) and "phase 2 in the same area" (Vientiane Times) -> 18.303, 105.139, node LA2 1 -> LA2 3 (moved).
  Upper Yeywa 280 MW (MM): dam at 22.2421, 97.1017 (OSM node 487090340, rccdams, Wikidata Q65205813 within 50 m); GEM = Hsipaw town -> node
    unchanged (MM2 5).
The GEM node of every row must equal the node of the unit in FLEET_ADDITIONS_2050(_V5).csv and FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050.csv
(S4B-1: Truong Son 2 and Upper Yeywa are construction units without a start year) - asserted.

    PYTHONHASHSEED=0 python scripts_project/v5_gem_coord_data.py [--network results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research_inputs/fleet_v5/GEM_COORD_CORRECTIONS_V5.csv"
NET = ROOT / "results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc"
ROWS = [
    ("G100000410705", "New Kapar power plant", "1", "MY", 3.124999, 101.325455, 3.124999, 101.325455, "B",
     "GEM kept: TNB release 'located to the north of the existing Sultan Salahuddin Abdul Aziz Power Station'; OSM way 163052518 (existing station)",
     "https://www.marketscreener.com/quote/stock/TENAGA-NASIONAL-6491357/news/Tenaga-Nasional-TNB-NEW-2-100-MW-KAPAR-POWER-PLANT-FORTIFIES-ENERGY-TRANSITION-AGENDA-42057184/"),
    ("G100000406002", "Thai Binh Combined Cycle power station", "1-1", "VN", 20.447935, 106.356951, 20.447935, 106.356951, "C",
     "GEM kept for the node: site = Thai Do commune, between the coastal road and sea dyke 7 (no coordinate published); every tested point of that area -> same node",
     "https://diendandoanhnghiep.vn/thai-binh-quy-hoach-kho-noi-tiep-nhan-tau-150-000-tan-ngoai-khoi-cua-tra-ly-255455.html"),
    ("G100000410611", "Thai Binh Combined Cycle power station", "1-2", "VN", 20.447935, 106.356951, 20.447935, 106.356951, "C",
     "as unit 1-1", "https://diendandoanhnghiep.vn/thai-binh-quy-hoach-kho-noi-tiep-nhan-tau-150-000-tan-ngoai-khoi-cua-tra-ly-255455.html"),
    ("G100001090630", "Truong Son wind farm", "2", "LA", 19.001, 103.001, 18.303, 105.139, "B",
     "centre of the phase 1 turbines (OSM nodes 13455343457-465, operator=Truong Son Wind Power Project); phase 2 'located in the same area' (Vientiane Times); = Xeuchin 2 (KPL 2025-10-10)",
     "https://www.openstreetmap.org/node/13455343460 ; https://www.vientianetimes.org.la/freefreenews/freecontent_118_Borikhamxay_y25.php ; https://kpl.gov.la/En/detail.aspx?id=94998"),
    ("G100000602599", "Upper Yeywa hydroelectric plant", "", "MM", 22.6243, 97.3011, 22.2421, 97.1017, "A",
     "dam (OSM node 487090340 'Upper Yeywa Dam'; rccdams.co.uk 22.242104 N 97.101898 E; Wikidata Q65205813)",
     "https://www.openstreetmap.org/node/487090340 ; https://rccdams.co.uk/dams/upper-yeywa--kyaukme-/"),
]


def main(argv=None):
    from s4a_2_fleet_data import nearest_node
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, default=NET); a = ap.parse_args(argv)
    ds = xr.open_dataset(a.network)
    b = pd.DataFrame({k: ds[f"buses_{k}"].values for k in ("x", "y", "country", "carrier")}, index=ds["buses_i"].values.astype(str)); ds.close()
    nodes = b[b.carrier.astype(str) == "AC"][["x", "y", "country"]].astype({"x": float, "y": float, "country": str})
    tabs = {s: pd.read_csv(ROOT / f"research_inputs/fleet_v5/{s}.csv", dtype={"gem_unit_id": str}).set_index("gem_unit_id")
            for s in ("FLEET_ADDITIONS_2050", "FLEET_ADDITIONS_2050_V5", "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050")}   # S4A v4 / v5 and S4B-1 (decision 77)
    out = []
    for uid, plant, unit, c, la0, lo0, la1, lo1, grade, basis, src in ROWS:
        n0, d0 = nearest_node(nodes, c, la0, lo0); n1, d1 = nearest_node(nodes, c, la1, lo1)
        for s, t in tabs.items():
            if uid in t.index and t.at[uid, "node"] != n0:
                raise SystemExit(f"{uid}: GEM node {n0} differs from {s}.csv node {t.at[uid, 'node']}")
        src_tab = next((s for s in ("FLEET_ADDITIONS_2050_V5", "FLEET_ADDITIONS_CONSTRUCTION_NO_START_YEAR_2050") if uid in tabs[s].index), None)
        if src_tab is None:
            raise SystemExit(f"{uid}: not in the v5 GEM addition tables")
        out.append(dict(gem_unit_id=uid, plant=plant, unit=unit, country=c, capacity_mw=float(tabs[src_tab].at[uid, "capacity_mw"]), model_class=tabs[src_tab].at[uid, "model_class"],
                        table=src_tab, in_v4_s4a_table=uid in tabs["FLEET_ADDITIONS_2050"].index,
                        gem_lat=la0, gem_lon=lo0, checked_lat=la1, checked_lon=lo1, gem_node=n0, gem_node_km=round(d0, 3), checked_node=n1, checked_node_km=round(d1, 3),
                        node_changes=n0 != n1, grade=grade, basis=basis, source=src))
    t = pd.DataFrame(out)
    t.to_csv(OUT, index=False, lineterminator="\n")
    print(t[["gem_unit_id", "plant", "unit", "capacity_mw", "model_class", "table", "gem_node", "checked_node", "checked_node_km", "node_changes"]].to_string(index=False))


if __name__ == "__main__":
    main()
