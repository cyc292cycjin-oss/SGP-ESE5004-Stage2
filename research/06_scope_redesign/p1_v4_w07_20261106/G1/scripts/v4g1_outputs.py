"""V4 W07 G1 step 10 (Malaysia): A6 outputs for mechanical merging, the missing-data list, the data registry of this session and the merged evidence.

    python scripts/v4g1_outputs.py        (WSL pypsa-earth python; after all other G1 scripts)

* copies the A6 tables from tables/ to the G1 root unchanged (MY_OTHER_SHARE_STEPS, MY_SUBSECTORS_V4, MY_CAPTIVE, MY_BIOMASS_CHECK, MY_NCV, MY_NODE_SHARES);
* writes MY_MISSING_DATA.csv (item, purpose, url_if_known, priority) and MY_DATA_REGISTRY.csv (the SDMX responses: bytes, SHA256, URL, time);
* merges every tables/_*.json evidence list into EVIDENCE.json (key, value, unit, source, status, grade), checks key uniqueness and counts by status.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4g1_common as cm   # noqa: E402

A6 = ["MY_OTHER_SHARE_STEPS.csv", "MY_SUBSECTORS_V4.csv", "MY_CAPTIVE.csv", "MY_BIOMASS_CHECK.csv", "MY_NCV.csv", "MY_NODE_SHARES.csv"]
MISSING = [
    ("Malaysia industrial energy consumption by sub-sector 2019 (Energy Commission / Malaysia Energy Information Hub industrial survey)",
     "MY has no UNSD industry sub-row except NMM coal; needed to split the 'other' bucket (70 % of T_v2) beyond the facility products", "https://meih.st.gov.my", "high"),
     ("Sabah natural gas supply by consumer 2019 (SEDC Energy / PETRONAS Gas; Labuan included)",
     "NEB 2019 Sabah industry gas 29.0 TWh vs 12.1 TWh explained by the Labuan methanol and Sipitang ammonia plants; decides whether 16.9 TWh is NEU / energy sector (sensitivity -21.05 TWh 'other' 2050)", "", "high"),
    ("PETRONAS Chemicals Group annual report 2019 (methanol, ammonia / urea plant output and utilisation)", "replace the stated methanol utilisation 0.85 and the national ammonia utilisation 0.691 by plant output", "https://www.petronaschemicals.com", "high"),
    ("Malaysia primary aluminium production 2019 and 2023 (USGS Minerals Yearbook Malaysia chapter 2019-2022; Press Metal annual reports)",
     "v3 uses 750 kt (USGS 2017-18 Asia-Pacific estimate); capacity 1,080 kt; NEB Sarawak industry electricity 22.1 TWh suggests more", "https://www.usgs.gov/centers/national-minerals-information-center/international-minerals-statistics-and-information", "high"),
    ("Olefins / HVC production by plant 2019-2025 (Lotte Chemical Titan annual reports; PETRONAS Chemicals; PIC Pengerang start-up)", "replace ETSAP 2018 national olefins and the aromatics utilisation 0.85; R4 base for PIC", "", "medium"),
    ("Energy Commission, Performance and Statistical Information on the Electricity Supply Industry in Malaysia 2019 (co-generation and self-generation by industry)",
     "NEB 2019 note 5 source for self-generation; confirms that co-generation fuel for power is in transformation", "https://www.st.gov.my", "medium"),
    ("Cement kiln fuel mix Malaysia 2019 (Cement and Concrete Association of Malaysia; company sustainability reports)", "v3 takes 5.72 TWh kiln fuel from 'other' gas / oil beyond the UNSD NMM coal (1,232.7 kt, Estimate)", "", "medium"),
    ("Clinker trade Malaysia 2019 (UN Comtrade HS 252310)", "explain the implied clinker / cement 0.786 (EDGAR / USGS) against v3 0.656", "https://comtradeplus.un.org", "medium"),
    ("Glass production Malaysia 2019 (float and container; DOSM industrial statistics or company data)", "glass is not in ETSAP for MY and EDGAR 2.A.3 is 1.57 kt CO2; no MY glass sub-sector possible", "https://open.dosm.gov.my", "medium"),
    ("Ferro-alloy and polysilicon output in Samalaju, Sarawak 2019 (company reports)", "Sarawak industry electricity minus aluminium 5.9-10.9 TWh is not explained by an explicit sub-sector", "", "medium"),
    ("PyPSA-Eur industry_sector_ratios HVC methane row: share of natural-gas feedstock (documentation / build script)", "the 2050 HVC vector 6.103 MWh/t vs today energy use 3.269 MWh/t (+24.7 TWh T_v2); boundary check for ethane crackers", "https://github.com/PyPSA/pypsa-eur", "medium"),
    ("MPOB palm oil mill energy statistics (fibre, shell, EFB use)", "closed-loop quantity outside T_v2 (59-86 TWh 2019 by the IRENA mass balance); information only", "https://bepi.mpob.gov.my", "low"),
    ("Sabah Forest Industries pulp line status after 2015", "FAOSTAT carries 131 kt chemical pulp forward from 2015 (A)", "", "low"),
]


def main():
    G1 = cm.G1; T = G1 / "tables"
    for f in A6:
        shutil.copyfile(T / f, G1 / f)
    pd.DataFrame([dict(country=cm.CC, item=a, purpose=b, url_if_known=c, priority=d) for a, b, c, d in MISSING]).to_csv(G1 / "MY_MISSING_DATA.csv", index=False)
    reg = []
    for p in sorted((G1 / "sdmx").glob("*.xml")):
        rc = json.loads((p.parent / (p.name + ".receipt.json")).read_text())
        assert rc["sha256"] == cm.sha256(p) and rc["bytes"] == p.stat().st_size
        reg.append(dict(path=f"G1/sdmx/{p.name}", bytes=rc["bytes"], sha256=rc["sha256"], source="UNSD SDMX DF_UNDATA_ENERGY (public, no login; A5 exception)", url=rc["url"],
                        retrieved_utc=rc["utc"], http_status=rc["http_status"], licence="UN data terms of use (UNdata); same interface as research_inputs/assembly_v1/sources/unsd_targeted/",
                        content="Malaysia energy statistics with CONVERSION_FACTOR per observation"))
    pd.DataFrame(reg).to_csv(G1 / "MY_DATA_REGISTRY.csv", index=False)
    nums, sections = [], []
    for p in sorted(T.glob("_*.json")):
        d = json.loads(p.read_text()); sections.append(dict(file=f"tables/{p.name}", section=d["section"], n=len(d["numbers"])))
        nums += d["numbers"]
    keys = [x["key"] for x in nums]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicated evidence keys")
    cnt = pd.Series([x["status"].split(" ")[0] for x in nums]).value_counts().to_dict()
    cm.jdump(dict(session="V4 W07 G1 (Malaysia)", instruction_sha256="20d03b692f1d32733f34b04d85c01fb3df1345f95f366a6bf25de36ac7ec7baf", n_numbers=len(nums), by_status=cnt,
                  sections=sections, numbers=nums), G1 / "EVIDENCE.json")
    print(len(nums), cnt); print(pd.DataFrame(reg)[["path", "bytes", "sha256"]].to_string())


if __name__ == "__main__":
    main()
