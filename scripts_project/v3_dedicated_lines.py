"""V3 X1b (decisions 172, 173; review 2026-11-03 section 2.1): plant-dedicated export lines of the Lao IPPs, table research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv.

    PYTHONHASHSEED=0 python scripts_project/v3_dedicated_lines.py --network <built integrated network with existing_unit_components>

LA-TH: EPPO "Power purchased from Laos PDR" (page of 29 March 2016, archived snapshot 2026-06-11, read by eye from the page image), contract capacity. LA-VN: GEM Xekaman 1 and 3 (decision 100).
A project counts when its GEM units are operating in GIPT 2026-09 and sit in the existing fleet of the network at a Lao node. The line lands on the node of the other country nearest to the plant node.
Nothing is solved; the network file is read only for the existing units and the node coordinates.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import netCDF4 as nc
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts_project"))
from v3_layers import DEDICATED_LENGTH_FACTOR, great_circle_km   # noqa: E402

OUT = ROOT / "research_inputs/corridors/DEDICATED_PLANT_LINES_V3.csv"
OUT_ACE = ROOT / "research_inputs/corridors/APG_LA_TH_LINES_ACE2024.csv"
ACE_SHA_FILE = "ACE2024_APG_Interconnections_Project_Profiles.pdf (raw8), no. 9 Thailand - Lao PDR, profile p.21-23"
# every line of the profile is 115 kV HVAC with the agreement type Energy Exchange: the 955 MW of APG Table 1 are these seven lines, the 5,934.9 MW of generation-to-grid interconnections stand apart
ACE_LINES = [("Tha Li - Ken Thao", 100.0, 2020), ("Nong Khai - Dongphosy", 100.0, 2007), ("Nong Khai - Thanalaeng", 100.0, 1968), ("Bueng Kan - Pakxan", 100.0, 2002), ("Nakhon Phanom - Thakhek", 180.0, 2010),
             ("Mukdahan 2 - Pak Bo", 100.0, 1996), ("Sirindhorn 2 - Bang Yo", 275.0, 2020)]
GIPT = ROOT / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv"
EPPO_SHA = "680ed5756fafcc82692c182cb774c0fa0c0a40a4ab38cb8ad431bfb041f2c25a"
# project, EPPO section (2016), EPPO beginning date / COD, contract MW, other country, GEM unit ids
PROJECTS = [("Theun-Hinboun", "1 COD", "1998-03", 220.0, "TH", ["G100000602431"]),
            ("Houayho", "1 COD", "1999-09", 126.0, "TH", ["G100000602391"]),
            ("Nam Theun 2", "1 COD", "2010-04", 948.0, "TH", ["G100000602426"]),
            ("Nam Ngum 2", "1 COD", "2011-03", 597.0, "TH", ["G100000602408"]),
            ("Expanded Theun-Hinboun", "1 COD", "2012-12", 220.0, "TH", ["G100000602431"]),
            ("Hongsa Lignite", "2 signed PPA, under construction", "2015-06 / 2015-11 / 2016-03", 1473.0, "TH", ["G100000103946", "G100000103947", "G100000103948"]),
            ("Xayaburi", "2 signed PPA, under construction", "2019-10", 1220.0, "TH", ["G100000602432"]),
            ("Xe Pian - Xe Namnoy", "2 signed PPA, under construction", "2019-01", 354.0, "TH", ["G100000602433"]),
            ("Nam Ngiep 1", "3 signed MOU", "2019-01", 269.0, "TH", ["G100000602405"]),
            ("Xekaman 1", "", "", 322.0, "VN", ["G100000602434"]),
            ("Xekaman 3", "", "", 250.0, "VN", ["G100000602436"])]


def nearest(x0: float, y0: float, nodes: pd.DataFrame) -> tuple[str, float]:
    d = {k: great_circle_km(x0, y0, float(z.x), float(z.y)) for k, z in nodes.iterrows()}
    k = min(sorted(d), key=d.get)
    return k, d[k]


def main():
    p = argparse.ArgumentParser(); p.add_argument("--network", type=Path, required=True); a = p.parse_args()
    with nc.Dataset(a.network) as d:
        units = json.loads(d.getncattr("meta"))["existing_unit_components"]
        bx = pd.Series(np.asarray(d["buses_i"][:]).astype(str)); x = np.asarray(d["buses_x"][:]); y = np.asarray(d["buses_y"][:]); cc = np.asarray(d["buses_country"][:]).astype(str); car = np.asarray(d["buses_carrier"][:]).astype(str)
    b = pd.DataFrame(dict(x=x, y=y, country=cc, carrier=car), index=bx.values); ac = b[b.carrier == "AC"]
    g = pd.read_csv(GIPT, low_memory=False).set_index("GEM unit/phase ID"); rows = []
    for name, sec, cod, mw, other, ids in PROJECTS:
        ok = all(i in g.index and str(g.at[i, "Status"]) == "operating" for i in ids) and all(f"GEM:{i}" in units for i in ids)
        nodes = sorted({units[f"GEM:{i}"]["node"] for i in ids if f"GEM:{i}" in units})
        if len(nodes) != 1 or not nodes[0].startswith("LA"):
            raise ValueError(f"{name}: units are not at one Lao node: {nodes}")
        z = ac.loc[nodes[0]]; land, km = nearest(float(z.x), float(z.y), ac[ac.country == other])
        rows.append(dict(project=name, source=("EPPO Power purchased from Laos PDR" if other == "TH" else "GEM GIPT 2026-09 (decision 100)"), eppo_section=sec, eppo_cod=cod, contract_mw=mw, other_country=other, gem_unit_ids=";".join(ids),
                         gem_plant=str(g.at[ids[0], "Plant / Project name"]), gem_status=str(g.at[ids[0], "Status"]), gem_start_year=";".join(str(int(g.at[i, "Start year"])) for i in ids), gem_capacity_mw=float(sum(g.at[i, "Capacity (MW)"] for i in ids)),
                         network_component=units[f"GEM:{ids[0]}"]["component"], network_fleet_mw=float(sum(units[f"GEM:{i}"]["capacity_mw"] for i in ids)), plant_node=nodes[0], landing_node=land, great_circle_km=round(km, 3), line_km=round(km * DEDICATED_LENGTH_FACTOR, 3), counted=bool(ok)))
    t = pd.DataFrame(rows); t.to_csv(OUT, index=False, float_format="%.10g")
    pd.DataFrame([dict(line=k, voltage_kv=115, agreement="Energy Exchange", line_capacity_mw=m, cod=y, source=ACE_SHA_FILE) for k, m, y in ACE_LINES]).to_csv(OUT_ACE, index=False)
    print(t[["project", "contract_mw", "gem_status", "gem_start_year", "gem_capacity_mw", "network_fleet_mw", "plant_node", "landing_node", "line_km", "counted"]].to_string(index=False))
    print(t[t.counted].groupby(["plant_node", "landing_node"]).contract_mw.sum().to_string()); print(t[t.counted].groupby("other_country").contract_mw.sum().to_dict())


if __name__ == "__main__":
    main()
