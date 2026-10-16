"""S4B-4 registry fragment (decision 76): typhoon exposure, premium switch, and the deferred offshore items (ship density, protected areas).

    python scripts_project/s4b_4_data.py
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256

SCRIPT = "scripts_project/s4b_4_data.py"
RV = ROOT / "research_inputs/renewable_v5"
WP_SHA = "28fe39b4cc8c1dc020c99569efba9768ddf6df2986422471bee171a042a45244"; NI_SHA = "b30984b56c428391eff17a44d1a9662e444fc4ba419417e9613c18db07424155"
SHIP_SHA = "7d103de52acf355ffc2436909d5d98e9db93f74d6ad237680e5da6d6d24a9248"
NATURA_SHA = "99388fa350cb514caaca9fa10f0d36ef1e0c63f5462ae0ac8c6e9882744bd88e"


def main():
    ev = json.loads((RV / "TYPHOON_EXPOSURE_S4B4.json").read_text()); N = pd.read_csv(RV / "TYPHOON_EXPOSURE_BY_NODE.csv")
    t_sha = sha256(RV / "TYPHOON_EXPOSURE_BY_NODE.csv"); reg = Registry(SCRIPT)
    reg.add("typhoon_frequency_method", f"Per 0.3 deg cell: storms per 10 years whose centre passed within 100 km with sustained wind >= 50 m/s (97.19 kt, 1-min; USA_WIND, else WMO_WIND / 0.93), IBTrACS v04r01 WP + NI 1980-2024, "
            f"tracks interpolated to 30 min; {ev['storms_counted']} storms counted; maximum {ev['freq_max']:.1f} per decade (northern Philippines)", ev["storms_counted"], "storms", "B",
            "IBTrACS v04r01 (Knapp et al. 2010), NOAA NCEI", "ibtracs.WP.list.v04r01.csv / ibtracs.NI.list.v04r01.csv", f"WP:{WP_SHA}|NI:{NI_SHA}", decision_ref="76")
    reg.add("typhoon_node_flag_rule", "A node-technology (onwind on the onshore region, offwind-ac/dc on the offshore region) is exposed when >= 50 % of its wind potential (author layout potential per cell) lies in cells "
            "with >= threshold passages per 10 years; threshold 1 (default), 0.5 / 2 sensitivity", 1.0, "passages per 10 years", "C", "S4B instruction S4B-4 items 1-2", "TYPHOON_EXPOSURE_BY_NODE.csv", t_sha,
            sensitivity_low=0.5, sensitivity_high=2.0, decision_ref="76")
    for th in ["0.5", "1", "2"]:
        f = N[N[f"flag_ge_{th}"]]
        reg.add(f"typhoon_flagged_nodes_ge_{th.replace('.', 'p')}", f"Exposed node-technologies at >= {th} per 10 years: " + "; ".join(f"{r.tech} {r.node} ({r.potential_mw / 1e3:,.1f} GW)" for r in f.itertuples()),
                int(len(f)), "node-technologies", "B", "IBTrACS exposure (scripts_project/s4b_4_typhoon.py)", "TYPHOON_EXPOSURE_BY_NODE.csv", t_sha, decision_ref="76", status="REFERENCE_ONLY")
    reg.add("typhoon_premium_switch", "research.renewable.typhoon_premium = off (main) | on: onshore and offshore wind candidates at exposed nodes get capital cost x 1.25 (Tarp-Johansen & Clausen 2006, DTU / EC-ASEAN Energy Facility, "
            "+20-30 % for typhoon-class design); implemented only, not run", 25.0, "% capital cost", "C", "Tarp-Johansen N.J., Clausen N.-E. (2006) Design of wind turbines in typhoon area (S4A-1 section 1.5)",
            "configs/research/baseline.yaml research.renewable.typhoon_premium_pct", t_sha, sensitivity_low=15.0, sensitivity_high=35.0, decision_ref="76", status="SENSITIVITY")
    reg.add("offshore_shipdensity_raw12_verified", "raw12/shipdensity_global.zip (534,907,276 B) SHA256 matches SHA256SUMS_raw12.txt; not unzipped (13.1 GB inside: tif 9.82 GB + ovr 3.29 GB); to be cut to the ASEAN window "
            "with GDAL /vsizip/ when the shipping-lane exclusion is run (after the first cloud trial, decision 76)", 534907276, "bytes", "A", "World Bank (2021) Global Shipping Traffic Density, dataset 0037580, CC BY 4.0",
            "work/p2_data_intake/raw12/shipdensity_global.zip", SHIP_SHA, decision_ref="76", status="REFERENCE_ONLY")
    reg.add("protected_areas_local_natura", "Local protected-area raster used by the author chain: pypsa-asean/data/natura/natura.tiff (3,356,668 B, global 2.5 arc-min, float32) from 'Protected areas (WDPA)', "
            "Harvard Dataverse doi:10.7910/DVN/XIV9BL V1.3 (2022-01-27, CC0); a full-resolution WDPA release is not on the machine (October 2026: WDPA_Oct2026_Public_shp.zip 4,682,783,045 B, "
            "WDPA_Oct2026_Public.zip (gdb) 2,002,587,756 B per HTTP HEAD 2026-10-16; not downloaded, > 2 GB -> user decision)", 3356668, "bytes", "B",
            "Sosa Arango (2020) Protected areas (WDPA), Harvard Dataverse", "pypsa-asean/data/natura/natura.tiff", NATURA_SHA, decision_ref="76", status="REFERENCE_ONLY")
    reg.add("offshore_deferred_items_s4b4", "Deferred to after the first cloud trial (decision 76): floating offshore wind, shipping-lane exclusion, PyPSA-Eur installation densities and the 60 m depth limit", None, "flag", "B",
            "S4B instruction S4B-4 item 4", "-", t_sha, decision_ref="76", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4b_4.csv")
    print(len(reg.rows), "rows")


if __name__ == "__main__":
    main()
